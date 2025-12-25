use serde::Serialize;

// Token数据
#[derive(Debug, Serialize)]
pub struct TokenData {
    pub access_token: String,
}

// Token刷新响应体
#[derive(Debug, Serialize)]
pub struct TokenRefreshResponse {
    pub code: u32,
    pub message: String,
    pub data: TokenData,
}