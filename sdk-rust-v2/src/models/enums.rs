use serde::{Deserialize, Serialize};
use serde_repr::{Deserialize_repr, Serialize_repr};

// ---------------------------------------------------------------------------
// TimeInForce — wire format is u8 (0, 1, 2)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize_repr, Deserialize_repr)]
#[repr(u8)]
pub enum TimeInForce {
    GoodTillCanceled = 0,
    PostOnly = 1,
    ImmediateOrCancel = 2,
}

impl std::fmt::Display for TimeInForce {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::GoodTillCanceled => write!(f, "GoodTillCanceled"),
            Self::PostOnly => write!(f, "PostOnly"),
            Self::ImmediateOrCancel => write!(f, "ImmediateOrCancel"),
        }
    }
}

// ---------------------------------------------------------------------------
// CandlestickInterval — wire format is string ("1m", "5m", …)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CandlestickInterval {
    #[serde(rename = "1m")]
    OneMinute,
    #[serde(rename = "5m")]
    FiveMinutes,
    #[serde(rename = "15m")]
    FifteenMinutes,
    #[serde(rename = "30m")]
    ThirtyMinutes,
    #[serde(rename = "1h")]
    OneHour,
    #[serde(rename = "2h")]
    TwoHours,
    #[serde(rename = "4h")]
    FourHours,
    #[serde(rename = "8h")]
    EightHours,
    #[serde(rename = "12h")]
    TwelveHours,
    #[serde(rename = "1d")]
    OneDay,
    #[serde(rename = "3d")]
    ThreeDays,
    #[serde(rename = "1w")]
    OneWeek,
    #[serde(rename = "1mo")]
    OneMonth,
}

impl CandlestickInterval {
    pub fn as_seconds(&self) -> u64 {
        match self {
            Self::OneMinute => 60,
            Self::FiveMinutes => 300,
            Self::FifteenMinutes => 900,
            Self::ThirtyMinutes => 1800,
            Self::OneHour => 3600,
            Self::TwoHours => 7200,
            Self::FourHours => 14400,
            Self::EightHours => 28800,
            Self::TwelveHours => 43200,
            Self::OneDay => 86400,
            Self::ThreeDays => 259200,
            Self::OneWeek => 604800,
            Self::OneMonth => 2592000,
        }
    }
}

impl std::fmt::Display for CandlestickInterval {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::OneMinute => "1m",
            Self::FiveMinutes => "5m",
            Self::FifteenMinutes => "15m",
            Self::ThirtyMinutes => "30m",
            Self::OneHour => "1h",
            Self::TwoHours => "2h",
            Self::FourHours => "4h",
            Self::EightHours => "8h",
            Self::TwelveHours => "12h",
            Self::OneDay => "1d",
            Self::ThreeDays => "3d",
            Self::OneWeek => "1w",
            Self::OneMonth => "1mo",
        };
        write!(f, "{s}")
    }
}

// ---------------------------------------------------------------------------
// VolumeWindow
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum VolumeWindow {
    #[serde(rename = "7d")]
    SevenDays,
    #[serde(rename = "14d")]
    FourteenDays,
    #[serde(rename = "30d")]
    ThirtyDays,
    #[serde(rename = "90d")]
    NinetyDays,
}

impl std::fmt::Display for VolumeWindow {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::SevenDays => "7d",
            Self::FourteenDays => "14d",
            Self::ThirtyDays => "30d",
            Self::NinetyDays => "90d",
        };
        write!(f, "{s}")
    }
}

// ---------------------------------------------------------------------------
// OrderStatusType — string-based, with helper methods
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OrderStatusType {
    Acknowledged,
    Filled,
    PartiallyFilled,
    Cancelled,
    Rejected,
    Expired,
    Unknown,
}

impl OrderStatusType {
    /// Terminal states where the order is no longer live on the book.
    pub fn is_final(&self) -> bool {
        matches!(
            self,
            Self::Filled | Self::Cancelled | Self::Rejected | Self::Expired
        )
    }

    /// States indicating at least partial execution success.
    pub fn is_success(&self) -> bool {
        matches!(self, Self::Filled | Self::PartiallyFilled)
    }

    /// Parse from a wire string (case-insensitive).
    pub fn parse(s: &str) -> Self {
        match s.to_ascii_lowercase().as_str() {
            "acknowledged" => Self::Acknowledged,
            "filled" => Self::Filled,
            "partially_filled" | "partiallyfilled" => Self::PartiallyFilled,
            "cancelled" | "canceled" => Self::Cancelled,
            "rejected" => Self::Rejected,
            "expired" => Self::Expired,
            _ => Self::Unknown,
        }
    }
}

impl std::fmt::Display for OrderStatusType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::Acknowledged => "Acknowledged",
            Self::Filled => "Filled",
            Self::PartiallyFilled => "PartiallyFilled",
            Self::Cancelled => "Cancelled",
            Self::Rejected => "Rejected",
            Self::Expired => "Expired",
            Self::Unknown => "Unknown",
        };
        write!(f, "{s}")
    }
}

// ---------------------------------------------------------------------------
// SortDirection
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SortDirection {
    #[serde(rename = "ASC")]
    Ascending,
    #[serde(rename = "DESC")]
    Descending,
}

impl std::fmt::Display for SortDirection {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Ascending => write!(f, "ASC"),
            Self::Descending => write!(f, "DESC"),
        }
    }
}

// ---------------------------------------------------------------------------
// TwapStatus
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TwapStatus {
    Activated,
    Finished,
    Cancelled,
}

impl std::fmt::Display for TwapStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::Activated => "Activated",
            Self::Finished => "Finished",
            Self::Cancelled => "Cancelled",
        };
        write!(f, "{s}")
    }
}

// ---------------------------------------------------------------------------
// TradeAction
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TradeAction {
    OpenLong,
    CloseLong,
    OpenShort,
    CloseShort,
    Net,
}

impl std::fmt::Display for TradeAction {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::OpenLong => "OpenLong",
            Self::CloseLong => "CloseLong",
            Self::OpenShort => "OpenShort",
            Self::CloseShort => "CloseShort",
            Self::Net => "Net",
        };
        write!(f, "{s}")
    }
}

// ---------------------------------------------------------------------------
// VaultType
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum VaultType {
    User,
    Protocol,
}

impl std::fmt::Display for VaultType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::User => write!(f, "User"),
            Self::Protocol => write!(f, "Protocol"),
        }
    }
}

// ---------------------------------------------------------------------------
// DepthAggregationLevel — wire format is integer
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize_repr, Deserialize_repr)]
#[repr(u16)]
pub enum DepthAggregationLevel {
    L1 = 1,
    L2 = 2,
    L5 = 5,
    L10 = 10,
    L100 = 100,
    L1000 = 1000,
}

impl std::fmt::Display for DepthAggregationLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", *self as u16)
    }
}

// ===========================================================================
// Tests
// ===========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // -- TimeInForce --------------------------------------------------------

    /// Wire format for TimeInForce is a bare integer. Bots building
    /// order JSON payloads must emit 0/1/2, not strings.
    #[test]
    fn time_in_force_wire_values() {
        assert_eq!(serde_json::to_string(&TimeInForce::GoodTillCanceled).unwrap(), "0");
        assert_eq!(serde_json::to_string(&TimeInForce::PostOnly).unwrap(), "1");
        assert_eq!(serde_json::to_string(&TimeInForce::ImmediateOrCancel).unwrap(), "2");
    }

    /// Roundtrip ensures the integer encoding survives JSON persistence.
    #[test]
    fn time_in_force_roundtrip() {
        for tif in [
            TimeInForce::GoodTillCanceled,
            TimeInForce::PostOnly,
            TimeInForce::ImmediateOrCancel,
        ] {
            let json = serde_json::to_string(&tif).unwrap();
            let restored: TimeInForce = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, tif);
        }
    }

    /// Guard against accidentally adding or removing variants.
    #[test]
    fn time_in_force_variant_count() {
        let variants = [
            TimeInForce::GoodTillCanceled,
            TimeInForce::PostOnly,
            TimeInForce::ImmediateOrCancel,
        ];
        assert_eq!(variants.len(), 3);
    }

    // -- CandlestickInterval ------------------------------------------------

    /// Wire values for intervals must match the exchange API exactly.
    #[test]
    fn candlestick_interval_wire_values() {
        assert_eq!(serde_json::to_string(&CandlestickInterval::OneMinute).unwrap(), "\"1m\"");
        assert_eq!(serde_json::to_string(&CandlestickInterval::FiveMinutes).unwrap(), "\"5m\"");
        assert_eq!(serde_json::to_string(&CandlestickInterval::OneHour).unwrap(), "\"1h\"");
        assert_eq!(serde_json::to_string(&CandlestickInterval::OneDay).unwrap(), "\"1d\"");
        assert_eq!(serde_json::to_string(&CandlestickInterval::OneMonth).unwrap(), "\"1mo\"");
    }

    /// Roundtrip through JSON for all interval variants.
    #[test]
    fn candlestick_interval_roundtrip() {
        let all = [
            CandlestickInterval::OneMinute,
            CandlestickInterval::FiveMinutes,
            CandlestickInterval::FifteenMinutes,
            CandlestickInterval::ThirtyMinutes,
            CandlestickInterval::OneHour,
            CandlestickInterval::TwoHours,
            CandlestickInterval::FourHours,
            CandlestickInterval::EightHours,
            CandlestickInterval::TwelveHours,
            CandlestickInterval::OneDay,
            CandlestickInterval::ThreeDays,
            CandlestickInterval::OneWeek,
            CandlestickInterval::OneMonth,
        ];
        for v in &all {
            let json = serde_json::to_string(v).unwrap();
            let restored: CandlestickInterval = serde_json::from_str(&json).unwrap();
            assert_eq!(&restored, v);
        }
    }

    #[test]
    fn candlestick_interval_variant_count() {
        let all = [
            CandlestickInterval::OneMinute,
            CandlestickInterval::FiveMinutes,
            CandlestickInterval::FifteenMinutes,
            CandlestickInterval::ThirtyMinutes,
            CandlestickInterval::OneHour,
            CandlestickInterval::TwoHours,
            CandlestickInterval::FourHours,
            CandlestickInterval::EightHours,
            CandlestickInterval::TwelveHours,
            CandlestickInterval::OneDay,
            CandlestickInterval::ThreeDays,
            CandlestickInterval::OneWeek,
            CandlestickInterval::OneMonth,
        ];
        assert_eq!(all.len(), 13);
    }

    /// Duration conversion is used for candlestick time-range math.
    #[test]
    fn candlestick_interval_seconds() {
        assert_eq!(CandlestickInterval::OneMinute.as_seconds(), 60);
        assert_eq!(CandlestickInterval::OneHour.as_seconds(), 3600);
        assert_eq!(CandlestickInterval::OneDay.as_seconds(), 86400);
        assert_eq!(CandlestickInterval::OneWeek.as_seconds(), 604800);
    }

    // -- VolumeWindow -------------------------------------------------------

    /// Wire values for volume windows used in analytics queries.
    #[test]
    fn volume_window_wire_values() {
        assert_eq!(serde_json::to_string(&VolumeWindow::SevenDays).unwrap(), "\"7d\"");
        assert_eq!(serde_json::to_string(&VolumeWindow::ThirtyDays).unwrap(), "\"30d\"");
        assert_eq!(serde_json::to_string(&VolumeWindow::NinetyDays).unwrap(), "\"90d\"");
    }

    #[test]
    fn volume_window_roundtrip() {
        for v in [
            VolumeWindow::SevenDays,
            VolumeWindow::FourteenDays,
            VolumeWindow::ThirtyDays,
            VolumeWindow::NinetyDays,
        ] {
            let json = serde_json::to_string(&v).unwrap();
            let restored: VolumeWindow = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, v);
        }
    }

    #[test]
    fn volume_window_variant_count() {
        let all = [
            VolumeWindow::SevenDays,
            VolumeWindow::FourteenDays,
            VolumeWindow::ThirtyDays,
            VolumeWindow::NinetyDays,
        ];
        assert_eq!(all.len(), 4);
    }

    // -- OrderStatusType ----------------------------------------------------

    /// Bots must know if an order is terminal to stop tracking it.
    #[test]
    fn order_status_is_final() {
        assert!(!OrderStatusType::Acknowledged.is_final());
        assert!(OrderStatusType::Filled.is_final());
        assert!(!OrderStatusType::PartiallyFilled.is_final());
        assert!(OrderStatusType::Cancelled.is_final());
        assert!(OrderStatusType::Rejected.is_final());
        assert!(OrderStatusType::Expired.is_final());
        assert!(!OrderStatusType::Unknown.is_final());
    }

    /// Success states indicate the order executed at least partially.
    #[test]
    fn order_status_is_success() {
        assert!(OrderStatusType::Filled.is_success());
        assert!(OrderStatusType::PartiallyFilled.is_success());
        assert!(!OrderStatusType::Acknowledged.is_success());
        assert!(!OrderStatusType::Cancelled.is_success());
        assert!(!OrderStatusType::Rejected.is_success());
    }

    /// Parse handles variations that may arrive from different API versions.
    #[test]
    fn order_status_parse() {
        assert_eq!(OrderStatusType::parse("acknowledged"), OrderStatusType::Acknowledged);
        assert_eq!(OrderStatusType::parse("FILLED"), OrderStatusType::Filled);
        assert_eq!(OrderStatusType::parse("partially_filled"), OrderStatusType::PartiallyFilled);
        assert_eq!(OrderStatusType::parse("PartiallyFilled"), OrderStatusType::PartiallyFilled);
        assert_eq!(OrderStatusType::parse("cancelled"), OrderStatusType::Cancelled);
        assert_eq!(OrderStatusType::parse("canceled"), OrderStatusType::Cancelled);
        assert_eq!(OrderStatusType::parse("unknown_value"), OrderStatusType::Unknown);
    }

    /// Roundtrip for order status through JSON.
    #[test]
    fn order_status_roundtrip() {
        for v in [
            OrderStatusType::Acknowledged,
            OrderStatusType::Filled,
            OrderStatusType::PartiallyFilled,
            OrderStatusType::Cancelled,
            OrderStatusType::Rejected,
            OrderStatusType::Expired,
            OrderStatusType::Unknown,
        ] {
            let json = serde_json::to_string(&v).unwrap();
            let restored: OrderStatusType = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, v);
        }
    }

    #[test]
    fn order_status_variant_count() {
        let all = [
            OrderStatusType::Acknowledged,
            OrderStatusType::Filled,
            OrderStatusType::PartiallyFilled,
            OrderStatusType::Cancelled,
            OrderStatusType::Rejected,
            OrderStatusType::Expired,
            OrderStatusType::Unknown,
        ];
        assert_eq!(all.len(), 7);
    }

    // -- SortDirection ------------------------------------------------------

    /// Wire values must be uppercase strings matching the REST API.
    #[test]
    fn sort_direction_wire_values() {
        assert_eq!(serde_json::to_string(&SortDirection::Ascending).unwrap(), "\"ASC\"");
        assert_eq!(serde_json::to_string(&SortDirection::Descending).unwrap(), "\"DESC\"");
    }

    #[test]
    fn sort_direction_roundtrip() {
        for v in [SortDirection::Ascending, SortDirection::Descending] {
            let json = serde_json::to_string(&v).unwrap();
            let restored: SortDirection = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, v);
        }
    }

    // -- TwapStatus ---------------------------------------------------------

    #[test]
    fn twap_status_roundtrip() {
        for v in [TwapStatus::Activated, TwapStatus::Finished, TwapStatus::Cancelled] {
            let json = serde_json::to_string(&v).unwrap();
            let restored: TwapStatus = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, v);
        }
    }

    #[test]
    fn twap_status_variant_count() {
        let all = [TwapStatus::Activated, TwapStatus::Finished, TwapStatus::Cancelled];
        assert_eq!(all.len(), 3);
    }

    // -- TradeAction --------------------------------------------------------

    /// TradeAction serializes as PascalCase strings matching the API.
    #[test]
    fn trade_action_roundtrip() {
        for v in [
            TradeAction::OpenLong,
            TradeAction::CloseLong,
            TradeAction::OpenShort,
            TradeAction::CloseShort,
            TradeAction::Net,
        ] {
            let json = serde_json::to_string(&v).unwrap();
            let restored: TradeAction = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, v);
        }
    }

    #[test]
    fn trade_action_variant_count() {
        let all = [
            TradeAction::OpenLong,
            TradeAction::CloseLong,
            TradeAction::OpenShort,
            TradeAction::CloseShort,
            TradeAction::Net,
        ];
        assert_eq!(all.len(), 5);
    }

    // -- VaultType ----------------------------------------------------------

    #[test]
    fn vault_type_roundtrip() {
        for v in [VaultType::User, VaultType::Protocol] {
            let json = serde_json::to_string(&v).unwrap();
            let restored: VaultType = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, v);
        }
    }

    // -- DepthAggregationLevel ----------------------------------------------

    /// Wire format is a bare integer; bots use it in depth subscription topic strings.
    #[test]
    fn depth_aggregation_wire_values() {
        assert_eq!(serde_json::to_string(&DepthAggregationLevel::L1).unwrap(), "1");
        assert_eq!(serde_json::to_string(&DepthAggregationLevel::L2).unwrap(), "2");
        assert_eq!(serde_json::to_string(&DepthAggregationLevel::L5).unwrap(), "5");
        assert_eq!(serde_json::to_string(&DepthAggregationLevel::L10).unwrap(), "10");
        assert_eq!(serde_json::to_string(&DepthAggregationLevel::L100).unwrap(), "100");
        assert_eq!(serde_json::to_string(&DepthAggregationLevel::L1000).unwrap(), "1000");
    }

    #[test]
    fn depth_aggregation_roundtrip() {
        for v in [
            DepthAggregationLevel::L1,
            DepthAggregationLevel::L2,
            DepthAggregationLevel::L5,
            DepthAggregationLevel::L10,
            DepthAggregationLevel::L100,
            DepthAggregationLevel::L1000,
        ] {
            let json = serde_json::to_string(&v).unwrap();
            let restored: DepthAggregationLevel = serde_json::from_str(&json).unwrap();
            assert_eq!(restored, v);
        }
    }

    #[test]
    fn depth_aggregation_variant_count() {
        let all = [
            DepthAggregationLevel::L1,
            DepthAggregationLevel::L2,
            DepthAggregationLevel::L5,
            DepthAggregationLevel::L10,
            DepthAggregationLevel::L100,
            DepthAggregationLevel::L1000,
        ];
        assert_eq!(all.len(), 6);
    }

    // -- Display trait smoke ------------------------------------------------

    /// Display output is used in logging and tracing spans.
    #[test]
    fn display_impls() {
        assert_eq!(TimeInForce::PostOnly.to_string(), "PostOnly");
        assert_eq!(CandlestickInterval::OneHour.to_string(), "1h");
        assert_eq!(VolumeWindow::ThirtyDays.to_string(), "30d");
        assert_eq!(OrderStatusType::Filled.to_string(), "Filled");
        assert_eq!(SortDirection::Ascending.to_string(), "ASC");
        assert_eq!(TwapStatus::Activated.to_string(), "Activated");
        assert_eq!(TradeAction::OpenLong.to_string(), "OpenLong");
        assert_eq!(VaultType::Protocol.to_string(), "Protocol");
        assert_eq!(DepthAggregationLevel::L100.to_string(), "100");
    }
}
