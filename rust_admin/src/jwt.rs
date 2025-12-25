use jsonwebtoken::{encode, decode, Header, Validation, EncodingKey, DecodingKey, errors::Error as JwtError};
use serde::{Deserialize, Serialize};
use std::sync::{RwLock, OnceLock};
use chrono::{Utc, Duration};
use log::info;

// 密钥轮换管理
static KEY_ROTATION: OnceLock<RwLock<KeyRotation>> = OnceLock::new();

#[derive(Debug, Clone)]
struct KeyRotation {
    current_key: String,
    previous_key: String,
    rotation_time: chrono::DateTime<Utc>,
}

impl KeyRotation {
    fn new() -> Self {
        let current_key = std::env::var("JWT_SECRET").unwrap_or_else(|_| "default_secret_key".to_string());
        Self {
            current_key: current_key.clone(),
            previous_key: current_key,
            rotation_time: Utc::now(),
        }
    }

    fn rotate(&mut self) {
        self.previous_key = self.current_key.clone();
        self.current_key = format!("{}_{}", self.current_key, Utc::now().timestamp());
        self.rotation_time = Utc::now();
        info!("JWT密钥已轮换");
    }

    fn should_rotate(&self) -> bool {
        Utc::now().signed_duration_since(self.rotation_time) > Duration::hours(24)
    }

    fn get_keys(&self) -> (String, String) {
        (self.current_key.clone(), self.previous_key.clone())
    }
}

fn get_key_rotation() -> &'static RwLock<KeyRotation> {
    KEY_ROTATION.get_or_init(|| RwLock::new(KeyRotation::new()))
}

// JWT载荷结构
#[derive(Debug, Serialize, Deserialize)]
pub struct JwtPayload {
    pub iss: String,    // 签发人
    pub aud: String,    // 受众
    pub uid: u32,       // 用户ID
    pub name: String,   // 用户名
    pub exp: i64,       // 过期时间
    pub iat: i64,       // 签发时间
}

// 生成Token
pub fn generate_token(uid: u32, name: &str, expire_minutes: i64) -> Result<String, JwtError> {
    let key_rotation = get_key_rotation().read().unwrap();
    
    // 检查是否需要轮换密钥
    if key_rotation.should_rotate() {
        drop(key_rotation);
        let mut key_rotation = get_key_rotation().write().unwrap();
        key_rotation.rotate();
    }
    
    let (current_key, _) = get_key_rotation().read().unwrap().get_keys();
    
    let now = Utc::now();
    let payload = JwtPayload {
        iss: std::env::var("JWT_ISS").unwrap_or_else(|_| "lmoadll_admin".to_string()),
        aud: std::env::var("JWT_AUD").unwrap_or_else(|_| "lmoadll_client".to_string()),
        uid,
        name: name.to_string(),
        exp: (now + Duration::minutes(expire_minutes)).timestamp(),
        iat: now.timestamp(),
    };
    
    encode(&Header::default(), &payload, &EncodingKey::from_secret(current_key.as_bytes()))
}

// 验证Token
pub fn validate_token(token: &str) -> Result<JwtPayload, JwtError> {
    let key_rotation = get_key_rotation().read().unwrap();
    let (current_key, previous_key) = key_rotation.get_keys();
    
    // 先尝试用当前密钥验证
    let mut validation = Validation::default();
    validation.set_issuer(&[std::env::var("JWT_ISS").unwrap_or_else(|_| "lmoadll_admin".to_string())]);
    validation.set_audience(&[std::env::var("JWT_AUD").unwrap_or_else(|_| "lmoadll_client".to_string())]);
    
    match decode::<JwtPayload>(token, &DecodingKey::from_secret(current_key.as_bytes()), &validation) {
        Ok(token_data) => Ok(token_data.claims),
        Err(_) => {
            // 如果当前密钥验证失败，尝试用之前的密钥验证
            decode::<JwtPayload>(token, &DecodingKey::from_secret(previous_key.as_bytes()), &validation)
                .map(|token_data| token_data.claims)
        }
    }
}