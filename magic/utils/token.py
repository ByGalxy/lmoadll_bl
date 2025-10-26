# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
JWT Token 管理模块

该模块提供JWT token的创建、验证和管理功能,
用于应用程序的用户认证和会话管理。
"""

import secrets
from flask import request
from typing import Dict
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    verify_jwt_in_request,
    decode_token
)



__all__ = [
    'InitJwtManager',
    'CreateJwtToken',
    'GetCurrentUserIdentity'
]


def get_utc_now():
    """安全获取当前UTC时间"""
    return datetime.now(timezone.utc)


class JWTKeyManager:
    def __init__(self, rotation_days: int = 7, max_keys: int = 10):
        self.rotation_days = rotation_days
        self.max_keys = max_keys
        self.key_dict: Dict[str, datetime] = {} # {'6e969ed020840444240ab4c440fdb87d7b557bc070ea3a837d59345351075794': datetime.datetime(2025, 10, 22, 2, 55, 45, 225830, tzinfo=datetime.timezone.utc)}
        self._add_new_key()
    
    def _add_new_key(self) -> str:
        """添加新密钥到字典"""
        new_key = secrets.token_hex(32)
        self.key_dict[new_key] = get_utc_now()
        return new_key
    
    def _clean_old_keys(self):
        """清理过期密钥"""
        current_time = get_utc_now()
        expired_keys = []
        
        for key, created_time in self.key_dict.items():
            key_age = current_time - created_time
            if key_age.days > self.rotation_days:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.key_dict[key]
    
    def get_current_key(self) -> str:
        """获取当前有效密钥"""
        self._clean_old_keys()
        
        if not self.key_dict:
            return self._add_new_key()
        
        latest_key = max(self.key_dict.items(), key=lambda x: x[1])[0]
        return latest_key
    
    def get_all_valid_keys(self) -> list:
        """获取所有有效密钥"""
        self._clean_old_keys()
        return list(self.key_dict.keys())

    
jwt_key_manager = JWTKeyManager(rotation_days=7, max_keys=8)


def InitJwtManager(app):
    """初始化JWT管理器, 初始化JWT管理器并配置JWT相关设置"""

    if not app.config.get('JWT_SECRET_KEY'):
        app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
    
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    jwt = JWTManager(app)
    
    @jwt.encode_key_loader
    def encode_key_callback(identity):
        """编码时使用当前最新密钥"""
        return jwt_key_manager.get_current_key()
    
    @jwt.decode_key_loader
    def decode_key_callback(header, payload):
        """解码时智能选择密钥"""
        # 获取所有有效密钥
        valid_keys = jwt_key_manager.get_all_valid_keys()
        
        # 如果有令牌，尝试自动选择正确的密钥
        auth_header = request.headers.get('Authorization', '')
        cookie_token = request.cookies.get('access_token')
        
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # 去掉 "Bearer " 前缀
        elif cookie_token:
            token = cookie_token
        
        if token:
            # 尝试每个密钥来解码令牌
            for key in valid_keys:
                try:
                    # 使用PyJWT手动验证
                    import jwt as pyjwt
                    pyjwt.decode(token, key, algorithms=["HS256"], options={"verify_exp": False})
                    return key
                except pyjwt.InvalidTokenError:
                    continue
        
        # 如果没有令牌或者所有密钥都失败，返回当前密钥(让库自己处理错误)
        return jwt_key_manager.get_current_key()
    
    return jwt


def CreateJwtToken(identity, additional_claims=None):
    """创建访问令牌, 根据用户身份创建JWT访问令牌"""
    try:
        # 设置默认的额外声明
        if additional_claims is None:
            additional_claims = {
                'token_type': 'access',
                'created_at': get_utc_now().isoformat()
            }
        
        # 创建访问令牌
        # 这里不需要手动指定密钥，flask-jwt-extended会自动使用encode_key_loader回调
        access_token = create_access_token(
            identity=identity, 
            additional_claims=additional_claims
        )
        return access_token
    except Exception:
        # print(f"创建JWT令牌失败喵: {e}")
        return None


def GetCurrentUserIdentity():
    """获取当前用户身份, 支持Cookie和Header两种方式"""
    try:
        # 首先尝试标准的JWT验证（从Authorization头获取）
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity is not None:
                return identity
        except Exception:
            # Header验证失败，继续尝试cookie方式
            pass
        
        # 如果标准方式失败，尝试从cookie中获取令牌
        access_token = request.cookies.get('access_token')
        if access_token:
            try:
                decoded_token = decode_token(access_token)
                identity = decoded_token.get('sub')
                if identity:
                    return identity
                    
            except Exception:
                # 解码cookie令牌失败，继续
                pass
        
        # 所有方式都失败，返回None
        return None
        
    except Exception:
        # print(f"获取用户身份失败喵: {e}")
        return None
