# -*- coding: utf-8 -*-
from flask import Blueprint, send_file



adminRouter = Blueprint('admin', __name__, url_prefix='/admin')


@adminRouter.route('/', methods=['GET'])
def admin_index() -> dict[str, str]:
    return send_file('admin/index.html')
