use rand::Rng;

/// Generate a random `u64` nonce for transaction replay protection.
///
/// Each call produces a cryptographically random value, making collisions
/// negligible even across high-frequency submission loops.
pub fn generate_replay_protection_nonce() -> u64 {
    rand::thread_rng().gen::<u64>()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn returns_u64() {
        let nonce: u64 = generate_replay_protection_nonce();
        // Just verify it's a valid u64 (compiles and doesn't panic).
        let _ = nonce;
    }

    #[test]
    fn consecutive_calls_differ() {
        let a = generate_replay_protection_nonce();
        let b = generate_replay_protection_nonce();
        assert_ne!(a, b, "two consecutive nonces should differ");
    }

    #[test]
    fn hundred_calls_all_unique() {
        let mut seen = HashSet::new();
        for _ in 0..100 {
            let nonce = generate_replay_protection_nonce();
            assert!(
                seen.insert(nonce),
                "duplicate nonce after {} calls",
                seen.len()
            );
        }
        assert_eq!(seen.len(), 100);
    }

    #[test]
    fn nonce_is_not_always_zero() {
        let mut all_zero = true;
        for _ in 0..10 {
            if generate_replay_protection_nonce() != 0 {
                all_zero = false;
                break;
            }
        }
        assert!(!all_zero, "nonce generator should not always produce 0");
    }
}
