import Quick
import Nimble
@testable import DecibelSDK

/// BDD-style tests for SDK configuration using Quick/Nimble.
final class ConfigSpec: QuickSpec {
    override class func spec() {
        describe("SDK Configuration") {
            var world: TestWorld!

            beforeEach {
                world = TestWorld()
            }

            afterEach {
                world.clear()
            }

            context("when using mainnet preset") {
                it("creates a valid read client") {
                    world.config = .mainnet
                    expect(DecibelReadClient(config: world.config!, apiKey: nil)).toNot(beNil())
                }

                it("configures for mainnet environment") {
                    world.config = .mainnet
                    expect(world.config!.network).to(equal(.mainnet))
                    expect(world.config!.tradingHTTPURL).to(equal("https://api.decibel.trade"))
                }

                it("has correct chain ID") {
                    world.config = .mainnet
                    expect(world.config!.chainID).to(equal(1))
                }

                it("has valid deployment addresses") {
                    world.config = .mainnet
                    expect(world.config!.deployment.package_addr).toNot(beEmpty())
                }
            }

            context("when using testnet preset") {
                it("creates a valid read client") {
                    world.config = .testnet
                    expect(DecibelReadClient(config: world.config!, apiKey: nil)).toNot(beNil())
                }

                it("configures for testnet environment") {
                    world.config = .testnet
                    expect(world.config!.network).to(equal(.testnet))
                    expect(world.config!.tradingHTTPURL).to(equal("https://api.testnet.decibel.trade"))
                }

                it("has correct chain ID") {
                    world.config = .testnet
                    expect(world.config!.chainID).to(equal(2))
                }
            }

            context("when using local preset") {
                it("creates a valid read client") {
                    world.config = .local
                    expect(DecibelReadClient(config: world.config!, apiKey: nil)).toNot(beNil())
                }

                it("configures for local environment") {
                    world.config = .local
                    expect(world.config!.network).to(equal(.local))
                    expect(world.config!.tradingHTTPURL).to(equal("http://localhost:3000"))
                }

                it("has correct chain ID") {
                    world.config = .local
                    expect(world.config!.chainID).to(equal(4))
                }
            }

            context("when requesting configuration by name") {
                it("returns mainnet configuration when requested") {
                    world.config = .named("mainnet")
                    expect(world.config).toNot(beNil())
                    expect(world.config?.network).to(equal(.mainnet))
                }

                it("returns testnet configuration when requested") {
                    world.config = .named("testnet")
                    expect(world.config).toNot(beNil())
                    expect(world.config?.network).to(equal(.testnet))
                }

                it("returns local configuration when requested") {
                    world.config = .named("local")
                    expect(world.config).toNot(beNil())
                    expect(world.config?.network).to(equal(.local))
                }

                it("returns nil for unknown configuration") {
                    world.config = .named("unknown")
                    expect(world.config).to(beNil())
                }
            }

            context("configuration validation") {
                it("validates correct configuration") {
                    world.config = .testnet
                    expect{ try world.config?.validate() }.notTo(throwError())
                }

                it("fails validation for missing fullnode URL") {
                    let config = DecibelConfig(
                        network: .testnet,
                        fullnodeURL: "",
                        tradingHTTPURL: "https://api.testnet.decibel.trade",
                        tradingWsURL: "wss://api.testnet.decibel.trade/ws",
                        deployment: Deployment(package_addr: "0x1", usdc: "0x2")
                    )
                    expect{ try config.validate() }.to(throwError())
                }

                it("fails validation for missing trading HTTP URL") {
                    let config = DecibelConfig(
                        network: .testnet,
                        fullnodeURL: "https://fullnode.testnet.aptoslabs.com/v1",
                        tradingHTTPURL: "",
                        tradingWsURL: "wss://api.testnet.decibel.trade/ws",
                        deployment: Deployment(package_addr: "0x1", usdc: "0x2")
                    )
                    expect{ try config.validate() }.to(throwError())
                }

                it("fails validation for missing trading WebSocket URL") {
                    let config = DecibelConfig(
                        network: .testnet,
                        fullnodeURL: "https://fullnode.testnet.aptoslabs.com/v1",
                        tradingHTTPURL: "https://api.testnet.decibel.trade",
                        tradingWsURL: "",
                        deployment: Deployment(package_addr: "0x1", usdc: "0x2")
                    )
                    expect{ try config.validate() }.to(throwError())
                }
            }
        }
    }
}
