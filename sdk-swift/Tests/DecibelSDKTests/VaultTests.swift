import XCTest
@testable import DecibelSDK

final class VaultTests: XCTestCase {
    let decoder = JSONDecoder()

    func testVault_Deserialization() throws {
        let json = """
        {
            "address": "0xvault", "name": "Alpha", "description": "A vault",
            "manager": "0xmgr", "status": "Active", "created_at": 1700000000000,
            "tvl": 500000.0, "volume": 1000000.0, "volume_30d": null,
            "all_time_pnl": 50000.0, "net_deposits": null,
            "all_time_return": 0.1, "past_month_return": null,
            "sharpe_ratio": null, "max_drawdown": null,
            "weekly_win_rate_12w": null, "profit_share": null,
            "pnl_90d": null, "manager_cash_pct": null,
            "average_leverage": null, "depositors": 42,
            "perp_equity": null, "vault_type": "user",
            "social_links": ["https://x.com"]
        }
        """.data(using: .utf8)!

        let vault = try decoder.decode(Vault.self, from: json)
        XCTAssertEqual(vault.name, "Alpha")
        XCTAssertEqual(vault.depositors, 42)
        XCTAssertEqual(vault.vaultType, .user)
        XCTAssertNil(vault.volume30d)
    }

    func testVault_AllNulls() throws {
        let json = """
        {
            "address": "0x", "name": "V", "description": null,
            "manager": "0xm", "status": "Pending", "created_at": 0,
            "tvl": null, "volume": null, "volume_30d": null,
            "all_time_pnl": null, "net_deposits": null,
            "all_time_return": null, "past_month_return": null,
            "sharpe_ratio": null, "max_drawdown": null,
            "weekly_win_rate_12w": null, "profit_share": null,
            "pnl_90d": null, "manager_cash_pct": null,
            "average_leverage": null, "depositors": null,
            "perp_equity": null, "vault_type": null,
            "social_links": null
        }
        """.data(using: .utf8)!

        let vault = try decoder.decode(Vault.self, from: json)
        XCTAssertNil(vault.description)
        XCTAssertNil(vault.tvl)
        XCTAssertNil(vault.vaultType)
    }

    func testUserOwnedVault_Deserialization() throws {
        let json = """
        {
            "vault_address": "0xv", "vault_name": "My Vault",
            "vault_share_symbol": "MV", "status": "Active",
            "age_days": 30, "num_managers": 2,
            "tvl": 100000.0, "apr": 0.15,
            "manager_equity": null, "manager_stake": null
        }
        """.data(using: .utf8)!

        let vault = try decoder.decode(UserOwnedVault.self, from: json)
        XCTAssertEqual(vault.vaultName, "My Vault")
        XCTAssertEqual(vault.ageDays, 30)
    }

    func testVaultType_Protocol() throws {
        let json = """
        {
            "address": "0x", "name": "P", "description": null,
            "manager": "0xm", "status": "Active", "created_at": 0,
            "tvl": null, "volume": null, "volume_30d": null,
            "all_time_pnl": null, "net_deposits": null,
            "all_time_return": null, "past_month_return": null,
            "sharpe_ratio": null, "max_drawdown": null,
            "weekly_win_rate_12w": null, "profit_share": null,
            "pnl_90d": null, "manager_cash_pct": null,
            "average_leverage": null, "depositors": null,
            "perp_equity": null, "vault_type": "protocol",
            "social_links": null
        }
        """.data(using: .utf8)!

        let vault = try decoder.decode(Vault.self, from: json)
        XCTAssertEqual(vault.vaultType, .protocol)
    }
}
