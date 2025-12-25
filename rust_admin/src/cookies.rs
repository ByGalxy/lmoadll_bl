use actix_web::cookie::{Cookie, SameSite};

// Cookie配置常量
pub const REFRESH_TOKEN_COOKIE_NAME: &str = "refresh_token";
pub const REFRESH_TOKEN_MAX_AGE_DAYS: i64 = 7;

// 创建refresh_token cookie
pub fn create_refresh_token_cookie<'a>(token: &'a str) -> Cookie<'a> {
    Cookie::build(REFRESH_TOKEN_COOKIE_NAME, token)
        .http_only(true)
        .secure(false) // 开发环境设为false，生产环境设为true
        .same_site(SameSite::Strict)
        .path("/")
        .max_age(actix_web::cookie::time::Duration::days(REFRESH_TOKEN_MAX_AGE_DAYS))
        .finish()
}

// 创建清除refresh_token的cookie
pub fn create_clear_refresh_token_cookie() -> Cookie<'static> {
    Cookie::build(REFRESH_TOKEN_COOKIE_NAME, "")
        .http_only(true)
        .secure(false)
        .same_site(SameSite::Strict)
        .path("/")
        .max_age(actix_web::cookie::time::Duration::seconds(0)) // 立即过期
        .finish()
}