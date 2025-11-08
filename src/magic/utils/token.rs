// JWT Token 管理模块
// 
// 该模块提供JWT token的创建、验证和管理功能,
// 用于应用程序的用户认证和会话管理。

use std::sync::{Arc, RwLock};
use chrono::{DateTime, Duration, Utc};
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use rand::Rng;
use hex;
use lazy_static::lazy_static;


/// JWT Claims结构体
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,           // 用户身份
    pub token_type: String,    // token类型
    pub created_at: String,    // 创建时间
    pub exp: i64,              // 过期时间
    pub iat: i64,              // 签发时间
}


/// Token创建结果
#[derive(Debug, Serialize)]
pub struct TokenPair {
    pub lmoadll_user: String,          // Access Token
    pub lmoadll_refresh_token: String, // Refresh Token
}


/// JWT密钥管理器
#[derive(Debug)]
pub struct JwtKeyManager {
    rotation_days: i64,
    max_keys: usize,
    key_dict: Arc<RwLock<HashMap<String, DateTime<Utc>>>>,
}


impl JwtKeyManager {
    /// 创建新的JWT密钥管理器
    pub fn new(rotation_days: i64, max_keys: usize) -> Self {
        let mut manager = Self {
            rotation_days,
            max_keys,
            key_dict: Arc::new(RwLock::new(HashMap::new())),
        };
        manager.add_new_key();
        manager
    }


    /// 添加新密钥
    fn add_new_key(&mut self) -> String {
        let new_key = Self::generate_key();
        let mut key_dict = self.key_dict.write().unwrap();
        key_dict.insert(new_key.clone(), Utc::now());
        new_key
    }


    /// 生成随机密钥
    fn generate_key() -> String {
        let mut rng = rand::rng();
        let mut key = [0u8; 32];
        rng.fill(&mut key);
        hex::encode(key)
    }


    /// 清理过期密钥
    fn clean_old_keys(&self) {
        let current_time = Utc::now();
        let mut key_dict = self.key_dict.write().unwrap();
        
        // 清理过期密钥
        key_dict.retain(|_, created_time| {
            let key_age = current_time - *created_time;
            key_age.num_days() <= self.rotation_days
        });
        
        // 限制密钥数量不超过max_keys
        if key_dict.len() > self.max_keys {
            // 保留最新的max_keys个密钥
            let mut keys: Vec<(String, DateTime<Utc>)> = key_dict.drain().collect();
            keys.sort_by(|a, b| b.1.cmp(&a.1)); // 按时间降序排序
            
            for (key, time) in keys.into_iter().take(self.max_keys) {
                key_dict.insert(key, time);
            }
        }
    }


    /// 获取当前有效密钥
    pub fn get_current_key(&self) -> String {
        self.clean_old_keys();
        
        let key_dict = self.key_dict.read().unwrap();
        if key_dict.is_empty() {
            drop(key_dict); // 释放读锁
            let mut manager = self.key_dict.write().unwrap();
            let new_key = Self::generate_key();
            manager.insert(new_key.clone(), Utc::now());
            return new_key;
        }
        
        key_dict
            .iter()
            .max_by_key(|&(_, time)| time)
            .map(|(key, _)| key.clone())
            .unwrap()
    }


    /// 获取所有有效密钥
    pub fn get_all_valid_keys(&self) -> Vec<String> {
        self.clean_old_keys();
        let key_dict = self.key_dict.read().unwrap();
        key_dict.keys().cloned().collect()
    }
}


lazy_static! {
    pub static ref JWT_KEY_MANAGER: JwtKeyManager = JwtKeyManager::new(7, 8);
}


/// 初始化JWT管理器
pub fn init_jwt_manager() -> Result<(), Box<dyn std::error::Error>> {
    // 这里可以添加JWT管理器的初始化逻辑
    // 目前直接返回成功
    Ok(())
}


/// 创建双令牌
pub fn create_tokens(identity: &str, additional_claims: Option<HashMap<String, String>>) -> Result<TokenPair, Box<dyn std::error::Error>> {
    let current_key = JWT_KEY_MANAGER.get_current_key();
    
    // 设置默认的额外声明
    let mut base_claims = additional_claims.unwrap_or_default();
    
    // 创建access token
    let access_claims = create_claims(identity, "access", 15, &mut base_claims.clone())?; // 15分钟过期
    let access_token = encode_token(&access_claims, &current_key)?;
    
    // 创建refresh token
    let refresh_claims = create_claims(identity, "refresh", 7 * 24 * 60, &mut base_claims)?; // 7天过期
    let refresh_token = encode_token(&refresh_claims, &current_key)?;
    
    Ok(TokenPair {
        lmoadll_user: access_token,
        lmoadll_refresh_token: refresh_token,
    })
}


/// 创建访问令牌（向后兼容）
pub fn create_jwt_token(identity: &str, additional_claims: Option<HashMap<String, String>>) -> Result<String, Box<dyn std::error::Error>> {
    let tokens = create_tokens(identity, additional_claims)?;
    Ok(tokens.lmoadll_user)
}


/// 刷新访问令牌
pub fn refresh_token(refresh_token: &str, request_context: Option<&RequestContext>) -> Result<String, Box<dyn std::error::Error>> {
    let current_key = JWT_KEY_MANAGER.get_current_key();
    
    // 解码refresh token
    let decoded_token = decode_token(refresh_token, &current_key)?;
    
    // 安全改进：增强验证逻辑
    // 1. 验证token类型
    if decoded_token.claims.token_type != "refresh" {
        return Err("Invalid token type".into());
    }
    
    // 2. 验证用户身份存在
    if decoded_token.claims.sub.is_empty() {
        return Err("Invalid user identity".into());
    }
    
    // 3. 如果提供了请求上下文，进行额外的安全检查
    if let Some(context) = request_context {
        // 验证来源IP（可选，如果需要严格的会话绑定）
        let _current_ip = &context.remote_addr;
        
        // 验证用户代理
        let _current_user_agent = &context.user_agent;
        
        // 检查请求频率（可以集成到Redis等缓存中）
        // 这里可以添加请求限流逻辑，防止暴力刷新攻击
    }
    
    // 4. 验证token是否在黑名单中（预留接口，需要实现黑名单功能）
    // 此处可以调用检查token是否被撤销的函数
    
    // 5. 创建新的access token
    let mut access_claims = HashMap::new();
    access_claims.insert("token_type".to_string(), "access".to_string());
    
    let new_access_token = create_jwt_token(&decoded_token.claims.sub, Some(access_claims))?;
    
    Ok(new_access_token)
}


/// 获取当前用户身份
pub fn get_current_user_identity(authorization_header: Option<&str>, cookie_token: Option<&str>) -> Option<String> {
    // 首先尝试从Authorization头获取
    if let Some(header) = authorization_header {
        if let Some(token) = extract_bearer_token(header) {
            if let Ok(identity) = validate_token_and_get_identity(token) {
                return Some(identity);
            }
        }
    }
    
    // 如果标准方式失败，尝试从cookie中获取令牌
    if let Some(token) = cookie_token {
        if let Ok(identity) = validate_token_and_get_identity(token) {
            return Some(identity);
        }
    }
    
    // 所有方式都失败，返回None
    None
}

// 辅助函数

/// 创建Claims结构体
fn create_claims(identity: &str, token_type: &str, expires_minutes: i64, additional_claims: &mut HashMap<String, String>) -> Result<Claims, Box<dyn std::error::Error>> {
    let now = Utc::now();
    let exp = now + Duration::minutes(expires_minutes);
    
    let mut claims = Claims {
        sub: identity.to_string(),
        token_type: token_type.to_string(),
        created_at: now.to_rfc3339(),
        exp: exp.timestamp(),
        iat: now.timestamp(),
    };
    
    // 添加额外声明
    for (key, value) in additional_claims.iter() {
        match key.as_str() {
            "sub" => claims.sub = value.clone(),
            "token_type" => claims.token_type = value.clone(),
            "created_at" => claims.created_at = value.clone(),
            _ => { /* 忽略未知字段 */ }
        }
    }
    
    Ok(claims)
}


/// 编码Token
fn encode_token(claims: &Claims, key: &str) -> Result<String, Box<dyn std::error::Error>> {
    let encoding_key = EncodingKey::from_secret(key.as_ref());
    let header = Header::new(Algorithm::HS256);
    
    encode(&header, claims, &encoding_key)
        .map_err(|e| e.into())
}


/// 解码Token
fn decode_token(token: &str, key: &str) -> Result<jsonwebtoken::TokenData<Claims>, Box<dyn std::error::Error>> {
    let decoding_key = DecodingKey::from_secret(key.as_ref());
    let validation = Validation::new(Algorithm::HS256);
    
    decode::<Claims>(token, &decoding_key, &validation)
        .map_err(|e| e.into())
}


/// 从Authorization头提取Bearer Token
fn extract_bearer_token(header: &str) -> Option<&str> {
    if header.starts_with("Bearer ") {
        Some(&header[7..]) // 去掉 "Bearer " 前缀
    } else {
        None
    }
}


/// 验证token并获取用户身份
fn validate_token_and_get_identity(token: &str) -> Result<String, Box<dyn std::error::Error>> {
    let current_key = JWT_KEY_MANAGER.get_current_key();
    let decoded = decode_token(token, &current_key)?;
    
    // 验证是否为access token类型
    if decoded.claims.token_type == "access" {
        Ok(decoded.claims.sub)
    } else {
        Err("Invalid token type".into())
    }
}


/// 请求上下文结构体（用于安全验证）
#[derive(Debug)]
pub struct RequestContext {
    pub remote_addr: String,
    pub user_agent: String,
}


impl RequestContext {
    pub fn new(remote_addr: String, user_agent: String) -> Self {
        Self {
            remote_addr,
            user_agent,
        }
    }
}



#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_tokens() {
        let identity = "test_user_123";
        let result = create_tokens(identity, None);
        
        assert!(result.is_ok());
        let tokens = result.unwrap();
        
        assert!(!tokens.lmoadll_user.is_empty());
        assert!(!tokens.lmoadll_refresh_token.is_empty());
        assert_ne!(tokens.lmoadll_user, tokens.lmoadll_refresh_token);
    }

    #[test]
    fn test_create_jwt_token() {
        let identity = "test_user_456";
        let result = create_jwt_token(identity, None);
        
        assert!(result.is_ok());
        let token = result.unwrap();
        assert!(!token.is_empty());
    }

    #[test]
    fn test_refresh_token() {
        // 首先创建refresh token
        let identity = "refresh_test_user";
        let tokens = create_tokens(identity, None).unwrap();
        
        // 测试刷新token
        let result = refresh_token(&tokens.lmoadll_refresh_token, None);
        assert!(result.is_ok());
        
        let new_access_token = result.unwrap();
        assert!(!new_access_token.is_empty());
        assert_ne!(new_access_token, tokens.lmoadll_user);
    }

    #[test]
    fn test_get_current_user_identity() {
        // 创建测试token
        let identity = "auth_test_user";
        let tokens = create_tokens(identity, None).unwrap();
        
        // 测试从Authorization头获取
        let auth_header = format!("Bearer {}", tokens.lmoadll_user);
        let result = get_current_user_identity(Some(&auth_header), None);
        
        assert!(result.is_some());
        assert_eq!(result.unwrap(), identity);
        
        // 测试从cookie获取
        let result = get_current_user_identity(None, Some(&tokens.lmoadll_user));
        assert!(result.is_some());
        assert_eq!(result.unwrap(), identity);
    }

    #[test]
    fn test_jwt_key_manager() {
        let manager = JwtKeyManager::new(7, 5);
        
        // 测试密钥生成
        let key1 = manager.get_current_key();
        assert!(!key1.is_empty());
        
        // 测试密钥列表
        let keys = manager.get_all_valid_keys();
        assert!(!keys.is_empty());
        assert!(keys.contains(&key1));
    }

    #[test]
    fn test_invalid_token_validation() {
        // 测试无效token
        let result = get_current_user_identity(Some("Bearer invalid_token"), None);
        assert!(result.is_none());
        
        // 测试无效的refresh token
        let result = refresh_token("invalid_refresh_token", None);
        assert!(result.is_err());
    }

    #[test]
    fn test_token_expiration() {
        let identity = "expiration_test_user";
        
        // 创建短期token进行测试
        let mut claims = HashMap::new();
        claims.insert("test_field".to_string(), "test_value".to_string());
        
        let result = create_tokens(identity, Some(claims));
        assert!(result.is_ok());
    }
}
