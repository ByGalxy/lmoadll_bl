'''
-*- coding: utf-8 -*-
系统后台管理

为了区分普通用户和管理员, 此管理面板为管理员专属;
普通用户应该另开, 而不是使用管理员面板.
'''

from flask import Blueprint, send_file, Response, redirect, url_for, request
from functools import wraps
from var.token import get_current_user_identity
from var.sql.sqlite.sqlite import get_user_role_by_identity, get_user_count, get_user_name_by_identity, get_site_option_by_name



adminRouter = Blueprint('admin', __name__, url_prefix='/admin')


# 没权限就想来? 没门()
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先检查用户是否登录
        user_identity = get_current_user_identity()
        if user_identity is None:
            # 用户未登录，重定向到登录页面
            original_path = request.path
            if request.query_string:
                original_path = f"{original_path}?{request.query_string.decode('utf-8')}"
            return redirect(url_for('login.login_page', redirect=original_path))
        
        try:
            user_group = get_user_role_by_identity(user_identity)
            # 检查用户角色
            if user_group[0] in ['superadministrator', 'administrator']:
                # 用户是管理员，继续执行原函数
                return f(*args, **kwargs)
            else:
                # 用户不是管理员，重定向到首页
                return redirect('/')
        except Exception as e:
            print(f"获取用户信息时出错: {e}")
            return redirect('/')
    return decorated_function


@adminRouter.route('/', methods=['GET'])
@admin_required
def admin_index() -> Response:
    return send_file('admin/base/index.html')


@adminRouter.route('/options-general', methods=['GET'])
@admin_required
def admin_options_general() -> Response:
    return send_file('admin/base/options-general.html')


# get user count
@adminRouter.route('/user_count', methods=['POST'])
@admin_required
def admin_get_user_count() -> Response:
    user_count = get_user_count()
    return Response(str(user_count), mimetype='text/plain')


# get admin name
@adminRouter.route('/get_admin_name', methods=['POST'])
@admin_required
def admin_get_admin_name() -> Response:
    user_identity = get_current_user_identity()
    if user_identity is None:
        return Response("Unknown", mimetype='text/plain')
    
    try:
        # 先检查用户是否有管理员权限
        user_group = get_user_role_by_identity(user_identity)
        if user_group and user_group[0] in ['superadministrator', 'administrator']:
            # 获取用户名
            user_name = get_user_name_by_identity(user_identity)
            if user_name and user_name[0]:
                return Response(user_name[0], mimetype='text/plain')
        return Response("Unknown", mimetype='text/plain')
    except Exception as e:
        print(f"获取用户信息时出错: {e}")
        return Response("Unknown", mimetype='text/plain')


# get admin Identity
@adminRouter.route('/get_admin_identity', methods=['POST'])
@admin_required
def admin_get_admin_identity() -> Response:
    user_identity = get_current_user_identity()
    if user_identity is None:
        return Response("Unknown", mimetype='text/plain')
    
    try:
        user_group = get_user_role_by_identity(user_identity)
        if user_group and len(user_group) > 0:
            # 检查用户角色
            if user_group[0] == 'superadministrator':
                return Response('超级管理员', mimetype='text/plain')
            elif user_group[0] == 'administrator':
                return Response('管理员', mimetype='text/plain')
        return Response('Unknown', mimetype='text/plain')
    except Exception as e:
        print(f"获取用户身份时出错: {e}")
        return Response('Unknown', mimetype='text/plain')


"""
P26
get name options
查询全局设置
"""
@adminRouter.route('/get_name_options', methods=['POST'])
@admin_required
def admin_get_name_options() -> Response:
    try:
        user = request.json.get('user').strip()
        name_options = get_site_option_by_name(user) # [True, {"name": name, "user": user, "value": value}]
        return Response(name_options[1]['value'], mimetype='text/plain')
    except Exception as e:
        print(f'获取全局设置失败喵: {e}') # fuck
        return Response('Unknown', mimetype='text/plain')
