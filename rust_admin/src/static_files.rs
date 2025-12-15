use axum::extract::Request;
use axum::http::{Response, StatusCode, header};
use axum::response::Html;
use axum::body::to_bytes;
use std::path::Path;
use tokio::fs;
use serde::Serialize;

pub async fn serve_html(file_name: &str) -> Result<Html<String>, String> {
    let path = Path::new("../admin/base").join(file_name);
    let content = fs::read_to_string(&path)
        .await
        .map_err(|e| format!("Failed to read HTML file {}: {}", file_name, e))?;
    Ok(Html(content))
}

pub async fn serve_css(file_name: &str) -> Result<String, String> {
    let path = Path::new("../admin/asses").join(file_name);
    let content = fs::read_to_string(&path)
        .await
        .map_err(|e| format!("Failed to read CSS file {}: {}", file_name, e))?;
    Ok(content)
}

pub async fn serve_js(file_name: &str) -> Result<String, String> {
    let path = Path::new("../admin/asses").join(file_name);
    let content = fs::read_to_string(&path)
        .await
        .map_err(|e| format!("Failed to read JS file {}: {}", file_name, e))?;
    Ok(content)
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
    pub message: String,
}

// Proxy function to forward requests to Python backend
async fn proxy_to_python_backend(req: Request) -> Result<Response<String>, (StatusCode, String)> {
    // Build the target URL for Python backend
    let python_url = format!("http://localhost:2324{}{}", 
        req.uri().path(), 
        if let Some(query) = req.uri().query() { format!("?{}", query) } else { "".to_string() }
    );
    
    // Extract request details
    let method = req.method().clone();
    let headers = req.headers().clone();
    
    // Read request body
    let body_bytes = to_bytes(req.into_body(), 1024 * 1024).await.map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to read request body: {}", e)))?;
    let body_str = String::from_utf8(body_bytes.to_vec()).unwrap_or_default();
    
    // Create HTTP client
    let client = reqwest::Client::builder().build().map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to create HTTP client: {}", e)))?;
    
    // Forward the request to Python backend with original method
    let response = client.request(method, &python_url)
        .headers(headers)
        .body(body_str)
        .send()
        .await.map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to connect to backend service: {}", e)))?;
    
    // Get status before consuming the response
    let status = response.status();
    
    // Read response body
    let response_body = response.text().await.map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to read response body: {}", e)))?;
    
    // Build and return the response with appropriate content type
    let response = Response::builder()
        .status(status)
        .header(header::CONTENT_TYPE, "application/json")
        .body(response_body)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to build response: {}", e)))?;
    
    Ok(response)
}

pub async fn serve_static(request: Request) -> Result<Response<String>, (StatusCode, String)> {
    let path = request.uri().path();
    
    // API Proxy: Forward all /api requests to Python backend
    if path.starts_with("/api/") {
        return proxy_to_python_backend(request).await;
    }
    
    // Handle CSS files
    if path.ends_with(".css") {
        // Remove leading slash and any directory prefix
        let file_path = path.trim_start_matches('/');
        // If path contains directories, keep only the filename
        let file_name = Path::new(file_path).file_name().unwrap_or_default().to_string_lossy();
        match serve_css(&file_name).await {
            Ok(content) => {
                let response = Response::builder()
                    .status(StatusCode::OK)
                    .header(header::CONTENT_TYPE, "text/css")
                    .body(content)
                    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to build response: {}", e)))?;
                return Ok(response);
            }
            Err(e) => {
                return Ok(Response::builder()
                    .status(StatusCode::NOT_FOUND)
                    .body(format!("CSS file not found: {}", e))
                    .unwrap());
            }
        }
    }
    
    // Handle JS files
    if path.ends_with(".js") {
        // Remove leading slash and any directory prefix
        let file_path = path.trim_start_matches('/');
        // If path contains directories, keep only the filename
        let file_name = Path::new(file_path).file_name().unwrap_or_default().to_string_lossy();
        match serve_js(&file_name).await {
            Ok(content) => {
                let response = Response::builder()
                    .status(StatusCode::OK)
                    .header(header::CONTENT_TYPE, "application/javascript")
                    .body(content)
                    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to build response: {}", e)))?;
                return Ok(response);
            }
            Err(e) => {
                return Ok(Response::builder()
                    .status(StatusCode::NOT_FOUND)
                    .body(format!("JS file not found: {}", e))
                    .unwrap());
            }
        }
    }
    
    // Handle HTML files
    if path.ends_with(".html") || path == "/" {
        let file_name = if path == "/" {
            "login.html".to_string()
        } else {
            // Remove leading slash and any directory prefix
            let file_path = path.trim_start_matches('/');
            let path_obj = Path::new(file_path);
            path_obj.file_name().unwrap_or_default().to_string_lossy().to_string()
        };
        match serve_html(&file_name).await {
            Ok(html_content) => {
                let response = Response::builder()
                    .status(StatusCode::OK)
                    .header(header::CONTENT_TYPE, "text/html")
                    .body(html_content.0)
                    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to build response: {}", e)))?;
                return Ok(response);
            }
            Err(e) => {
                return Ok(Response::builder()
                    .status(StatusCode::NOT_FOUND)
                    .body(format!("HTML file not found: {}", e))
                    .unwrap());
            }
        }
    }
    
    // Default to login page for other paths
    match serve_html("login.html").await {
        Ok(html_content) => {
            let response = Response::builder()
                .status(StatusCode::OK)
                .header(header::CONTENT_TYPE, "text/html")
                .body(html_content.0)
                .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to build response: {}", e)))?;
            Ok(response)
        }
        Err(e) => {
            Ok(Response::builder()
                .status(StatusCode::NOT_FOUND)
                .body(format!("Default page not found: {}", e))
                .unwrap())
        }
    }
}
