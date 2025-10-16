# -*- coding: utf-8 -*-
import os
from werkzeug.middleware.proxy_fix import ProxyFix




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
        from var.token import InitJwtManager
        InitJwtManager(app)
    except Exception as e:
        print(f'初始化JWT管理器失败: {e}')


    # 注册install路由
    if os.path.exists('install/install.py'):
        from install.install import installRouter
        app.register_blueprint(installRouter)


    # 注册admin相关路由
    if os.path.exists('./admin'):
        from admin.admin import adminRouter
        from admin.login import loginRouter
        from var.auth import authRouter
        app.register_blueprint(adminRouter)
        app.register_blueprint(loginRouter)
        app.register_blueprint(authRouter)


    # 注册var路由
    if os.path.exists('./var'):
        from var.asses import assetsRouter
        app.register_blueprint(assetsRouter)
