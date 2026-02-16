use std::sync::Arc;
use std::time::Duration;
use tokio::sync::RwLock;

use crate::config::DecibelConfig;

#[derive(Debug, Clone)]
pub struct GasPriceInfo {
    pub gas_estimate: u64,
    pub timestamp: u64,
}

pub struct GasPriceManager {
    gas_price: Arc<RwLock<Option<GasPriceInfo>>>,
    fullnode_url: String,
    refresh_interval: Duration,
    multiplier: f64,
    http: reqwest::Client,
    task_handle: Arc<tokio::sync::Mutex<Option<tokio::task::JoinHandle<()>>>>,
}

impl GasPriceManager {
    pub fn new(config: &DecibelConfig, multiplier: f64, refresh_interval_ms: u64) -> Self {
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert("Content-Type", "application/json".parse().unwrap());

        Self {
            gas_price: Arc::new(RwLock::new(None)),
            fullnode_url: config.fullnode_url.clone(),
            refresh_interval: Duration::from_millis(refresh_interval_ms),
            multiplier,
            http: reqwest::Client::builder()
                .default_headers(headers)
                .build()
                .unwrap(),
            task_handle: Arc::new(tokio::sync::Mutex::new(None)),
        }
    }

    pub async fn get_gas_price(&self) -> Option<u64> {
        let price = self.gas_price.read().await;
        price.as_ref().map(|p| p.gas_estimate)
    }

    pub async fn initialize(&self) {
        self.fetch_and_set_gas_price().await;

        let gas_price = self.gas_price.clone();
        let url = self.fullnode_url.clone();
        let interval = self.refresh_interval;
        let multiplier = self.multiplier;
        let http = self.http.clone();

        let handle = tokio::spawn(async move {
            let mut ticker = tokio::time::interval(interval);
            loop {
                ticker.tick().await;
                if let Ok(estimate) = fetch_gas_estimate(&http, &url).await {
                    let adjusted = (estimate as f64 * multiplier) as u64;
                    let mut price = gas_price.write().await;
                    *price = Some(GasPriceInfo {
                        gas_estimate: adjusted,
                        timestamp: std::time::SystemTime::now()
                            .duration_since(std::time::UNIX_EPOCH)
                            .unwrap()
                            .as_millis() as u64,
                    });
                }
            }
        });

        let mut task = self.task_handle.lock().await;
        *task = Some(handle);
    }

    async fn fetch_and_set_gas_price(&self) {
        if let Ok(estimate) = fetch_gas_estimate(&self.http, &self.fullnode_url).await {
            let adjusted = (estimate as f64 * self.multiplier) as u64;
            let mut price = self.gas_price.write().await;
            *price = Some(GasPriceInfo {
                gas_estimate: adjusted,
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_millis() as u64,
            });
        }
    }

    pub async fn destroy(&self) {
        let mut task = self.task_handle.lock().await;
        if let Some(handle) = task.take() {
            handle.abort();
        }
    }
}

async fn fetch_gas_estimate(
    http: &reqwest::Client,
    fullnode_url: &str,
) -> std::result::Result<u64, Box<dyn std::error::Error + Send + Sync>> {
    let url = format!("{}/estimate_gas_price", fullnode_url.trim_end_matches('/'));
    let resp = http.get(&url).send().await?;
    let body: serde_json::Value = resp.json().await?;
    let estimate = body
        .get("gas_estimate")
        .and_then(|v| v.as_u64())
        .unwrap_or(100);
    Ok(estimate)
}
