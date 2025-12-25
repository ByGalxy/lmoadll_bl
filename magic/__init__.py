# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
主要的lmoadll的组件, 这是魔法()
"""

from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from magic.utils.TomlConfig import check_config_file
from magic.utils.Mail import init_mail, load_matl_config
from magic.utils.log2 import logger, _is_reload  # noqa: F401
from magic.PluginSystem import init_plugin_system
from magic.utils.jwt import InitJwtManager
from magic.routes.routes import combine_routes
from magic.PluginSystem import get_plugin_manager
import logging
import os


def Init_module(app: Flask) -> None:
    """初始化模块"""
    
    check_config_file()
    plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contents', 'plugin')
    plugin_manager = init_plugin_system(plugin_dir)
    plugin_manager.load_plugins()
    logging.info("插件系统初始化完成")

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    CORS(app, resources={r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": [],
            "max_age": 600
        }},
        allow_headers=["Content-Type","Authorization","X-Requested-With"],
        expose_headers=["X-RateLimit-Limit","X-RateLimit-Remaining","X-RateLimit-Reset"],
        supports_credentials=True,
        max_age=600)

    plugin_manager = get_plugin_manager()
    plugin_manager.register_all_api_routes(app)
    InitJwtManager(app)
    load_matl_config()
    init_mail(app)
    combine_routes(app)
