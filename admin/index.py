# -*- coding: utf-8 -*-
from flask import Blueprint, send_file, Response
from var.OAuth import login_required



adminRouter = Blueprint('admin', __name__, url_prefix='/admin')


@adminRouter.route('/', methods=['GET'])
@login_required
def admin_index() -> Response:
    return send_file('admin/index.html')
