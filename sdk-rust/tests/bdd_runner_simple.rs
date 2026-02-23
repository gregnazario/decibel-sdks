//! BDD Test Runner for Decibel SDK
//!
//! Entry point for running Cucumber/Gherkin tests against the Rust SDK.

use std::path::Path;

#[tokio::main]
async fn main() {
    // Set up environment for tests
    dotenv::dotenv().ok();

    // Set up tracing for test output
    tracing_subscriber::fmt()
        .with_test_writer()
        .with_env_filter(
            tracing_subscriber::EnvFilter::builder()
                .with_default_directive("decibel_sdk=debug")
                .from_env_lossy()
                .build()
        )
        .init();

    // Run the cucumber tests
    // Features are expected in the `features/` directory
    // Step definitions are registered via cucumber::Steps! macro
    cucumber::TestRunner::<bdd::TestWorld>::new(
        bdd::TestWorld::new(),
        features(),
    )
    .init_tracing()
    .run()
    .await;
}

fn features() -> cucumber::Cucumber<bdd::TestWorld> {
    // The cucumber crate automatically discovers feature files
    // We configure it to look in the features/ directory
    let features_path = Path::new("features");

    cucumber::Cucumber::new()
        .features(&features_path)
        .steps(bdd::steps::all_steps())
}

// Re-export for the cucumber macro
pub mod bdd;
