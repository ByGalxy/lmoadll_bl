# -*- coding: utf-8 -*-
from flask import Blueprint, send_file, request, redirect
from var.token import get_current_user_identity



loginRouter = Blueprint('login', __name__, url_prefix='/login')


"""
如果已经登录, 则重定向;
否则返回登录页面, 让用户登录
"""
@loginRouter.route('/', methods=["GET"])
def login_page():
    user_identity = get_current_user_identity()
    if user_identity is None:
        return send_file('./admin/base/login.html')
    else:
        redirect_url = request.args.get('redirect', '/')
        return redirect(redirect_url)
