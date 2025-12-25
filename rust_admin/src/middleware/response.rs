use actix_web::{HttpResponse, ResponseError, body::BoxBody, http::StatusCode};
use serde::Serialize;
use std::fmt;

// 响应状态码常量
pub const SUCCESS_CODE: u32 = 200;
pub const CUSTOM_ERROR_CODE: u32 = 233;
pub const SYSTEM_ERROR_CODE: u32 = 500;

// 通用响应结构
#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub code: u32,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
}

// 成功响应
pub fn success_response<T: Serialize>(data: Option<T>, message: &str) -> HttpResponse {
    HttpResponse::Ok().json(ApiResponse {
        code: SUCCESS_CODE,
        message: message.to_string(),
        data,
    })
}

// 自定义错误响应（已知错误）
pub fn custom_error_response<T: Serialize>(message: &str, data: Option<T>) -> HttpResponse {
    HttpResponse::Ok().json(ApiResponse {
        code: CUSTOM_ERROR_CODE,
        message: message.to_string(),
        data,
    })
}

// 系统错误响应（未知错误）
pub fn error_response<T: Serialize>(message: &str, data: Option<T>) -> HttpResponse {
    HttpResponse::InternalServerError().json(ApiResponse {
        code: SYSTEM_ERROR_CODE,
        message: message.to_string(),
        data,
    })
}

// 响应处理错误类型
#[derive(Debug)]
pub struct ResponseErrorWrapper {
    pub message: String,
    pub error_type: ResponseErrorType,
}

#[derive(Debug)]
pub enum ResponseErrorType {
    CustomError,
    SystemError,
}

impl fmt::Display for ResponseErrorWrapper {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl ResponseError for ResponseErrorWrapper {
    fn error_response(&self) -> HttpResponse<BoxBody> {
        match self.error_type {
            ResponseErrorType::CustomError => custom_error_response::<()>(&self.message, None),
            ResponseErrorType::SystemError => error_response::<()>(&self.message, None),
        }
    }
    
    fn status_code(&self) -> StatusCode {
        match self.error_type {
            ResponseErrorType::CustomError => StatusCode::OK, // 保持与Python一致，返回200状态码但code字段为233
            ResponseErrorType::SystemError => StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}

// 便捷的错误创建函数
pub fn custom_error(message: &str) -> ResponseErrorWrapper {
    ResponseErrorWrapper {
        message: message.to_string(),
        error_type: ResponseErrorType::CustomError,
    }
}

pub fn system_error(message: &str) -> ResponseErrorWrapper {
    ResponseErrorWrapper {
        message: message.to_string(),
        error_type: ResponseErrorType::SystemError,
    }
}

// 响应处理中间件工具
pub struct ResponseHandler;

impl ResponseHandler {
    pub fn success<T: Serialize>(data: Option<T>, message: &str) -> HttpResponse {
        success_response(data, message)
    }
    
    pub fn custom_error<T: Serialize>(message: &str, data: Option<T>) -> HttpResponse {
        custom_error_response(message, data)
    }
    
    pub fn error<T: Serialize>(message: &str, data: Option<T>) -> HttpResponse {
        error_response(message, data)
    }
}

// 全局响应处理实例
pub static RESPONSE_HANDLER: ResponseHandler = ResponseHandler;