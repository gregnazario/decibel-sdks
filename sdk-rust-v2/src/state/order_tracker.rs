use std::collections::HashMap;
use parking_lot::RwLock;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum OrderState {
    Pending,
    Acknowledged,
    PartiallyFilled,
    Filled,
    Cancelled,
    Expired,
}

impl OrderState {
    fn is_active(self) -> bool {
        matches!(
            self,
            OrderState::Pending | OrderState::Acknowledged | OrderState::PartiallyFilled
        )
    }

    fn is_completed(self) -> bool {
        matches!(
            self,
            OrderState::Filled | OrderState::Cancelled | OrderState::Expired
        )
    }
}

pub struct OrderLifecycleTracker {
    inner: RwLock<OrderTrackerInner>,
}

struct OrderTrackerInner {
    current: HashMap<String, OrderState>,
    history: HashMap<String, Vec<(OrderState, i64)>>,
}

fn now_ms() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}

impl Default for OrderLifecycleTracker {
    fn default() -> Self {
        Self::new()
    }
}

impl OrderLifecycleTracker {
    pub fn new() -> Self {
        Self {
            inner: RwLock::new(OrderTrackerInner {
                current: HashMap::new(),
                history: HashMap::new(),
            }),
        }
    }

    pub fn track(&self, order_id: &str, state: OrderState) {
        let mut inner = self.inner.write();
        let ts = now_ms();
        inner.current.insert(order_id.to_string(), state);
        inner
            .history
            .entry(order_id.to_string())
            .or_default()
            .push((state, ts));
    }

    pub fn update(&self, order_id: &str, new_state: OrderState) -> bool {
        let mut inner = self.inner.write();
        let current = match inner.current.get(order_id) {
            Some(s) => *s,
            None => return false,
        };
        if current == new_state {
            return false;
        }
        inner.current.insert(order_id.to_string(), new_state);
        let ts = now_ms();
        inner
            .history
            .entry(order_id.to_string())
            .or_default()
            .push((new_state, ts));
        true
    }

    pub fn get(&self, order_id: &str) -> Option<OrderState> {
        self.inner.read().current.get(order_id).copied()
    }

    pub fn history(&self, order_id: &str) -> Vec<(OrderState, i64)> {
        self.inner
            .read()
            .history
            .get(order_id)
            .cloned()
            .unwrap_or_default()
    }

    pub fn pending_orders(&self) -> Vec<String> {
        let inner = self.inner.read();
        inner
            .current
            .iter()
            .filter(|(_, s)| **s == OrderState::Pending)
            .map(|(id, _)| id.clone())
            .collect()
    }

    pub fn active_orders(&self) -> Vec<String> {
        let inner = self.inner.read();
        inner
            .current
            .iter()
            .filter(|(_, s)| s.is_active())
            .map(|(id, _)| id.clone())
            .collect()
    }

    pub fn completed_orders(&self) -> Vec<String> {
        let inner = self.inner.read();
        inner
            .current
            .iter()
            .filter(|(_, s)| s.is_completed())
            .map(|(id, _)| id.clone())
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn track_new_order() {
        let tracker = OrderLifecycleTracker::new();
        tracker.track("ord1", OrderState::Pending);
        assert_eq!(tracker.get("ord1"), Some(OrderState::Pending));
    }

    #[test]
    fn update_state() {
        let tracker = OrderLifecycleTracker::new();
        tracker.track("ord1", OrderState::Pending);
        assert!(tracker.update("ord1", OrderState::Acknowledged));
        assert_eq!(tracker.get("ord1"), Some(OrderState::Acknowledged));
    }

    #[test]
    fn update_nonexistent_returns_false() {
        let tracker = OrderLifecycleTracker::new();
        assert!(!tracker.update("missing", OrderState::Filled));
    }

    #[test]
    fn duplicate_state_returns_false() {
        let tracker = OrderLifecycleTracker::new();
        tracker.track("ord1", OrderState::Pending);
        assert!(tracker.update("ord1", OrderState::Acknowledged));
        assert!(!tracker.update("ord1", OrderState::Acknowledged));
        assert_eq!(tracker.get("ord1"), Some(OrderState::Acknowledged));
    }

    #[test]
    fn history_tracking() {
        let tracker = OrderLifecycleTracker::new();
        tracker.track("ord1", OrderState::Pending);
        tracker.update("ord1", OrderState::Acknowledged);
        tracker.update("ord1", OrderState::PartiallyFilled);

        let hist = tracker.history("ord1");
        assert_eq!(hist.len(), 3);
        assert_eq!(hist[0].0, OrderState::Pending);
        assert_eq!(hist[1].0, OrderState::Acknowledged);
        assert_eq!(hist[2].0, OrderState::PartiallyFilled);

        for entry in &hist {
            assert!(entry.1 > 0);
        }
    }

    #[test]
    fn history_empty_for_unknown() {
        let tracker = OrderLifecycleTracker::new();
        assert!(tracker.history("unknown").is_empty());
    }

    #[test]
    fn state_categories() {
        let tracker = OrderLifecycleTracker::new();
        tracker.track("ord1", OrderState::Pending);
        tracker.track("ord2", OrderState::Acknowledged);
        tracker.track("ord3", OrderState::PartiallyFilled);
        tracker.track("ord4", OrderState::Filled);
        tracker.track("ord5", OrderState::Cancelled);
        tracker.track("ord6", OrderState::Expired);

        let mut pending = tracker.pending_orders();
        pending.sort();
        assert_eq!(pending, vec!["ord1"]);

        let mut active = tracker.active_orders();
        active.sort();
        assert_eq!(active, vec!["ord1", "ord2", "ord3"]);

        let mut completed = tracker.completed_orders();
        completed.sort();
        assert_eq!(completed, vec!["ord4", "ord5", "ord6"]);
    }

    #[test]
    fn get_nonexistent_returns_none() {
        let tracker = OrderLifecycleTracker::new();
        assert!(tracker.get("nonexistent").is_none());
    }

    #[test]
    fn send_sync_assertion() {
        fn assert_send_sync<T: Send + Sync>() {}
        assert_send_sync::<OrderLifecycleTracker>();
    }
}
