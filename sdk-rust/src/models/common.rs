use serde::{Deserialize, Serialize};

// --- Enumerations ---

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[repr(u8)]
pub enum TimeInForce {
    GoodTillCanceled = 0,
    PostOnly = 1,
    ImmediateOrCancel = 2,
}

impl TimeInForce {
    pub fn as_u8(&self) -> u8 {
        *self as u8
    }

    pub fn from_u8(value: u8) -> Option<Self> {
        match value {
            0 => Some(Self::GoodTillCanceled),
            1 => Some(Self::PostOnly),
            2 => Some(Self::ImmediateOrCancel),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
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
    pub fn as_str(&self) -> &'static str {
        match self {
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
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
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

impl VolumeWindow {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::SevenDays => "7d",
            Self::FourteenDays => "14d",
            Self::ThirtyDays => "30d",
            Self::NinetyDays => "90d",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OrderStatusType {
    Acknowledged,
    Filled,
    Cancelled,
    Rejected,
    Unknown,
}

impl OrderStatusType {
    pub fn from_str(s: &str) -> Self {
        match s {
            "Acknowledged" => Self::Acknowledged,
            "Filled" => Self::Filled,
            "Cancelled" | "Canceled" => Self::Cancelled,
            "Rejected" => Self::Rejected,
            _ => Self::Unknown,
        }
    }

    pub fn is_success(&self) -> bool {
        matches!(self, Self::Acknowledged | Self::Filled)
    }

    pub fn is_failure(&self) -> bool {
        matches!(self, Self::Cancelled | Self::Rejected)
    }

    pub fn is_final(&self) -> bool {
        self.is_success() || self.is_failure()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SortDirection {
    #[serde(rename = "ASC")]
    Ascending,
    #[serde(rename = "DESC")]
    Descending,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TwapStatus {
    Activated,
    Finished,
    Cancelled,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TradeAction {
    OpenLong,
    CloseLong,
    OpenShort,
    CloseShort,
    Net,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum VaultType {
    User,
    Protocol,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MarketDepthAggregationSize {
    One = 1,
    Two = 2,
    Five = 5,
    Ten = 10,
    Hundred = 100,
    Thousand = 1000,
}

impl MarketDepthAggregationSize {
    pub fn all() -> [Self; 6] {
        [
            Self::One,
            Self::Two,
            Self::Five,
            Self::Ten,
            Self::Hundred,
            Self::Thousand,
        ]
    }
}

// --- Pagination ---

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PageParams {
    pub limit: Option<i32>,
    pub offset: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaginatedResponse<T> {
    pub items: Vec<T>,
    pub total_count: i64,
}

#[derive(Debug, Clone, Default)]
pub struct SortParams {
    pub sort_key: Option<String>,
    pub sort_dir: Option<SortDirection>,
}

#[derive(Debug, Clone, Default)]
pub struct SearchTermParams {
    pub search_term: Option<String>,
}

// --- Place Order Result ---

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlaceOrderResult {
    pub success: bool,
    pub order_id: Option<String>,
    pub transaction_hash: Option<String>,
    pub error: Option<String>,
}

impl PlaceOrderResult {
    pub fn success(order_id: Option<String>, transaction_hash: String) -> Self {
        Self {
            success: true,
            order_id,
            transaction_hash: Some(transaction_hash),
            error: None,
        }
    }

    pub fn failure(error: String) -> Self {
        Self {
            success: false,
            order_id: None,
            transaction_hash: None,
            error: Some(error),
        }
    }
}

// --- TWAP Order Result ---

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TwapOrderResult {
    pub success: bool,
    pub order_id: Option<String>,
    pub transaction_hash: String,
}
