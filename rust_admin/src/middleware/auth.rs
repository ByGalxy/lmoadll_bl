use axum::{
    body::Body,
    http::{Request, StatusCode, header},
    middleware::Next,
    response::Response,
    extract::State,
};
use std::sync::Arc;

use crate::services::auth::AuthService;

pub async fn admin_required<B>(
    State(auth_service): State<Arc<AuthService>>,
    req: Request<B>,
    next: Next,
) -> Result<Response, StatusCode> {
    // Extract token from Authorization header
    let auth_header = req.headers().get(header::AUTHORIZATION);
    
    match auth_header {
        Some(header_value) => {
            let header_str = header_value.to_str().map_err(|_| StatusCode::UNAUTHORIZED)?;
            
            // Check if it's a Bearer token
            if !header_str.starts_with("Bearer ") {
                return Err(StatusCode::UNAUTHORIZED);
            }
            
            let token = &header_str[7..]; // Skip "Bearer "
            
            // Validate token
            match auth_service.validate_token(token).await {
                Ok(_) => {
                    // Convert Request<B> to Request<Body> for next.run
                    let (parts, _) = req.into_parts();
                    let req = Request::from_parts(parts, Body::empty());
                    Ok(next.run(req).await)
                }
                Err(_) => Err(StatusCode::UNAUTHORIZED),
            }
        }
        None => Err(StatusCode::UNAUTHORIZED),
    }
}
