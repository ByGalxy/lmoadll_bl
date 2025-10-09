# -*- coding: utf-8 -*-
from flask import Blueprint, Response, send_file, request, jsonify, abort
from var.sql.sqlite.sqlite import check_superadmin_exists, get_or_set_site_option
from var.toml_config import Doesitexist_configtoml, red_configtoml
from var.argon2_password import hash_password
from var.sql.mysql.mysql import sc_verification_db_conn as mysql_svdc
from var.sql.sqlite.sqlite import sc_verification_db_conn as sqlite_svdc
from functools import wraps
import os
import random
import string



installRouter = Blueprint('install', __name__, url_prefix='/install')


def install_permissions(f):
    @wraps(f)
    def per_install(*args, **kwargs):
        if Doesitexist_configtoml('server', 'install'):
            return f(*args, **kwargs)
        else:
            return abort(404)
    return per_install


@installRouter.route('/', methods=['GET'])
@install_permissions
def install_index() -> Response | None:
    return send_file('install/base/install.html')


# 判断是否有配置过数据库
@installRouter.route('/check_database_configuration', methods=['POST'])
@install_permissions
def check_database_configuration() -> None:
    if Doesitexist_configtoml('db','sql_rd') == 'sqlite' and Doesitexist_configtoml('db','sql_prefix') != '' and os.path.exists(Doesitexist_configtoml('db','sql_sqlite_path')):
        # 还没开始写......
        pass


# 获取数据库路径, 自动生成路径and return
@installRouter.route('/get_sqlite_path', methods=['POST'])
@install_permissions
def get_sqlite_path() -> Response:
    data = request.get_json()
    db_type = data.get('db_type')

    if db_type == 'sqlite':
        usr_dir = 'usr'
        os.makedirs(usr_dir, exist_ok=True)

        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        db_filename = f'{random_name}.db'
        default_path = os.path.abspath(os.path.join(usr_dir, db_filename))

        return jsonify({'path': default_path})
    
    return jsonify({'error': '无效的数据库类型'})


# 测试数据库连接并保持配置
@installRouter.route('/verification_db_conn', methods=['POST'])
@install_permissions
def install_verification_db_conn() -> Response:
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求的数据为空'})

    # 处理SQLite数据库
    if data['db_type'] == 'sqlite':
        # 获取SQLite相关参数
        db_prefix = data.get('db_prefix', 'lmoadll_')
        sql_sqlite_path = data.get('sql_sqlite_path')
        
        # 检查必要参数是否存在
        if not sql_sqlite_path:
            return jsonify({'success': False, 'message': 'SQLite数据库路径不能为空'})
        
        # 调用SQLite验证函数
        result = sqlite_svdc(db_prefix, sql_sqlite_path)
        if result[0]:
            return jsonify({'success': True, 'message': 'SQLite连接成功'})
        else:
            return jsonify({'success': False, 'message': f'数据库连接错误: {result[1]}'})
    
    # 处理MySQL数据库
    elif data['db_type'] == 'mysql':
        result = mysql_svdc(
            data.get('db_host'),
            data.get('db_port'),
            data.get('db_name'),
            data.get('db_user'),
            data.get('db_password')
        )

        if result[0]:
            return jsonify({'success': True, 'message': 'MySQL连接成功'})
        else:
            return jsonify({'success': False, 'message': f'数据库连接错误: {result[1]}'})
    
    # 处理未知数据库类型
    else:
        return jsonify({'success': False, 'message': f'数据类型本喵不认识 {data["db_type"]}'})


# 创建超级管理员账号并保存配置
@installRouter.route('/create_admin_account', methods=['POST'])
@install_permissions
def create_admin_account() -> Response:
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求的数据为空'})

    # 获取表单数据
    site_name = data.get('site_name')
    site_url = data.get('site_url')
    superadministrator_email = data.get('superadministrator_email')
    superadministrator_username = data.get('superadministrator_username')
    superadministrator_password = data.get('superadministrator_password')

    # 验证必填字段
    if not site_name or not site_url or not superadministrator_email or not superadministrator_username or not superadministrator_password:
        return jsonify({'success': False, 'message': '请填写所有必填字段'})

    try:
        # 加密密码
        hashed_password = hash_password(superadministrator_password)
        if not hashed_password:
            return jsonify({'success': False, 'message': '密码加密失败'})

        # 获取并保存数据库配置
        db_type = data.get('db_type')
        if db_type == 'sqlite':
            red_configtoml('db', 'sql_rd', 'sqlite')
            db_prefix = data.get('db_prefix', 'lmoadll_')
            red_configtoml('db', 'sql_prefix', db_prefix)
            sql_sqlite_path = data.get('sql_sqlite_path')
            red_configtoml('db', 'sql_sqlite_path', sql_sqlite_path)
            
            # 保存网站配置到数据库
            get_or_set_site_option(db_prefix, sql_sqlite_path, 'site_name', site_name)
            get_or_set_site_option(db_prefix, sql_sqlite_path, 'site_url', site_url)
            
            # 在数据库中创建超级管理员账号
            result = check_superadmin_exists(
                db_prefix,
                sql_sqlite_path,
                superadministrator_username,
                superadministrator_email,
                hashed_password
            )
            
            if not result[0]:
                return jsonify({'success': False, 'message': f'创建管理员账号失败: {result[1]}'})
        elif db_type == 'mysql':
            # 还没开始写......
            pass
        
        # 关闭安装模式
        red_configtoml('server', 'install', False)

        return jsonify({'success': True, 'message': '超级管理员账号创建成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建管理员账号失败: {str(e)}'})
