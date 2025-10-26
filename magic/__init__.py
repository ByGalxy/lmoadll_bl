# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
主要的lmoadll的组件, 这是魔法()
"""

from werkzeug.middleware.proxy_fix import ProxyFix
from magic.InitRouter import initrouter


def Init_module(app):
    """
    初始化模块

    Args:
        app: Flask应用实例
    """

    # 使用ProxyFix中间件获取客户端真实IP, 告诉Flask应用信任1层代理
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # 初始化JWT管理器
    try:
        from magic.utils.token import InitJwtManager

        InitJwtManager(app)
    except Exception as e:
        print(f"初始化JWT管理器失败: {e}")
    
    initrouter(app)
