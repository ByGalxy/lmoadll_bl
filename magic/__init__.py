# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
主要的lmoadll的组件, 这是魔法()
"""

import pathlib
import tomllib
from tomli_w import dump
from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix
from magic.InitRouter import initrouter


mail = Mail()
MAIL_SENDER_NAME = "数数洞洞"
SMTP_CONFIG = {}
CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config.toml" # 配置文件路径


def check_config_file():
    """检查config.toml是否存在, 如果不存在则创建默认配置"""
    if not CONFIG_PATH.exists():
        default_config = {
            "server": {
                "install": False
            }
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "wb") as f:
            dump(default_config, f)


def load_matl_config():
    """加载邮箱配置""" 
    global MAIL_SENDER_NAME, SMTP_CONFIG
    
    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        if "smtp" in config and "MAIL_SENDER_NAME" in config["smtp"]:
            MAIL_SENDER_NAME = config["smtp"]["MAIL_SENDER_NAME"]
        
        if "smtp" in config and "SMTP_CONFIG" in config["smtp"]:
            smtp_config = config["smtp"]["SMTP_CONFIG"]
            SMTP_CONFIG = {
                'MAIL_SERVER': smtp_config.get('MAIL_SERVER', 'smtp.qq.com'),
                'MAIL_PORT': smtp_config.get('MAIL_PORT', 465),
                'MAIL_USERNAME': smtp_config.get('MAIL_USERNAME', ''),
                'MAIL_PASSWORD': smtp_config.get('MAIL_PASSWORD', ''),
                'MAIL_DEFAULT_SENDER': (MAIL_SENDER_NAME, smtp_config.get('MAIL_USERNAME', '')),
                'MAIL_USE_SSL': smtp_config.get('MAIL_USE_SSL', True),
                'MAIL_USE_TLS': smtp_config.get('MAIL_USE_TLS', False)
            }
    except Exception as e:
        print(f"加载配置文件失败: {e}")


def Init_module(app: Flask) -> None:
    """初始化模块"""
    
    check_config_file()
    load_matl_config()

    # 使用ProxyFix中间件获取客户端真实IP, 告诉Flask应用信任1层代理
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    CORS(app, 
        resources={r"/api/*": {
            "origins": ["http://127.0.0.1:5500", "http://localhost:5500"],
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": [],
            "max_age": 600
        }},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=[],
        max_age=600)


    # 初始化JWT管理器
    try:
        from magic.utils.token import InitJwtManager
        
        InitJwtManager(app)
    except Exception as e:
        print(f"初始化JWT管理器失败: {e}")
    

    # 初始化邮件服务
    try:
        for key, value in SMTP_CONFIG.items():
            app.config[key] = value

        app.config['MAIL_DEBUG'] = False
        
        mail.init_app(app)
    except Exception as e:
        print(f"初始化Flask-Mail失败: {e}")
    
    initrouter(app)
