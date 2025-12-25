use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct LoginData {
    pub uid: u32,
    pub name: String,
    pub avatar: String,
    pub group: String,
    pub access_token: String,
}

#[derive(Debug, Serialize)]
pub struct LoginResponse {
    pub code: u32,
    pub message: String,
    pub data: LoginData,
}