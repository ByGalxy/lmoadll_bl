from fastapi import APIRouter
from fastapi.responses import FileResponse
from flask import Blueprint
import os

installRouter = Blueprint('install', __name__, url_prefix='/install')

@installRouter.get("/")
def install():
    config_path = "config.toml"
    if not os.path.exists(config_path):
        return FileResponse("var/lmoadll/install/base/welcome.html")
    pass

@installRouter.post("")
def get_install_Check_connection():
    pass
