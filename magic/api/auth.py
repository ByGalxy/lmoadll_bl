# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
认证模块

该模块提供用户登录功能, 包括用户验证、密码校验和JWT令牌生成.
"""

import random
import re
import string
import time
import logging
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_mail import Message
from functools import wraps
from magic import mail, SMTP_CONFIG
from magic.utils.Argon2Password import VerifyPassword, HashPassword
from magic.utils.token import CreateTokens, GetCurrentUserIdentity
from magic.utils.TomlConfig import DoesitexistConfigToml
from magic.utils.db import db_orm, GetUserByEmail, GetDbConnection
from magic.PluginSystem import call_plugin_hook


verification_codes = {}     # {email: {"code": 验证码, "hash": 验证码哈希, "expires_at": 过期时间戳}}
CODE_EXPIRATION_TIME = 300  # 验证码有效期(秒)
auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """登录验证装饰器

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


def verify_code(email, code):
    """验证验证码是否有效
    
    Args:
        email: 用户邮箱
        code: 用户输入的验证码
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    cleanup_expired_codes()
    
    if email not in verification_codes:
        return False, "验证码不存在或已过期"
    
    code_data = verification_codes[email]
    
    if int(time.time()) > code_data['expires_at']:
        del verification_codes[email]
        return False, "验证码已过期"
    
    if code != code_data['code']:
        return False, "验证码错误"
    
    del verification_codes[email]
    return True, None


def cleanup_expired_codes():
    """清理过期的验证码
    """
    current_time = int(time.time())
    expired_emails = [email for email, data in verification_codes.items() 
                     if data['expires_at'] < current_time]
    
    for email in expired_emails:
        del verification_codes[email]
    
    if expired_emails:
        logging.info(f"已清理 {len(expired_emails)} 个过期的验证码")


@auth_bp.route('/login', methods=['POST'])
def login_api():
    """处理登录请求, 验证用户凭据并生成JWT令牌

    请求格式：
    ```
    POST /api/auth/login
    {
        "username_email": "用户输入的邮箱",
        "password": "用户输入的密码"
    }
    ```

    响应格式：
        成功: `{"code": 200, "message": "登录成功", "user_info": {用户信息}}`
        失败: `{"code": 错误码, "message": "错误信息"}`
        注意: `JWT令牌通过cookie传递, 不在响应JSON中包含`
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据为空喵喵"}), 400
        
        if not data["username_email"] or not data["password"]:
            return jsonify({"code": 400, "message": "邮箱和密码不能为空喵喵"}), 400
        
        user = GetUserByEmail(data["username_email"])
        if not user:
            return jsonify({"code": 401, "message": "邮箱或密码错误喵喵"}), 401
        
        if not VerifyPassword(user['password'], data["password"]):
            return jsonify({"code": 401, "message": "邮箱或密码错误喵喵"}), 401
        
        # 生成令牌
        tokens = CreateTokens(identity=str(user['uid']))
        if not tokens:
            return jsonify({"code": 500, "message": "生成令牌失败喵喵"}), 500

        # access_token = tokens['lmoadllUser']
        refresh_token = tokens['lmoadll_refresh_token']

        response = jsonify({
            "code": 200,
            "message": "登录成功喵",
            "data": {
                "uid": user['uid'],
                "name": user['name'],
                "avatar": "",
                "group": user['group']
            }
        })
        
        """
        设置cookie, 不设置过期时间使它成为会话cookie
        当token过期时, 用户需要重新登录, 新生成的token会自动覆盖旧token
        secure:
            https协议传输, 打开后如果不是HTTPS连接, 浏览器会拒绝保存带有secure=True的Cookie.
            如果开发环境, 发现浏览器保存Cookie, 请检查是否开启了secure选项.
            如果是生产环境, 网站建议使用HTTPS协议并打开secure选项.
        """
        response.set_cookie(
            'lmoadll_refresh_token',
            refresh_token,
            httponly=True,            # 防止XSS攻击
            secure=True,              # 仅HTTPS传输
            samesite='None',          # 允许跨站使用
            max_age=30*24*60*60       # 30天过期时间
        )
        
        # response.set_cookie(
        #     'lmoadllUser',
        #     access_token,
        #     httponly=True,           # 防止XSS攻击
        #     secure=True,             # 仅HTTPS传输
        #     samesite='None',         # 允许跨站使用
        #     max_age=15*60            # 15分钟过期时间
        # )

        try:
            # 获取数据库连接
            db = db_orm.get_db("default")
            # 获取表名
            success, message, _, _, table_name = GetDbConnection("users")
            if success:
                current_time = int(time.time())  # 获取当前时间戳
                # 使用同一个连接执行更新操作
                db.execute(f"UPDATE {table_name} SET lastLogin = ? WHERE uid = ?", (current_time, user['uid']))
                db.commit()
        except Exception as e:
            logging.warning(f"更新用户最后登录时间失败喵: {e}")
        finally:
            # 确保连接被归还到连接池
            try:
                db_orm.return_db(db, "default")
            except:
                pass

        return response
        
    except Exception as e:
        logging.error(f"登录过程中出现错误喵: {e}")
        return jsonify({"code": 500, "message": f"登录失败: {str(e)}"}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /api/auth/logout
    
    处理登出请求
    - 清除cookie中的access_token和refresh_token
    - 客户端也应该删除本地存储的令牌

    响应格式：
    * 成功: `{"code": 200, "message": "登出成功喵"}`
    * 失败: `{"code": 500, "message": "错误信息"}`
    """
    try:
        response = jsonify({"code": 200, "message": "登出成功喵"})
        
        # response.delete_cookie('lmoadllUser')
        response.delete_cookie('lmoadll_refresh_token')
        
        return response, 200
    except Exception as e:
        logging.error(f"登出过程中出现错误喵: {e}")
        return jsonify({"code": 500, "message": "登出失败喵"}), 500


@auth_bp.route('user', methods=['GET'])
def user_api():
    """获取用户的数据信息
    GET /api/auth/user

    响应格式:

    成功:
    ```
    {
    "code": 200,
    "data":{
        "uid": "1",
        "name": "神秘的绿",
        "email": "xxxxx@xxx.xxx"
        }
    }
    ```

    错误:
    ```
    {
        "code": 401,
        "message": "用户未登录喵喵"
    }
    ```
    """
    try:
        user_identity = GetCurrentUserIdentity()

        if user_identity is None:
            return jsonify({"code": 401, "message": "用户未登录喵喵"}), 401
        
        success, message, db, cursor, table_name = GetDbConnection("users")
        if not success:
            return jsonify({"code": 500, "message": f"数据库连接失败喵喵: {message}"}), 500
        
        try:
            # 查询用户详细信息
            cursor.execute(f"SELECT uid, name, mail, createdAt, lastLogin FROM {table_name} WHERE uid = ?", (user_identity,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({"code": 404, "message": "用户不存在喵喵"}), 404
            
            # 使用插件获取用户信息
            user_info_results = call_plugin_hook("user_info_get", user_identity)
            user_meta = {}
            for result in user_info_results:
                if result and isinstance(result, dict):
                    user_meta.update(result)
            
            user_info = {
                "uid": user[0],
                "name": user[1],
                "email": user[2],
                "RegisterTime": user[3],
                "LastLoginTime": user[4],
                **user_meta
            }

            return jsonify({
                "code": 200,
                "data": user_info
            }), 200
            
        except Exception as e:
            logging.error(f"查询用户信息时出错喵: {e}")
            return jsonify({"code": 500, "message": "查询用户信息失败喵喵"}), 500
            
        finally:
            if db:
                db_orm.return_db(db, "default")
                
    except Exception as e:
        logging.error(f"获取用户信息过程中出现错误喵: {e}")
        return jsonify({"code": 500, "message": "服务器内部错误喵喵"}), 500


@auth_bp.route('/register', methods=['POST'])
def register_api():
    """注册新用户

    请求格式：
    ```
    POST /api/auth/register
    {
        "code": "验证码",
        "codeSalt": "验证码哈希",
        "email":    "新用户邮箱",
        "username": "新用户名",
        "password": "新用户密码"
    }
    ```
    
    响应格式：

    成功: 
    ```
    {
        "code": 200, "uid": "用户的UID", "name": "用户名", "avatar": "用户头像URL", "avatarMin": "用户头像URL-小", 
        "moemoepoint": "用户记忆点", "role": "用户角色", "isChechIn": false, "dailyToolsetUploadCount": 0
    }
    ```
    失败:
    ```
    {"code": 错误码, "message": "错误信息"}
    ```
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据为空喵喵"}), 400
        
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        code = data.get('code')
        code_salt = data.get('codeSalt')
        
        if not email or not username or not password or not code or not code_salt:
            return jsonify({"code": 400, "message": "邮箱、用户名、密码、验证码和验证码哈希都不能为空喵喵"}), 400
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"code": 400, "message": "邮箱格式不正确喵喵"}), 400
        
        if len(username) < 2 or len(username) > 50:
            return jsonify({"code": 400, "message": "用户名长度应在2-50个字符之间喵喵"}), 400
        
        if len(password) < 8:
            return jsonify({"code": 400, "message": "密码长度应不少于8个字符喵喵"}), 400
        
        if len(code) != 6:
            return jsonify({"code": 400, "message": "验证码应为6位字母+数字喵喵"}), 400
        
        try:
            db_prefix = DoesitexistConfigToml('db', 'sql_prefix')
            sql_sqlite_path = DoesitexistConfigToml('db', 'sql_sqlite_path')
            
            if not db_prefix or not sql_sqlite_path:
                print("数据库配置缺失: db_prefix或sql_sqlite_path为空")
                return jsonify({"code": 500, "message": "数据库配置缺失喵喵"}), 500
        except Exception as e:
            logging.error(f"读取配置文件时出错: {str(e)}")
            return jsonify({"code": 500, "message": "读取配置失败喵喵"}), 500
        
        try:
            user = GetUserByEmail(email)
            if user:
                return jsonify({
                    "code": 400,
                    "message": "该邮箱已被注册喵喵"
                }), 400
        except Exception as e:
            logging.error(f"检查邮箱是否已存在时出错喵喵: {str(e)}")
            return jsonify({"code": 500, "message": "数据库查询失败喵喵"}), 500
        
        if email not in verification_codes:
            print(verification_codes)
            return jsonify({"code": 400, "message": "验证码不存在或已过期喵喵"}), 400
        
        code_data = verification_codes[email]
        
        if int(time.time()) > code_data['expires_at']:
            del verification_codes[email]
            return jsonify({"code": 400, "message": "验证码已过期喵喵"}), 400
        
        if not VerifyPassword(code_data['hash'], code):
            return jsonify({"code": 400, "message": "验证码错误喵喵"}), 400
        
        if code_data['hash'] != code_salt:
            return jsonify({"code": 400, "message": "验证码哈希不匹配喵喵"}), 400
        
        password_hash = HashPassword(password)
        if not password_hash:
            return jsonify({"code": 500, "message": "密码处理失败喵喵"}), 500
        
        # 创建新用户
        try:
            # 获取数据库连接
            success, message, db, cursor, table_name = GetDbConnection("users")
            
            if not success:
                print(f"数据库连接失败: {message}")
                return jsonify({"code": 500, "message": f"数据库连接失败喵喵: {message}"}), 500
            
            try:
                current_time = int(time.time())
                cursor.execute(
                    f"INSERT INTO {table_name} (name, password, mail, `group`, createdAt, isActive, isLoggedIn) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        username,              # name
                        password_hash,         # password
                        email,                 # mail
                        "user",                # group
                        current_time,          # createdAt
                        1,                     # isActive
                        0                      # isLoggedIn
                    )
                )
                
                # 提交事务
                db.commit()
                
                # 获取插入的用户ID
                inserted_user_id = cursor.lastrowid
                
                # 成功后删除验证码
                if email in verification_codes:
                    del verification_codes[email]
                
                # 生成返回的用户信息
                # 注：头像、记忆点、签到状态等字段为模拟数据; TODO 需要头像、记忆点、签到状态等字段
                user_info = {
                    "code": 200,
                    "uid": inserted_user_id,
                    "name": username,
                    "avatar": f"/api/files/avatar/{inserted_user_id}.png",         # 模拟头像URL
                    "avatarMin": f"/api/files/avatar/{inserted_user_id}_min.png",  # 模拟小头像URL
                    "moemoepoint": 0,             # 初始记忆点为0
                    "role": "user",               # 角色为user
                    "isChechIn": False,           # 未签到
                    "dailyToolsetUploadCount": 0  # 每日上传数量为0
                }
                
                return jsonify(user_info), 200
            
            except Exception as e:
                # 回滚事务
                if db:
                    db.rollback()
                logging.error(f"创建用户时出错: {str(e)}")
                return jsonify({"code": 500, "message": f"创建用户失败喵喵: {str(e)}"}), 500
            
            finally:
                # 释放数据库连接
                if db:
                    db_orm.return_db(db, "default")
        
        except Exception as e:
            logging.error(f"数据库操作时出错: {str(e)}")
            return jsonify({"code": 500, "message": "数据库操作失败喵喵"}), 500
    
    except Exception as e:
        logging.error(f"注册过程中出现未预期错误喵: {str(e)}")
        return jsonify({"code": 500, "message": "注册失败，请稍后重试喵喵"}), 500


@auth_bp.route('/email/code/register', methods=['POST'])
def send_email_code_register_api():
    """发送验证码
    
    请求格式:
    ```
    POST /api/auth/email/code/register
    {
        "email": "用户邮箱"
    }
    ```
    
    响应格式:

    成功:
        `{"code": 200, "codeSalt": "验证码哈希"}`

    失败:
    ```
    {
        "statusCode": 233,
        "stack": [],
        "data": {
            "code": 233,
            "message": "您的邮箱已经被使用了, 请换一个试试"
        }
    }
    ```
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据为空喵喵"}), 400
        
        email = data.get('email')

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"code": 400, "message": "邮箱格式不正确喵喵"}), 400

        try:
            db_prefix = DoesitexistConfigToml('db', 'sql_prefix')
            sql_sqlite_path = DoesitexistConfigToml('db', 'sql_sqlite_path')
            
            if not db_prefix or not sql_sqlite_path:
                print("数据库配置缺失: db_prefix或sql_sqlite_path为空")
                return jsonify({"code": 500, "message": "数据库配置缺失喵喵"}), 500
        except Exception as e:
            logging.error(f"读取配置文件时出错: {str(e)}")
            return jsonify({"code": 500, "message": "读取配置失败喵喵"}), 500
        
        try:
            user = GetUserByEmail(email)
            if user:
                return jsonify({
                    "statusCode": 233,
                    "stack": [],
                    "data": {
                        "code": 233,
                        "message": "您的邮箱已经被使用了喵, 请换一个试试喵"
                    }
                }), 400
        except Exception as e:
            logging.error(f"检查邮箱是否已存在时出错喵喵: {str(e)}")
            return jsonify({"code": 500, "message": "数据库查询失败喵喵"}), 500
        
        # 生成6位字母数字混合验证码
        try:
            random.seed()
            chars = string.ascii_letters + string.digits
            verification_code = ''.join([random.choice(chars) for _ in range(6)])
        except Exception as e:
            logging.error(f"生成验证码时出错: {str(e)}")
            return jsonify({"code": 500, "message": "验证码生成失败喵喵"}), 500
        
        code_salt = HashPassword(verification_code)
        if not code_salt:
            logging.error("验证码哈希失败")
            return jsonify({"code": 500, "message": "验证码生成失败喵喵"}), 500
        
        # 计算验证码过期时间
        expires_at = int(time.time()) + CODE_EXPIRATION_TIME
        
        # 存储验证码信息到内存中
        verification_codes[email] = {
            "code": verification_code,
            "hash": code_salt,
            "expires_at": expires_at,
            "created_at": int(time.time())
        }
        print(f"验证码 {verification_code} 已成功生成并存储到内存中, 过期时间为 {expires_at}")
        # 实现邮件发送功能
        try:
            msg = Message(
                subject="注册验证码",
                recipients=[email],
                sender=SMTP_CONFIG['MAIL_DEFAULT_SENDER']
            )
            
            # 邮件正文
            msg.body = f"哈喽～✨ 你有一条可爱的注册验证码待查收!请在 5 分钟内使用它完成注册哦 ⏳,\n验证码过期后需要重新获取~\n\n如果不是你在注册,忽略这封邮件就好啦 💌\n\n你的注册验证码是:{verification_code},🐾 本邮件由系统自动发送,无需回复."
            
            # 发送邮件
            mail.send(msg)
            # print(f"验证码 {verification_code} 已成功发送到邮箱 {email}")
        except Exception as e:
            logging.error(f"发送邮件失败喵: {str(e)}")
            # 从内存中删除已生成的验证码
            if email in verification_codes:
                del verification_codes[email]
            return jsonify({"code": 500, "message": "发送邮件失败，请稍后重试喵喵"}), 500
        
        cleanup_expired_codes()

        return jsonify({"code": 200, "codeSalt": code_salt}), 200
        
    except Exception as e:
        logging.error(f"发送验证码过程中出现未预期错误喵: {str(e)}")
        return jsonify({"code": 500, "message": "发送验证码失败，请稍后重试喵喵"}), 500


@auth_bp.route('/user/userInfoEdit', methods=['POST'])
def user_info_edit_api():
    """修改用户个人信息 - 使用插件系统实现
    
    请求格式：
    ```
    POST /api/auth/user/userInfoEdit
    {
        "description": "个人描述",
        "age": 25,
        "gender": 1,
        "avatar": "头像URL",
        "location": "地理位置",
        "website": "个人网站",
        "bio": "个人简介",
        "birthday": "生日",
        "phone": "电话号码",
        "occupation": "职业"
    }
    ```
    
    响应格式：
    
    成功:
    ```
    {
        "code": 200,
        "message": "个人信息更新成功喵",
        "data": {
            "description": "更新后的个人描述",
            "age": 25,
            "gender": 1,
            "avatar": "头像URL",
            "location": "地理位置",
            "website": "个人网站",
            "bio": "个人简介",
            "birthday": "生日",
            "phone": "电话号码",
            "occupation": "职业"
        }
    }
    ```
    
    失败:
    ```
    {
        "code": 错误码,
        "message": "错误信息",
        "errors": ["具体错误信息1", "具体错误信息2"]
    }
    ```
    """
    try:
        # 验证用户身份
        user_identity = GetCurrentUserIdentity()
        if user_identity is None:
            return jsonify({"code": 401, "message": "用户未登录喵喵"}), 401
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据为空喵喵"}), 400
        
        # 使用插件系统进行参数验证
        validation_results = call_plugin_hook("user_info_edit_validation", data)
        
        # 收集所有插件的验证错误
        validation_errors = []
        for result in validation_results:
            if result and isinstance(result, tuple) and len(result) == 2:
                is_valid, errors = result
                if not is_valid and isinstance(errors, list):
                    validation_errors.extend(errors)
        
        # 如果有验证错误，返回错误信息
        if validation_errors:
            return jsonify({
                "code": 400,
                "message": "参数验证失败喵喵",
                "errors": validation_errors
            }), 400
        
        # 使用插件系统进行数据预处理
        processed_data = data.copy()
        pre_save_results = call_plugin_hook("user_data_pre_save", processed_data)
        
        # 应用插件的预处理结果
        for result in pre_save_results:
            if result and isinstance(result, dict):
                processed_data.update(result)
        
        # 保存用户数据
        from contents.plugin.wes_user_information.main import save_user_meta
        success = save_user_meta(user_identity, processed_data)
        
        if not success:
            return jsonify({"code": 500, "message": "保存用户信息失败喵喵"}), 500
        
        # 使用插件系统进行后处理
        call_plugin_hook("user_data_post_save", processed_data)
        
        return jsonify({
            "code": 200,
            "message": "个人信息更新成功喵",
            "data": processed_data
        }), 200
                
    except Exception as e:
        logging.error(f"修改用户信息过程中出现错误喵: {e}")
        return jsonify({"code": 500, "message": "服务器内部错误喵喵"}), 500

# @auth_bp.route('/refresh', methods=['POST'])
# def refresh_api():
#     """
#     POST /api/auth/refresh
      
#      使用lmoadll_refresh_token刷新access token
     
#      请求格式: 仅接受从cookie中获取lmoadll_refresh_token
    
#     响应格式：
#     * 成功: `{"code": 200, "message": "令牌刷新成功", "expires_in": 900}`
#     * 失败: `{"code": 错误码, "message": "错误信息"}`
#     """
#     try:
#         # 仅从cookie中获取refresh token,移除从请求体获取的路径
#         refresh_token = request.cookies.get('lmoadll_refresh_token')
        
#         if not refresh_token:
#             return jsonify({"code": 400, "message": "缺少lmoadll_refresh token喵喵"}), 400
        
#         # 刷新access token,传入请求上下文以进行额外验证
#         new_access_token = RefreshToken(refresh_token, request)
#         if not new_access_token:
#             return jsonify({"code": 401, "message": "无效的refresh token喵喵"}), 401
        
#         # 从配置中获取access token过期时间(分钟)
#         access_expires_in = 15  # 默认15分钟
        
#         # 不在JSON响应中返回token
#         response = jsonify({
#             "code": 200,
#             "message": "令牌刷新成功喵",
#             "expires_in": access_expires_in * 60  # 转换为秒
#         })
        
#         response.set_cookie(
#             'lmoadllUser', 
#             new_access_token,
#             httponly=True,           # 防止XSS攻击
#             secure=True,             # 仅HTTPS传输
#             samesite='None',         # 允许跨站使用
#             max_age=15*60            # 15分钟过期时间
#         )
        
#         return response, 200
#     except Exception as e:
#         logging.error(f"刷新令牌过程中出现错误喵: {e}")
#         return jsonify({"code": 500, "message": "刷新失败喵"}), 500
