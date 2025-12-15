use axum::{
    extract::State,
    http::{header, HeaderMap},
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

use crate::services::auth::AuthService;

#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    email: String,
    password: String,
}

#[derive(Debug, Serialize)]
pub struct LoginResponse {
    success: bool,
    message: String,
    access_token: Option<String>,
    refresh_token: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    sub: String,
    exp: usize,
    iat: usize,
}

pub async fn login(
    State(auth_service): State<Arc<AuthService>>,
    Json(payload): Json<LoginRequest>,
) -> Json<LoginResponse> {
    match auth_service.authenticate(&payload.email, &payload.password).await {
        Ok(token) => Json(LoginResponse {
            success: true,
            message: "Login successful".to_string(),
            access_token: Some(token),
            refresh_token: None,
        }),
        Err(err) => Json(LoginResponse {
            success: false,
            message: format!("Authentication failed: {}", err),
            access_token: None,
            refresh_token: None,
        }),
    }
}

pub async fn check(
    State(auth_service): State<Arc<AuthService>>,
    headers: HeaderMap,
) -> impl IntoResponse {
    // Extract token from Authorization header
    let auth_header = headers.get(header::AUTHORIZATION);
    
    match auth_header {
        Some(header_value) => {
            let header_str = match header_value.to_str() {
                Ok(s) => s,
                Err(_) => {
                    return Json(LoginResponse {
                        success: false,
                        message: "Invalid authorization header".to_string(),
                        access_token: None,
                        refresh_token: None,
                    })
                }
            };
            
            // Check if it's a Bearer token
            if !header_str.starts_with("Bearer ") {
                return Json(LoginResponse {
                    success: false,
                    message: "Invalid token format".to_string(),
                    access_token: None,
                    refresh_token: None,
                });
            }
            
            let token = &header_str[7..]; // Skip "Bearer "
            
            // Validate token
            match auth_service.validate_token(token).await {
                Ok(_) => Json(LoginResponse {
                    success: true,
                    message: "Token is valid".to_string(),
                    access_token: None,
                    refresh_token: None,
                }),
                Err(_) => Json(LoginResponse {
                    success: false,
                    message: "Invalid or expired token".to_string(),
                    access_token: None,
                    refresh_token: None,
                }),
            }
        }
        None => Json(LoginResponse {
            success: false,
            message: "No authorization header".to_string(),
            access_token: None,
            refresh_token: None,
        }),
    }
}
