use axum::response::Html;
use std::path::PathBuf;

pub async fn admin_page() -> Html<String> {
    let html_path = PathBuf::from("../admin/base/admin.html");
    match tokio::fs::read_to_string(&html_path).await {
        Ok(content) => Html(content),
        Err(_) => Html("<h1>Admin page not found</h1>".to_string()),
    }
}

pub async fn user_management_page() -> Html<String> {
    let html_path = PathBuf::from("../admin/base/UserManagement.html");
    match tokio::fs::read_to_string(&html_path).await {
        Ok(content) => Html(content),
        Err(_) => Html("<h1>User management page not found</h1>".to_string()),
    }
}

pub async fn options_general_page() -> Html<String> {
    let html_path = PathBuf::from("../admin/base/options-general.html");
    match tokio::fs::read_to_string(&html_path).await {
        Ok(content) => Html(content),
        Err(_) => Html("<h1>Options general page not found</h1>".to_string()),
    }
}
