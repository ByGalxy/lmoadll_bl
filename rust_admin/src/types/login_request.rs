use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub username_email: String,
    pub password: String,
}