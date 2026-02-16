import XCTest
@testable import DecibelSDK

final class AccountTests: XCTestCase {
    let decoder = JSONDecoder()

    func testAccountOverview_FullValues() throws {
        let json = """
        {
            "perp_equity_balance": 10000.0,
            "unrealized_pnl": 500.0,
            "unrealized_funding_cost": -10.5,
            "cross_margin_ratio": 0.15,
            "maintenance_margin": 1000.0,
            "cross_account_leverage_ratio": 5.0,
            "volume": 250000.0,
            "net_deposits": 8000.0,
            "all_time_return": 0.25,
            "pnl_90d": 2000.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.1,
            "weekly_win_rate_12w": 0.6,
            "average_cash_position": 5000.0,
            "average_leverage": 3.0,
            "cross_account_position": 7000.0,
            "total_margin": 2000.0,
            "usdc_cross_withdrawable_balance": 3000.0,
            "usdc_isolated_withdrawable_balance": 1000.0,
            "realized_pnl": 1500.0,
            "liquidation_fees_paid": 50.0,
            "liquidation_losses": 200.0
        }
        """.data(using: .utf8)!

        let overview = try decoder.decode(AccountOverview.self, from: json)
        XCTAssertEqual(overview.perpEquityBalance, 10000.0)
        XCTAssertEqual(overview.unrealizedPnl, 500.0)
        XCTAssertEqual(overview.crossAccountLeverageRatio, 5.0)
        XCTAssertEqual(overview.volume, 250000.0)
        XCTAssertEqual(overview.sharpeRatio, 1.5)
        XCTAssertEqual(overview.realizedPnl, 1500.0)
        XCTAssertEqual(overview.liquidationFeesPaid, 50.0)
    }

    func testUserSubaccount_Deserialization() throws {
        let json = """
        {
            "subaccount_address": "0xsub",
            "primary_account_address": "0xowner",
            "is_primary": true,
            "custom_label": "Main Trading",
            "is_active": true
        }
        """.data(using: .utf8)!

        let sub = try decoder.decode(UserSubaccount.self, from: json)
        XCTAssertEqual(sub.subaccountAddress, "0xsub")
        XCTAssertTrue(sub.isPrimary)
        XCTAssertEqual(sub.customLabel, "Main Trading")
        XCTAssertEqual(sub.isActive, true)
    }

    func testUserSubaccount_NullOptionals() throws {
        let json = """
        {
            "subaccount_address": "0xsub",
            "primary_account_address": "0xowner",
            "is_primary": false,
            "custom_label": null,
            "is_active": null
        }
        """.data(using: .utf8)!

        let sub = try decoder.decode(UserSubaccount.self, from: json)
        XCTAssertFalse(sub.isPrimary)
        XCTAssertNil(sub.customLabel)
        XCTAssertNil(sub.isActive)
    }

    func testDelegation_WithExpiration() throws {
        let json = """
        {
            "delegated_account": "0xdelegate",
            "permission_type": "trading",
            "expiration_time_s": 1700000000
        }
        """.data(using: .utf8)!

        let delegation = try decoder.decode(Delegation.self, from: json)
        XCTAssertEqual(delegation.delegatedAccount, "0xdelegate")
        XCTAssertEqual(delegation.permissionType, "trading")
        XCTAssertEqual(delegation.expirationTimeS, 1700000000)
    }

    func testDelegation_NullExpiration() throws {
        let json = """
        {
            "delegated_account": "0xd",
            "permission_type": "all",
            "expiration_time_s": null
        }
        """.data(using: .utf8)!

        let delegation = try decoder.decode(Delegation.self, from: json)
        XCTAssertNil(delegation.expirationTimeS)
    }

    func testLeaderboardItem_Deserialization() throws {
        let json = """
        {
            "rank": 1,
            "account": "0x1",
            "account_value": 100000.0,
            "realized_pnl": 5000.0,
            "roi": 0.05,
            "volume": 500000.0
        }
        """.data(using: .utf8)!

        let item = try decoder.decode(LeaderboardItem.self, from: json)
        XCTAssertEqual(item.rank, 1)
        XCTAssertEqual(item.roi, 0.05)
        XCTAssertEqual(item.volume, 500000.0)
    }
}
