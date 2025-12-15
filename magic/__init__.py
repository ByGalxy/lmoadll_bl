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
from magic.InitRouter import initrouter
from magic.utils.TomlConfig import check_config_file
from magic.utils.Mail import load_matl_config, SMTP_CONFIG, mail
from magic.utils.log2 import logger, _is_reload  # noqa: F401
from magic.PluginSystem import init_plugin_system
import logging
import os


def Init_module(app: Flask) -> None:
    """初始化模块"""
    
    check_config_file()
    load_matl_config()
    
    plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contents', 'plugin')
    plugin_manager = init_plugin_system(plugin_dir)
    plugin_manager.load_plugins()
    logging.info("插件系统初始化完成")

    # 使用ProxyFix中间件获取客户端真实IP, 告诉Flask应用信任1层代理
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

    try:
        from magic.utils.token import InitJwtManager
        
        InitJwtManager(app)
    except Exception as e:
        logging.error(f"初始化JWT管理器失败: {e}")

    try:
        for key, value in SMTP_CONFIG.items():
            app.config[key] = value
        app.config['MAIL_DEBUG'] = False
        mail.init_app(app)
    except Exception as e:
        logging.error(f"初始化Flask-Mail失败: {e}")
    
    initrouter(app)
