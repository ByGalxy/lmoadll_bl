use actix_web::web;
use crate::auth::{login_api, refresh_token_api, logout_api, protected_api};

pub fn user_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api/auth")
            .route("/login", web::post().to(login_api))
            .route("/token/refresh", web::post().to(refresh_token_api))
            .route("/logout", web::post().to(logout_api))
            .route("/protected", web::post().to(protected_api))
    );
}