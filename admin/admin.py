"""
-*- coding: utf-8 -*-
系统后台管理

为了区分普通用户和管理员, 此管理面板为管理员专属;
普通用户应该另开, 而不是使用管理员面板.
"""

from flask import Blueprint, send_file, Response, redirect, url_for, request
from functools import wraps
from var.token import GetCurrentUserIdentity
from var.TomlConfig import DoesitexistConfigToml
from var.sql.LmoadllOrm import (
    GetUserRoleByIdentity,
    GetUserCount,
    GetUserNameByIdentity,
    GetSiteOptionByName,
    GetOrSetSiteOption
)



adminRouter = Blueprint('admin', __name__, url_prefix='/admin')


# 没权限就想来? 没门()
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先检查用户是否登录
        user_identity = GetCurrentUserIdentity()
        if user_identity is None:
            # 用户未登录，重定向到登录页面
            original_path = request.path
            if request.query_string:
                original_path = f"{original_path}?{request.query_string.decode('utf-8')}"
            return redirect(url_for('login.login_page', redirect=original_path))
        
        try:
            user_group = GetUserRoleByIdentity(user_identity)
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
    return send_file('admin/base/admin.html')


@adminRouter.route('/options-general', methods=['GET'])
@admin_required
def admin_options_general() -> Response:
    return send_file('admin/base/options-general.html')


@adminRouter.route('/user_count', methods=['POST'])
@admin_required
def admin_get_user_count() -> Response:
    """get user count"""
    user_count = GetUserCount()
    return Response(str(user_count), mimetype='text/plain')


@adminRouter.route('/get_admin_name', methods=['POST'])
@admin_required
def admin_get_admin_name() -> Response:
    """get admin name"""
    user_identity = GetCurrentUserIdentity()
    if user_identity is None:
        return Response("Unknown", mimetype='text/plain')
    
    try:
        # 先检查用户是否有管理员权限
        user_group = GetUserRoleByIdentity(user_identity)
        if user_group and user_group[0] in ['superadministrator', 'administrator']:
            # 获取用户名
            user_name = GetUserNameByIdentity(user_identity)
            if user_name and user_name[0]:
                return Response(user_name[0], mimetype='text/plain')
        return Response("Unknown", mimetype='text/plain')
    except Exception as e:
        print(f"获取用户信息时出错: {e}")
        return Response("Unknown", mimetype='text/plain')


@adminRouter.route('/get_admin_identity', methods=['POST'])
@admin_required
def admin_get_admin_identity() -> Response:
    """get admin Identity"""
    user_identity = GetCurrentUserIdentity()
    if user_identity is None:
        return Response("Unknown", mimetype='text/plain')
    
    try:
        user_group = GetUserRoleByIdentity(user_identity)
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


@adminRouter.route('/get_name_options', methods=['POST'])
@admin_required
def admin_get_name_options() -> Response:
    """
    P26

    get name options

    查询全局设置
    """
    try:
        option_name = request.json.get('user').strip()
        name_options = GetSiteOptionByName(option_name) # [True, {"name": name, "user": user, "value": value}]
        if name_options[0] and name_options[1] is not None:
            return Response(name_options[1]['value'], mimetype='text/plain')
        else:
            return Response('', mimetype='text/plain')
    except Exception as e:
        print(f'获取全局设置失败喵: {e}')
        return Response('Unknown', mimetype='text/plain')


@adminRouter.route('/set_name_options', methods=['POST'])
@admin_required
def admin_set_name_options() -> Response:
    """set name options"""
    try:
        site_name = request.json.get('site_name').strip()
        site_description = request.json.get('site_description').strip()
        site_keywords = request.json.get('site_keywords').strip()
        enable_registration = str(request.json.get('enable_registration')).lower()
        # 获取数据库前缀和路径
        db_prefix = DoesitexistConfigToml("db", "sql_prefix")
        sql_sqlite_path = DoesitexistConfigToml("db", "sql_sqlite_path")

        if not db_prefix or not sql_sqlite_path:
            return Response("数据库配置缺失", mimetype='text/plain')

        # 保存网站名称
        result_name = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'site_name', site_name)
        # 保存网站描述
        result_description = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'site_description', site_description)
        # 保存网站关键词
        result_keywords = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'site_keywords', site_keywords)
        # 保存允许用户注册设置
        result_registration = GetOrSetSiteOption(db_prefix, sql_sqlite_path, 'enable_registration', enable_registration)
        
        if result_name[0] and result_description[0] and result_keywords[0] and result_registration[0]:
            return Response("网站设置保存成功", mimetype='text/plain')
        else:
            print(f'网站设置保存失败喵: {result_name[1]}, {result_description[1]}, {result_keywords[1]}, {result_registration[1]}')
            return Response(f"网站设置保存失败: {result_name[1]}, {result_description[1]}, {result_keywords[1]}, {result_registration[1]}", mimetype='text/plain')
    except Exception as e:
        print(f'保存全局设置失败喵: {e}')
        return Response(f'保存全局设置失败: {e}', mimetype='text/plain')
