use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct CommonResponse {
    pub code: u32,
    pub message: String,
}