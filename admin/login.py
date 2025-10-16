# -*- coding: utf-8 -*-
from flask import Blueprint, send_file, request, redirect
from var.token import GetCurrentUserIdentity



loginRouter = Blueprint('login', __name__, url_prefix='/login')


@loginRouter.route('/', methods=["GET"])
def login_page():
    """
    如果已经登录, 则重定向;
    否则返回登录页面, 让用户登录
    """
    user_identity = GetCurrentUserIdentity()
    if user_identity is None:
        return send_file('./admin/base/login.html')
    else:
        redirect_url = request.args.get('redirect', '/')
        return redirect(redirect_url)
