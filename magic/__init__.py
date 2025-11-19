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
from magic.utils.log2 import logger  # noqa: F401
import logging


def Init_module(app: Flask) -> None:
    """初始化模块"""
    
    check_config_file()
    load_matl_config()

    # 使用ProxyFix中间件获取客户端真实IP, 告诉Flask应用信任1层代理
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    CORS(app, 
        resources={r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": [],
            "max_age": 600
        }},
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Requested-With"
        ],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ],
        supports_credentials=True,
        max_age=600)


    # 初始化JWT管理器
    try:
        from magic.utils.token import InitJwtManager
        
        InitJwtManager(app)
    except Exception as e:
        logging.error(f"初始化JWT管理器失败: {e}")
    

    # 初始化邮件服务
    try:
        for key, value in SMTP_CONFIG.items():
            app.config[key] = value

        app.config['MAIL_DEBUG'] = False
        
        mail.init_app(app)
    except Exception as e:
        logging.error(f"初始化Flask-Mail失败: {e}")
    
    initrouter(app)
