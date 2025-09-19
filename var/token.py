"""
-*- coding: utf-8 -*-
JWT Token 管理模块

该模块提供JWT token的创建、验证和管理功能,
用于应用程序的用户认证和会话管理。
"""

from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended import decode_token
from datetime import timedelta
import secrets



__all__ = ['init_jwt_manager', 'create_jwt_token', 'get_current_user_identity', 'jwt_required']


"""
初始化JWT管理器
初始化JWT管理器并配置JWT相关设置
"""
def init_jwt_manager(app):
    # 使用随机生成的密钥提高安全性
    if not app.config.get('JWT_SECRET_KEY'):
        app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
    
    # 设置JWT令牌过期时间
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    # 创建JWT管理器实例
    jwt = JWTManager(app)
    
    # 可以在这里添加JWT相关的回调函数，例如token过期处理等
    
    return jwt


"""
创建访问令牌
根据用户身份创建JWT访问令牌
"""
def create_jwt_token(identity):
    try:
        # 可以添加额外的令牌声明
        additional_claims = {
            # 例如：'user_type': user_type
        }
        
        # 创建访问令牌，有效期可以通过current_app.config['JWT_ACCESS_TOKEN_EXPIRES']配置
        access_token = create_access_token(identity=identity, additional_claims=additional_claims)
        return access_token
    except Exception as e:
        print(f"创建JWT令牌失败: {e}")
        return None


"""
获取当前用户身份
获取当前登录用户的身份信息
"""
def get_current_user_identity():
    
    try:
        # 尝试从cookie中获取令牌
        access_token = request.cookies.get('access_token')
        
        if not access_token:
            # 如果cookie中没有令牌，尝试使用verify_jwt_in_request作为备选方案
            verify_jwt_in_request(optional=True)
            return get_jwt_identity()

        # 解码令牌获取身份信息
        decoded_token = decode_token(access_token)
        return decoded_token.get('sub')
    except Exception as e:
        print(f"获取用户身份失败: {e}")
        return None
