mod magic;

use serde::Serialize;
use std::env;
use dotenvy::dotenv;
use tokio::net::TcpListener;
use axum::{
    extract::Json,
    response::IntoResponse,
    routing::get,
    Router,
};


// 响应结构体
#[derive(Serialize)]
struct StatusResponse {
    status: String,
}


// 获取IP地址
fn get_local_ip_addresses() -> Vec<String> {
    let mut addresses = Vec::new();
    
    // 总是包含本地回环地址
    addresses.push("127.0.0.1".to_string());
    
    // 获取所有网络接口的IP地址
    if let Ok(interfaces) = get_if_addrs::get_if_addrs() {
        for interface in interfaces {
            // 排除回环接口和虚拟网络接口
            if interface.is_loopback() {
                continue;
            }
            
            // 排除常见的虚拟网络接口名称
            let name = interface.name.to_lowercase();
            if name.contains("virtual") || name.contains("vpn") || 
               name.contains("hyper-v") || name.contains("docker") ||
               name.contains("vmware") || name.contains("vbox") {
                continue;
            }
            
            match interface.addr {
                get_if_addrs::IfAddr::V4(ip) => {
                    let ip_str = ip.ip.to_string();
                    
                    // 只保留真正有用的IP地址：
                    // 1. 排除链路本地地址 (169.254.x.x)
                    // 2. 排除内部网络地址 (172.16.x.x - 172.31.x.x, 192.168.x.x, 10.x.x.x)
                    // 3. 只保留公网IP或特定需要的内部IP
                    
                    if ip_str.starts_with("169.254") {
                        continue; // 链路本地地址
                    }
                    
                    if ip_str.starts_with("172.") {
                        // 检查是否是172.16-172.31范围内的私有地址
                        let octets = ip.ip.octets();
                        if octets[1] >= 16 && octets[1] <= 31 {
                            continue; // 私有地址范围
                        }
                    }
                    
                    if ip_str.starts_with("192.168.") || ip_str.starts_with("10.") {
                        // 对于这些私有地址，我们可以选择性保留
                        // 这里我们只保留看起来像是主要网络接口的地址
                        // 比如10.5.3.67这样的地址可能是有用的
                        if ip_str == "10.5.3.67" {
                            addresses.push(ip_str);
                        }
                        continue;
                    }
                    
                    // 其他地址（可能是公网IP）都保留
                    addresses.push(ip_str);
                }
                get_if_addrs::IfAddr::V6(_) => {
                    // 暂时不处理IPv6地址
                    continue;
                }
            }
        }
    }
    
    addresses
}


// 根路由
async fn root() -> impl IntoResponse {
    Json(StatusResponse {
        status: "OK".to_string(),
    })
}


#[tokio::main]
async fn main() {
    // 加载环境变量
    dotenv().ok();
    
    // 获取调试模式
    let debug = env::var("debug").unwrap_or_else(|_| "False".to_string());
    let is_debug = debug.to_lowercase() == "true" || debug == "1" || debug == "t";

    // 创建基础应用
    let app = Router::new().route("/", get(root));

    // 使用初始化应用模块
    let app = magic::init_module(app);
    
    let listener = TcpListener::bind("0.0.0.0:2324").await.unwrap();
    
    println!("Starting server on all addresses (0.0.0.0)");
    println!("Debug mode: {}", is_debug);
    
    // 获取所有网络接口的IP地址显示后启动服务器
    let local_ips = get_local_ip_addresses();
    for ip in local_ips {
        println!(" * Running on http://{}:2324", ip);
    }

    axum::serve(listener, app).await.unwrap();
}
