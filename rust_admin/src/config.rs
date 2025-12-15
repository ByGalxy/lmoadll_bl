use dotenv::dotenv;
use sqlx::SqlitePool;
use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub database_url: String,
    pub jwt_secret: String,
    pub server_host: String,
    pub server_port: u16,
}

impl Config {
    pub fn from_env() -> Result<Self, String> {
        dotenv().ok();

        Ok(Self {
            database_url: env::var("DATABASE_URL")
                .unwrap_or_else(|_| "sqlite:E:\\Windows\\Documents\\AWorkAndProjects\\python\\web\\lmoadll_bl_py\\contents\\rs3o8qxrn7.db".to_string()),
            jwt_secret: env::var("JWT_SECRET")
                .unwrap_or_else(|_| "your-secret-key-change-in-production".to_string()),
            server_host: env::var("SERVER_HOST")
                .unwrap_or_else(|_| "0.0.0.0".to_string()),
            server_port: env::var("SERVER_PORT")
                .unwrap_or_else(|_| "2326".to_string())
                .parse()
                .map_err(|e| format!("Invalid port number: {}", e))?,
        })
    }

    pub async fn create_pool(&self) -> Result<SqlitePool, String> {
        SqlitePool::connect(&self.database_url)
            .await
            .map_err(|e| format!("Failed to connect to database: {}", e))
    }
}
