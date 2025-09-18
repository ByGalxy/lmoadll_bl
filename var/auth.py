"""
-*- coding: utf-8 -*-
认证模块

该模块提供用户登录功能, 包括用户验证、密码校验和JWT令牌生成.
"""

from flask import Blueprint, request, jsonify
from var.argon2_password import verify_password
from var.token import create_jwt_token
from var.toml_config import Doesitexist_configtoml
from var.sql.sqlite.sqlite import get_user_by_username_or_email



authRouter = Blueprint('lauth', __name__, url_prefix='/lauth')


"""
处理登录请求, 验证用户凭据并生成JWT令牌

请求格式：
POST /lauth/login
{
    "username_or_email": "用户输入的用户名或邮箱",
    "password": "用户输入的密码"
}

响应格式：
成功: {"code": 200, "message": "登录成功", "access_token": "JWT令牌"}
失败: {"code": 错误码, "message": "错误信息"}
"""
@authRouter.route('/login', methods=['POST'])
def login_api():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据为空"}), 400
        
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        
        # 验证输入参数
        if not username_or_email or not password:
            return jsonify({"code": 400, "message": "用户名/邮箱和密码不能为空"}), 400
        
        # 从配置中获取数据库信息
        try:
            db_prefix = Doesitexist_configtoml('db', 'sql_prefix')
            sql_sqlite_path = Doesitexist_configtoml('db', 'sql_sqlite_path')
            
            if not db_prefix or not sql_sqlite_path:
                return jsonify({"code": 500, "message": "数据库配置缺失"}), 500
        except Exception as e:
            return jsonify({"code": 500, "message": f"读取配置失败: {str(e)}"}), 500
        
        # 获取用户信息
        user = get_user_by_username_or_email(db_prefix, sql_sqlite_path, username_or_email)
        if not user:
            return jsonify({"code": 401, "message": "用户名/邮箱或密码错误"}), 401
        
        # 验证密码
        if not verify_password(user['password'], password):
            return jsonify({"code": 401, "message": "用户名/邮箱或密码错误"}), 401
        
        # 生成JWT令牌，使用用户ID作为identity
        access_token = create_jwt_token(identity=user['uid'])
        if not access_token:
            return jsonify({"code": 500, "message": "生成令牌失败"}), 500
        
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "access_token": access_token,
            "user_info": {
                "uid": user['uid'],
                "username": user['name'],
                "email": user['email'],
                "group": user['group']
            }
        }), 200
        
    except Exception as e:
        print(f"登录过程中出现错误: {e}")
        return jsonify({"code": 500, "message": f"登录失败: {str(e)}"}), 500


"""
POST /lauth/logout
处理登出请求
注意: JWT是无状态的, 客户端应该删除存储的令牌
JWT是无状态的, 服务器端不需要特殊处理
客户端应该删除存储的令牌
"""
@authRouter.route('/logout', methods=['POST'])
def logout():
    try:
        return jsonify({"code": 200, "message": "登出成功"}), 200
    except Exception as e:
        print(f"登出过程中出现错误: {e}")
        return jsonify({"code": 500, "message": f"登出失败: {str(e)}"}), 500
