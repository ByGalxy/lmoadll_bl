mod logger;
mod auth;
mod jwt;
mod cookies;
mod types;
mod middleware;
mod routes;
use actix_web::{App, HttpResponse, HttpServer, Responder, get};
use actix_web::middleware as actix_middleware;
use logger::init_logger;
use routes::modules::userRouter::user_routes;
use log::info;


#[get("/")]
async fn hello() -> impl Responder {
    HttpResponse::ExpectationFailed().body("Hello world")
}


#[actix_web::main]
async fn main() -> std::io::Result<()> {
    init_logger();
    let addr = ("127.0.0.1", 8080);
    info!("🚀 Server running at `http://{}:{}`", addr.0, addr.1);
    HttpServer::new(|| {
        App::new()
            .service(hello)
            .configure(user_routes)
            .wrap(actix_middleware::Logger::default())
    })
        .bind(addr)?
        .run()
        .await
}
