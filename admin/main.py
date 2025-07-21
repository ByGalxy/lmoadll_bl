from fastapi import FastAPI, Request
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from logs import setup_logging

app = FastAPI(title="Admin Panel")

admin_server_thread = None

# 挂载静态文件
app.mount("/static", StaticFiles(directory="admin/static"), name="static")

# 初始化模板
templates = Jinja2Templates(directory="admin/html")

@app.get("/")
async def admin_dashboard(request: Request):
    # 可以在这里传递数据到模板，如已加载的插件、统计信息等
    return templates.TemplateResponse("index.html", {"request": request, "title": "管理面板"})

def start_admin_server():
    log_config = setup_logging()
    # 修复信号错误：在主线程启动Uvicorn
    import sys
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    uvicorn.run(
        "admin.main:app",
        host="127.0.0.1",
        port=8003,
        log_level="info",
        log_config=log_config,
        reload=False  # Windows环境下主线程不支持reload
    )

# 挂载静态文件
app.mount("/static", StaticFiles(directory="admin/static"), name="static")

# 初始化模板
templates = Jinja2Templates(directory="admin/html")

@app.get("/")
async def admin_dashboard(request: Request):
    # 可以在这里传递数据到模板，如已加载的插件、统计信息等
    return templates.TemplateResponse("index.html", {"request": request, "title": "管理面板"})