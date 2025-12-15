# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
from flask import Flask


def initrouter(app: Flask) -> None:
    from admin.install import install_bp
    app.register_blueprint(install_bp)

    from admin import admin_bp
    from admin.login import login_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(login_bp)

    from magic.asses import assets_bp
    app.register_blueprint(assets_bp)

    from magic.api import api_bp
    app.register_blueprint(api_bp)
