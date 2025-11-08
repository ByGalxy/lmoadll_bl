/// 主要的lmoadll的组件, 这是魔法()

mod lmoadll;
use axum::Router;


/// 初始化模块
pub fn init_module(app: Router) -> Router {
    // 初始化JWT管理器（待实现）
    let app = init_jwt_manager(app);
    
    // 初始化路由
    let app = init_router(app);
    
    app
}


/// 初始化JWT管理器
fn init_jwt_manager(app: Router) -> Router {
    // TODO: 实现JWT管理器
    // 目前先返回原始应用
    app
}


/// 初始化路由
fn init_router(app: Router) -> Router {
    // 注册admin相关路由
    let app = app
        .nest("/admin", admin_routes())
        .nest("/api", api_routes());
    
    app
}


/// Admin路由
fn admin_routes() -> Router {
    Router::new()
        // TODO: 实现admin相关路由
}


/// API路由
fn api_routes() -> Router {
    Router::new()
        // TODO: 实现API路由
}
