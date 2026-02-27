//! Simple BDD Test Runner for Decibel SDK

use cucumber::World;

#[path = "bdd/mod.rs"]
mod bdd;

use bdd::TestWorld;

#[tokio::main]
async fn main() {
    dotenv::dotenv().ok();
    TestWorld::run("../features/").await;
}
