# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0


import os
from flask import Flask


def initrouter(app: Flask) -> None:
    if os.path.exists("admin/install.py"):
        from admin.install import install_bp
        app.register_blueprint(install_bp)

    # 注册admin相关路由
    if os.path.exists("./admin"):
        from admin import admin_bp
        from admin.login import login_bp
        app.register_blueprint(admin_bp)
        app.register_blueprint(login_bp)

    # 注册magic路由
    if os.path.exists("./magic"):
        from magic.asses import assets_bp
        app.register_blueprint(assets_bp)

    # 注册api
    from magic.lmoadll import api_bp
    app.register_blueprint(api_bp)
