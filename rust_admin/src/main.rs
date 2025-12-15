use axum::{
    Router,
    routing::get,
};
use std::net::SocketAddr;
use tracing_subscriber;

mod config;
mod handlers;
mod models;
mod routes;
mod middleware;
mod services;
mod static_files;

use crate::config::Config;

#[tokio::main]
async fn main() -> Result<(), String> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    // Load configuration
    let config = Config::from_env()?;
    tracing::info!("Configuration loaded");
    
    // Create database connection pool
    let pool = config.create_pool().await?;
    tracing::info!("Database connection pool created");
    
    // Create auth service
    let auth_service = services::auth::AuthService::new(pool.clone(), config.jwt_secret.clone());
    
    // Build our application with routes
    let app = Router::new()
        .route("/", get(root))
        .nest("/admin", routes::admin::routes(auth_service.clone().into()))
        .fallback(static_files::serve_static);
    
    // Run our application
    let addr = SocketAddr::from((config.server_host.parse::<std::net::IpAddr>().unwrap(), config.server_port));
    tracing::info!("Server listening on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await
        .map_err(|e| format!("Failed to bind to address: {}", e))?;
    
    axum::serve(listener, app)
        .await
        .map_err(|e| format!("Server error: {}", e))?;
    
    Ok(())
}

async fn root() -> &'static str {
    "{\"Status\": \"OK\"}"
}

