from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

installRouter = APIRouter()

@installRouter.get("/")
def install():
    config_path = "config.toml"
    if not os.path.exists(config_path):
        return FileResponse("var/lmoadll/install/base/welcome.html")
    pass

@installRouter.post("")
def get_install_Check_connection():
    pass