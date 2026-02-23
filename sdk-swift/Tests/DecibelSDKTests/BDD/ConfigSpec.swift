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
                    expect{ try DecibelReadClient(config: world.config, apiKey: nil) }.notTo(throwError())
                }

                it("configures for mainnet environment") {
                    world.config = .mainnet
                    expect(world.config.network).to(equal(.mainnet))
                    expect(world.config.tradingHttpUrl).to(equal("https://api.decibel.trade"))
                }

                it("has correct chain ID") {
                    world.config = .mainnet
                    expect(world.config.chainId).to(equal(1))
                }

                it("has valid deployment addresses") {
                    world.config = .mainnet
                    expect(world.config.deployment.package).toNot(beEmpty())
                }
            }

            context("when using testnet preset") {
                it("creates a valid read client") {
                    world.config = .testnet
                    expect{ try DecibelReadClient(config: world.config, apiKey: nil) }.notTo(throwError())
                }

                it("configures for testnet environment") {
                    world.config = .testnet
                    expect(world.config.network).to(equal(.testnet))
                    expect(world.config.tradingHttpUrl).to(equal("https://api.testnet.decibel.trade"))
                }

                it("has correct chain ID") {
                    world.config = .testnet
                    expect(world.config.chainId).to(equal(2))
                }
            }

            context("when using local preset") {
                it("creates a valid read client") {
                    world.config = .local
                    expect{ try DecibelReadClient(config: world.config, apiKey: nil) }.notTo(throwError())
                }

                it("configures for local environment") {
                    world.config = .local
                    expect(world.config.network).to(equal(.local))
                    expect(world.config.tradingHttpUrl).to(equal("http://localhost:3000"))
                }

                it("has correct chain ID") {
                    world.config = .local
                    expect(world.config.chainId).to(equal(4))
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
                    expect{ world.config?.validate() }.notTo(throwError())
                }

                it("fails validation for missing fullnode URL") {
                    var config = DecibelConfig.testnet
                    config.fullnodeUrl = ""
                    expect{ try config.validate() }.to(throwError())
                }

                it("fails validation for missing trading HTTP URL") {
                    var config = DecibelConfig.testnet
                    config.tradingHttpUrl = ""
                    expect{ try config.validate() }.to(throwError())
                }

                it("fails validation for missing trading WebSocket URL") {
                    var config = DecibelConfig.testnet
                    config.tradingWsUrl = ""
                    expect{ try config.validate() }.to(throwError())
                }
            }
        }
    }
}
