use axum::{
    Router,
    routing::{get, post},
};
use std::sync::Arc;

use crate::handlers::auth;
use crate::services::auth::AuthService;

pub fn routes(auth_service: Arc<AuthService>) -> Router {
    Router::new()
        .route("/auth/login", post(auth::login))
        .route("/auth/check", get(auth::check))
        .with_state(auth_service)
}
