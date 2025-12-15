use axum::response::Html;
use std::path::PathBuf;

pub async fn login_page() -> Html<String> {
    let html_path = PathBuf::from("../admin/base/login.html");
    match tokio::fs::read_to_string(&html_path).await {
        Ok(content) => Html(content),
        Err(_) => Html("<h1>Login page not found</h1>".to_string()),
    }
}
