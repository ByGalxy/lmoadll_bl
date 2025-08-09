from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

installRouter = APIRouter()

@installRouter.get("/")
def install():
    config_path = "config.toml"
    if not os.path.exists(config_path):
        return FileResponse("var/lmoadll/install/base/welcome.html")
    # 如果需要进一步处理配置文件，可以在这里添加代码
    pass