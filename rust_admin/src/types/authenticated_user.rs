use actix_web::{http::header, HttpRequest, FromRequest, dev::Payload};
use futures_util::future::{Ready, ok, err};
use log::warn;
use serde::Serialize;

use crate::jwt::validate_token;

// 认证用户结构体
#[derive(Debug, Serialize)]
pub struct AuthenticatedUser {
    pub uid: u32,
    pub name: String,
}

impl FromRequest for AuthenticatedUser {
    type Error = actix_web::Error;
    type Future = Ready<Result<Self, Self::Error>>;

    fn from_request(req: &HttpRequest, _: &mut Payload) -> Self::Future {
        // 检查Authorization头部
        if let Some(auth_header) = req.headers().get(header::AUTHORIZATION) {
            if let Ok(auth_str) = auth_header.to_str() {
                if auth_str.starts_with("Bearer ") {
                    let token = &auth_str[7..]; // 去掉"Bearer "前缀
                    
                    match validate_token(token) {
                        Ok(payload) => {
                            return ok(AuthenticatedUser {
                                uid: payload.uid,
                                name: payload.name,
                            });
                        }
                        Err(e) => {
                            warn!("Token验证失败: {}", e);
                            return err(actix_web::error::ErrorUnauthorized("Token无效"));
                        }
                    }
                }
            }
        }
        
        err(actix_web::error::ErrorUnauthorized("需要认证"))
    }
}