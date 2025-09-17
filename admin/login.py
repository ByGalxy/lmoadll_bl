# -*- coding: utf-8 -*-
from flask import Blueprint, send_file



loginRouter = Blueprint('login', __name__, url_prefix='/login')


@loginRouter.route('/')
def login_page():
    return send_file('./admin/login.html')
