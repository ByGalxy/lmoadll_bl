use axum::{
    Router,
    routing::{get, post},
};
use std::sync::Arc;

use crate::handlers::{admin, install, login};
use crate::middleware::auth;
use crate::services::auth::AuthService;

pub fn routes(auth_service: Arc<AuthService>) -> Router {
    Router::new()
        // Install routes (no auth required)
        .route("/install", get(install::install_page))
        .route("/install/check_config", post(install::check_config))
        .route("/install/generate_sqlite_path", post(install::generate_sqlite_path))
        .route("/install/test_connection", post(install::test_connection))
        .route("/install/save_config", post(install::save_config))
        
        // Login routes (no auth required)
        .route("/login", get(login::login_page))
        
        // Admin routes (require auth)
        .route("/", get(admin::admin_page).layer(axum::middleware::from_fn_with_state(auth_service.clone(), auth::admin_required)))
        .route("/user_management", get(admin::user_management_page).layer(axum::middleware::from_fn_with_state(auth_service.clone(), auth::admin_required)))
        .route("/options_general", get(admin::options_general_page).layer(axum::middleware::from_fn_with_state(auth_service.clone(), auth::admin_required)))
}
