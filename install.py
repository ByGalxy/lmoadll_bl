# -*- coding: utf-8 -*-
from flask import Blueprint, Response, send_file, request, jsonify, abort
from var.lmoadll.sql.mysql.mysql import sc_verification_db_conn as mysql_svdc
from var.lmoadll.sql.sqlite.sqlite import sc_verification_db_conn as sqlite_svdc
from var.lmoadll.toml_config import Doesitexist_configtoml as dctoml
from functools import wraps
import os
import random
import string



installRouter = Blueprint('install', __name__, url_prefix='/install')


def Install_perssions(f):
    @wraps(f)
    def per_install(*args, **kwargs):
        if dctoml('server','install'):
            return f(*args,**kwargs)
        else:
            return abort(404)
    return per_install


@installRouter.route('/', methods=['GET'])
@Install_perssions
def install_index() -> Response | None:
    return send_file('install/base/install.html')


# 判断是否有配置过数据库
@installRouter.route('/check_database_configuration', methods=['POST'])
@Install_perssions
def check_database_configuration() -> Response:
    if dctoml('db','sql_rd') == 'sqlite' and dctoml('db','sql_prefix') != '' and os.path.exists(dctoml('db','sql_sqlite_path')):
        pass


# 获取数据库路径, 自动生成路径and return
@installRouter.route('/get_sqlite_path', methods=['POST'])
@Install_perssions
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
@Install_perssions
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
            return jsonify(
                {'success': False, 'message': f'数据库连接错误: {result[1]}'}
            )
    
    # 处理MySQL数据库
    elif data['db_type'] == 'mysql':
        result = mysql_svdc(
            data.get('db_host'),
            data.get('db_port'),
            data.get('db_name'),
            data.get('db_user'),
            data.get('db_password'),
        )

        if result[0]:
            return jsonify({'success': True, 'message': 'MySQL连接成功'})
        else:
            return jsonify(
                {'success': False, 'message': f'数据库连接错误: {result[1]}'}
            )
    
    # 处理未知数据库类型
    else:
        return jsonify(
            {'success': False, 'message': f'数据类型本喵不认识 {data["db_type"]}'}
        )