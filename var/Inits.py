# -*- coding: utf-8 -*-
import os



"""
初始化应用模块

Args:
    app: Flask应用实例
"""
def Init_module(app):    # 初始化JWT管理器
    try:
        from var.token import init_jwt_manager
        init_jwt_manager(app)
    except Exception as e:
        print(f'初始化JWT管理器失败: {e}')

    # 注册安装路由
    if os.path.exists('install.py'):
        from install import installRouter
        app.register_blueprint(installRouter)

    # 注册admin相关路由
    if os.path.exists('./admin'):
        from admin.index import adminRouter
        from admin.login import loginRouter
        from var.OAuth import authRouter
        app.register_blueprint(adminRouter)
        app.register_blueprint(loginRouter)
        app.register_blueprint(authRouter)
