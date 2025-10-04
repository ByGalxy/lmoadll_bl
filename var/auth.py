"""
-*- coding: utf-8 -*-
认证模块

该模块提供用户登录功能, 包括用户验证、密码校验和JWT令牌生成.
"""

from flask import Blueprint, request, jsonify, redirect, url_for
from functools import wraps
from var.argon2_password import verify_password
from var.token import create_jwt_token, get_current_user_identity
from var.toml_config import Doesitexist_configtoml
from var.sql.sqlite.sqlite import get_user_by_username_or_email



authRouter = Blueprint('auth', __name__, url_prefix='/auth')


"""
P22
登录验证装饰器
检查用户是否已登录，未登录则重定向到登录页面
"""
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 尝试获取当前用户身份
        user_identity = get_current_user_identity()
        if user_identity is None:
            # 获取当前请求的路径部分作为原始页面
            original_path = request.path
            # 如果存在查询参数，也一并传递
            if request.query_string:
                original_path = f"{original_path}?{request.query_string.decode('utf-8')}"
            # 重定向到登录页面，并传递原始页面路径作为查询参数
            return redirect(url_for('login.login_page', redirect=original_path))
        # 用户已登录，继续执行原函数
        return f(*args, **kwargs)
    return decorated_function


"""
处理登录请求, 验证用户凭据并生成JWT令牌

请求格式：
POST /auth/login
{
    "username_or_email": "用户输入的用户名或邮箱",
    "password": "用户输入的密码"
}

响应格式：
成功: {"code": 200, "message": "登录成功", "user_info": {用户信息}}
失败: {"code": 错误码, "message": "错误信息"}
注意: JWT令牌通过cookie传递, 不在响应JSON中包含
"""
@authRouter.route('/login', methods=['POST'])
def login_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据为空"}), 400
        
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        
        if not username_or_email or not password:
            return jsonify({"code": 400, "message": "用户名/邮箱和密码不能为空"}), 400

        try:
            db_prefix = Doesitexist_configtoml('db', 'sql_prefix')
            sql_sqlite_path = Doesitexist_configtoml('db', 'sql_sqlite_path')
            
            if not db_prefix or not sql_sqlite_path:
                return jsonify({"code": 500, "message": "数据库配置缺失"}), 500
        except Exception as e:
            return jsonify({"code": 500, "message": f"读取配置失败: {str(e)}"}), 500
        
        user = get_user_by_username_or_email(db_prefix, sql_sqlite_path, username_or_email)
        if not user:
            return jsonify({"code": 401, "message": "用户名/邮箱或密码错误"}), 401
        
        if not verify_password(user['password'], password):
            return jsonify({"code": 401, "message": "用户名/邮箱或密码错误"}), 401
        
        # 生成JWT令牌，确保用户ID是字符串类型
        access_token = create_jwt_token(identity=str(user['uid']))
        if not access_token:
            return jsonify({"code": 500, "message": "生成令牌失败"}), 500
        
        # 设置JWT令牌到cookie中，设置httponly防止XSS攻击
        response = jsonify({
            "code": 200,
            "message": "登录成功"
        })
        
        # 设置cookie，不设置过期时间使它成为会话cookie
        # 当token过期时，用户需要重新登录，新生成的token会自动覆盖旧token
        response.set_cookie(
            'access_token', 
            access_token,
            httponly=True,
            secure=True,# 开发环境可以设为False，生产环境应设为True
            samesite='Lax'
        )

        return response, 200
        
    except Exception as e:
        print(f"登录过程中出现错误: {e}")
        return jsonify({"code": 500, "message": f"登录失败: {str(e)}"}), 500


"""
POST /auth/logout
处理登出请求
注意: JWT是无状态的, 客户端应该删除存储的令牌
JWT是无状态的, 服务器端不需要特殊处理
客户端应该删除存储的令牌
"""
@authRouter.route('/logout', methods=['GET'])
def logout():
    try:
        # 创建响应对象
        response = jsonify({"code": 200, "message": "登出成功"})
        
        # 清除cookie中的令牌
        response.delete_cookie('access_token')
        
        # 可选：清除localStorage中的用户信息（在前端处理）
        return response, 200
    except Exception as e:
        print(f"登出过程中出现错误: {e}")
        return jsonify({"code": 500, "message": f"登出失败: {str(e)}"}), 500
