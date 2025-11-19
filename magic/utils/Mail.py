# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""用于处理和加载 Mail 的操作"""

import tomllib
import logging
from flask_mail import Mail
from magic.utils.TomlConfig import CONFIG_PATH


mail = Mail()
MAIL_SENDER_NAME = "数数洞洞"
SMTP_CONFIG = {}


def load_matl_config():
    """加载邮箱配置""" 
    global MAIL_SENDER_NAME, SMTP_CONFIG
    default_username = ""
    
    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        if "smtp" in config and "MAIL_SENDER_NAME" in config["smtp"]:
            MAIL_SENDER_NAME = config["smtp"]["MAIL_SENDER_NAME"]
        
        # 构建SMTP配置
        SMTP_CONFIG = {
            'MAIL_SERVER': '',           # 默认SMTP服务器
            'MAIL_PORT': 465,            # 默认端口
            'MAIL_USERNAME': '',         # 默认用户名为空
            'MAIL_PASSWORD': '',         # 默认密码为空
            'MAIL_USE_SSL': True,        # 默认使用SSL
            'MAIL_USE_TLS': False        # 默认不使用TLS
        }
        
        if "smtp" in config and "SMTP_CONFIG" in config["smtp"]:
            smtp_config = config["smtp"]["SMTP_CONFIG"]
            
            # 更新每个配置项，但保留默认值
            for key, default_value in SMTP_CONFIG.items():
                if key in smtp_config:
                    SMTP_CONFIG[key] = smtp_config[key]
            
            # 获取用户名用于构建默认发送者
            default_username = smtp_config.get('MAIL_USERNAME', '')
            
            SMTP_CONFIG['MAIL_DEFAULT_SENDER'] = (MAIL_SENDER_NAME, default_username)
        
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
