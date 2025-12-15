use crate::models::user::User;
use argon2::{Argon2, PasswordHash, PasswordVerifier};
use jsonwebtoken::{encode, EncodingKey, Header};
use serde::{Deserialize, Serialize};
use sqlx::SqlitePool;

#[derive(Debug, Serialize, Deserialize)]
pub struct AuthClaims {
    pub sub: String,
    pub exp: usize,
    pub is_admin: bool,
}

#[derive(Clone)]
pub struct AuthService {
    pool: SqlitePool,
    jwt_secret: String,
}

impl AuthService {
    pub fn new(pool: SqlitePool, jwt_secret: String) -> Self {
        Self { pool, jwt_secret }
    }

    pub async fn authenticate(&self, email: &str, password: &str) -> Result<String, String> {
        let user = sqlx::query_as::<_, User>(
            "SELECT * FROM users WHERE email = ?"
        )
        .bind(email)
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| format!("Database error: {}", e))?;

        let user = user.ok_or_else(|| "Invalid email or password".to_string())?;

        let argon2 = Argon2::default();
        let parsed_hash = PasswordHash::new(&user.password_hash)
            .map_err(|e| format!("Password hash error: {}", e))?;

        argon2
            .verify_password(password.as_bytes(), &parsed_hash)
            .map_err(|_| "Invalid email or password".to_string())?;

        let claims = AuthClaims {
            sub: user.email,
            exp: (chrono::Utc::now() + chrono::Duration::hours(24)).timestamp() as usize,
            is_admin: user.is_admin,
        };

        encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(self.jwt_secret.as_bytes()),
        )
        .map_err(|e| format!("JWT encoding error: {}", e))
    }

    pub async fn validate_token(&self, token: &str) -> Result<AuthClaims, String> {
        let validation = jsonwebtoken::Validation::default();
        let token_data = jsonwebtoken::decode::<AuthClaims>(
            token,
            &jsonwebtoken::DecodingKey::from_secret(self.jwt_secret.as_bytes()),
            &validation,
        )
        .map_err(|e| format!("Invalid token: {}", e))?;

        Ok(token_data.claims)
    }
}
