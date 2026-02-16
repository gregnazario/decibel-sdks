use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex, RwLock};
use futures_util::{SinkExt, StreamExt};
use tokio_tungstenite::{connect_async, tungstenite::Message};

use crate::config::DecibelConfig;
use crate::error::{DecibelError, Result};
use crate::models::WsSubscribeRequest;

type SubscriptionCallback = Arc<dyn Fn(serde_json::Value) + Send + Sync>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum WsReadyState {
    Connecting,
    Open,
    Closing,
    Closed,
}

pub struct WebSocketManager {
    config: DecibelConfig,
    api_key: Option<String>,
    subscriptions: Arc<RwLock<HashMap<String, Vec<SubscriptionCallback>>>>,
    write_tx: Arc<Mutex<Option<mpsc::Sender<String>>>>,
    state: Arc<RwLock<WsReadyState>>,
    connection_task: Arc<Mutex<Option<tokio::task::JoinHandle<()>>>>,
    on_error: Option<Arc<dyn Fn(String) + Send + Sync>>,
}

impl WebSocketManager {
    pub fn new(
        config: DecibelConfig,
        api_key: Option<String>,
        on_error: Option<Arc<dyn Fn(String) + Send + Sync>>,
    ) -> Self {
        Self {
            config,
            api_key,
            subscriptions: Arc::new(RwLock::new(HashMap::new())),
            write_tx: Arc::new(Mutex::new(None)),
            state: Arc::new(RwLock::new(WsReadyState::Closed)),
            connection_task: Arc::new(Mutex::new(None)),
            on_error,
        }
    }

    pub async fn connect(&self) -> Result<()> {
        let mut state = self.state.write().await;
        if *state == WsReadyState::Open || *state == WsReadyState::Connecting {
            return Ok(());
        }
        *state = WsReadyState::Connecting;
        drop(state);

        let mut ws_url = self.config.trading_ws_url.clone();
        if let Some(ref key) = self.api_key {
            if ws_url.contains('?') {
                ws_url = format!("{}&x-api-key={}", ws_url, key);
            } else {
                ws_url = format!("{}?x-api-key={}", ws_url, key);
            }
        }

        let (ws_stream, _) = connect_async(&ws_url)
            .await
            .map_err(|e| DecibelError::WebSocket(e.to_string()))?;

        let (mut write, mut read) = ws_stream.split();

        let (tx, mut rx) = mpsc::channel::<String>(256);
        {
            let mut write_tx = self.write_tx.lock().await;
            *write_tx = Some(tx);
        }

        {
            let mut state = self.state.write().await;
            *state = WsReadyState::Open;
        }

        let subscriptions = self.subscriptions.clone();
        let state_clone = self.state.clone();
        let on_error = self.on_error.clone();

        let read_task = tokio::spawn(async move {
            while let Some(msg_result) = read.next().await {
                match msg_result {
                    Ok(Message::Text(text)) => {
                        if let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) {
                            if let Some(channel) = value.get("channel").and_then(|c| c.as_str()) {
                                let subs = subscriptions.read().await;
                                if let Some(callbacks) = subs.get(channel) {
                                    let data = value.get("data").cloned().unwrap_or(value.clone());
                                    for cb in callbacks {
                                        cb(data.clone());
                                    }
                                }
                            }
                        }
                    }
                    Ok(Message::Close(_)) => {
                        let mut state = state_clone.write().await;
                        *state = WsReadyState::Closed;
                        break;
                    }
                    Err(e) => {
                        if let Some(ref handler) = on_error {
                            handler(e.to_string());
                        }
                        let mut state = state_clone.write().await;
                        *state = WsReadyState::Closed;
                        break;
                    }
                    _ => {}
                }
            }
        });

        let write_task = tokio::spawn(async move {
            while let Some(msg) = rx.recv().await {
                if write.send(Message::Text(msg.into())).await.is_err() {
                    break;
                }
            }
        });

        let mut task = self.connection_task.lock().await;
        *task = Some(tokio::spawn(async move {
            let _ = tokio::join!(read_task, write_task);
        }));

        Ok(())
    }

    pub async fn subscribe<F>(
        &self,
        topic: &str,
        callback: F,
    ) -> Result<Box<dyn FnOnce() + Send>>
    where
        F: Fn(serde_json::Value) + Send + Sync + 'static,
    {
        self.connect().await?;

        let cb: SubscriptionCallback = Arc::new(callback);
        let is_new_topic;

        {
            let mut subs = self.subscriptions.write().await;
            let entry = subs.entry(topic.to_string()).or_insert_with(Vec::new);
            is_new_topic = entry.is_empty();
            entry.push(cb);
        }

        if is_new_topic {
            let msg = serde_json::to_string(&WsSubscribeRequest::subscribe(topic))
                .map_err(|e| DecibelError::Serialization(e))?;
            self.send_message(&msg).await?;
        }

        let topic_owned = topic.to_string();
        let subscriptions = self.subscriptions.clone();
        let write_tx = self.write_tx.clone();

        Ok(Box::new(move || {
            let rt = tokio::runtime::Handle::try_current();
            if let Ok(handle) = rt {
                let subs = subscriptions.clone();
                let tx = write_tx.clone();
                let topic = topic_owned.clone();
                handle.spawn(async move {
                    let mut subs = subs.write().await;
                    if let Some(callbacks) = subs.get_mut(&topic) {
                        callbacks.pop();
                        if callbacks.is_empty() {
                            subs.remove(&topic);
                            let msg = serde_json::to_string(
                                &WsSubscribeRequest::unsubscribe(&topic),
                            )
                            .ok();
                            if let Some(msg) = msg {
                                let tx = tx.lock().await;
                                if let Some(ref sender) = *tx {
                                    let _ = sender.send(msg).await;
                                }
                            }
                        }
                    }
                });
            }
        }))
    }

    async fn send_message(&self, msg: &str) -> Result<()> {
        let tx = self.write_tx.lock().await;
        if let Some(ref sender) = *tx {
            sender
                .send(msg.to_string())
                .await
                .map_err(|e| DecibelError::WebSocket(format!("Failed to send: {}", e)))?;
        }
        Ok(())
    }

    pub async fn reset(&self, topic: &str) -> Result<()> {
        let unsub = serde_json::to_string(&WsSubscribeRequest::unsubscribe(topic))
            .map_err(|e| DecibelError::Serialization(e))?;
        self.send_message(&unsub).await?;

        let sub = serde_json::to_string(&WsSubscribeRequest::subscribe(topic))
            .map_err(|e| DecibelError::Serialization(e))?;
        self.send_message(&sub).await?;

        Ok(())
    }

    pub async fn ready_state(&self) -> WsReadyState {
        self.state.read().await.clone()
    }

    pub async fn close(&self) {
        {
            let mut state = self.state.write().await;
            *state = WsReadyState::Closing;
        }

        {
            let mut tx = self.write_tx.lock().await;
            *tx = None;
        }

        {
            let mut task = self.connection_task.lock().await;
            if let Some(handle) = task.take() {
                handle.abort();
            }
        }

        {
            let mut subs = self.subscriptions.write().await;
            subs.clear();
        }

        {
            let mut state = self.state.write().await;
            *state = WsReadyState::Closed;
        }
    }
}
