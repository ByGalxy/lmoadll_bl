"""
-*- coding: utf-8 -*-

lmoadll_bl platform

@copyright  Copyright (c) 2025 lmoadll_bl team
@license  GNU General Public License 3.0

"""

from flask import Flask
import os

app = Flask(__name__)

# 初始化JWT管理器
try:
    from var.lmoadll.token import init_jwt_manager
    jwt = init_jwt_manager(app)
except Exception as e:
    print(f'初始化JWT管理器失败: {e}')

if os.path.exists('install.py'):
    from install import installRouter
    app.register_blueprint(installRouter)


if os.path.exists('./admin'):
    from admin.index import adminRouter
    from admin.login import loginRouter
    from var.lmoadll.auth import authRouter
    app.register_blueprint(adminRouter)
    app.register_blueprint(loginRouter)
    app.register_blueprint(authRouter)


@app.get('/')
def root():
   return {'Status': 'OK'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2324, debug=False, threaded=True)
