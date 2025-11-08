# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
认证模块

该模块提供用户登录功能, 包括用户验证、密码校验和JWT令牌生成.
"""

from flask import Blueprint, request, jsonify, redirect, url_for
from functools import wraps
from magic.utils.Argon2Password import VerifyPassword
from magic.utils.token import CreateTokens, RefreshToken, GetCurrentUserIdentity
from magic.utils.TomlConfig import DoesitexistConfigToml
from magic.utils.LmoadllOrm import GetUserByEmail



auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """
    登录验证装饰器
    ==============================
    检查用户是否已登录, 未登录则重定向到登录页面

    获取用户身份和get路径中的查询参数, 如果用户已登录执行原有函数否则重定向登录页面
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_identity = GetCurrentUserIdentity()
        if user_identity is None:
            original_path = request.path
            if request.query_string:
                original_path = f"{original_path}?{request.query_string.decode('utf-8')}"
            return redirect(url_for('login.login_page', redirect=original_path))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login_api():
    """
    处理登录请求, 验证用户凭据并生成JWT令牌

    请求格式：
    ```
    POST /api/auth/login
    {
        "username_email": "用户输入的邮箱",
        "password": "用户输入的密码"
    }
    ```

    响应格式：
        成功: {"code": 200, "message": "登录成功", "user_info": {用户信息}}
        失败: {"code": 错误码, "message": "错误信息"}
        注意: JWT令牌通过cookie传递, 不在响应JSON中包含
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据为空喵喵"}), 400
        
        username_email = data.get('username_email')
        password = data.get('password')
        
        if not username_email or not password:
            return jsonify({"code": 400, "message": "邮箱和密码不能为空喵喵"}), 400

        try:
            db_prefix = DoesitexistConfigToml('db', 'sql_prefix')
            sql_sqlite_path = DoesitexistConfigToml('db', 'sql_sqlite_path')
            
            if not db_prefix or not sql_sqlite_path:
                return jsonify({"code": 500, "message": "数据库配置缺失喵喵"}), 500
        except Exception as e:
            return jsonify({"code": 500, "message": f"读取配置失败喵喵: {str(e)}"}), 500
        
        user = GetUserByEmail(db_prefix, sql_sqlite_path, username_email)
        if not user:
            return jsonify({"code": 401, "message": "邮箱或密码错误喵喵"}), 401
        
        if not VerifyPassword(user['password'], password):
            return jsonify({"code": 401, "message": "邮箱或密码错误喵喵"}), 401
        
        # 生成双令牌，确保用户ID是字符串类型
        tokens = CreateTokens(identity=str(user['uid']))
        if not tokens:
            return jsonify({"code": 500, "message": "生成令牌失败喵喵"}), 500
        
        access_token = tokens['lmoadllUser']
        refresh_token = tokens['lmoadll_refresh_token']
        
        # 从配置中获取access token过期时间(分钟)
        access_expires_in = 15  # 默认15分钟
        
        # 设置JWT令牌到cookie中，设置httponly防止XSS攻击
        # 安全改进：不在JSON响应中返回token，只通过cookie传递
        response = jsonify({
            "code": 200,
            "message": "登录成功喵",
            "expires_in": access_expires_in * 60  # 转换为秒
        })
        
        """
        设置cookie, 不设置过期时间使它成为会话cookie
        当token过期时, 用户需要重新登录, 新生成的token会自动覆盖旧token
        secure:
            https协议传输, 打开后如果不是HTTPS连接, 浏览器会拒绝保存带有secure=True的Cookie.
            如果开发环境, 发现浏览器保存Cookie, 请检查是否开启了secure选项.
            如果是生产环境, 网站建议使用HTTPS协议并打开secure选项.
        """
        # 存储lmoadll_refresh_token到cookie，访问受限制
        # 安全改进：设置SameSite为Strict
        response.set_cookie(
            'lmoadll_refresh_token', 
            refresh_token,
            httponly=True,
            secure=True,
            samesite='Strict'
        )
        
        # 存储lmoadllUser到cookie，方便前端自动携带
        # 安全改进：设置SameSite为Strict
        response.set_cookie(
            'lmoadllUser', 
            access_token,
            httponly=True,
            secure=True,
            samesite='Strict'
        )

        return response, 200
        
    except Exception as e:
        print(f"登录过程中出现错误喵: {e}")
        return jsonify({"code": 500, "message": f"登录失败: {str(e)}"}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh_api():
    """
    POST /api/auth/refresh
      
     使用lmoadll_refresh_token刷新access token
     
     请求格式：仅接受从cookie中获取lmoadll_refresh_token
    
    响应格式：
    成功: {"code": 200, "message": "令牌刷新成功", "expires_in": 900}
    失败: {"code": 错误码, "message": "错误信息"}
    """
    try:
        # 安全改进：仅从cookie中获取refresh token，移除从请求体获取的路径
        refresh_token = request.cookies.get('lmoadll_refresh_token')
        
        if not refresh_token:
            return jsonify({"code": 400, "message": "缺少lmoadll_refresh token喵喵"}), 400
        
        # 刷新access token，传入请求上下文以进行额外验证
        new_access_token = RefreshToken(refresh_token, request)
        if not new_access_token:
            return jsonify({"code": 401, "message": "无效的refresh token喵喵"}), 401
        
        # 从配置中获取access token过期时间（分钟）
        access_expires_in = 15  # 默认15分钟
        
        # 安全改进：不在JSON响应中返回token
        response = jsonify({
            "code": 200,
            "message": "令牌刷新成功喵",
            "expires_in": access_expires_in * 60  # 转换为秒
        })
        
        # 更新cookie中的lmoadllUser
        response.set_cookie(
            'lmoadllUser', 
            new_access_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        
        return response, 200
    except Exception as e:
        print(f"刷新令牌过程中出现错误喵: {e}")
        return jsonify({"code": 500, "message": f"刷新失败: {str(e)}"}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /api/auth/logout
    
    处理登出请求
    - 清除cookie中的access_token和refresh_token
    - 客户端也应该删除本地存储的令牌
    """
    try:
        response = jsonify({"code": 200, "message": "登出成功喵"})
        
        response.delete_cookie('lmoadllUser')
        response.delete_cookie('lmoadll_refresh_token')
        
        return response, 200
    except Exception as e:
        print(f"登出过程中出现错误喵: {e}")
        return jsonify({"code": 500, "message": f"登出失败: {str(e)}"}), 500
