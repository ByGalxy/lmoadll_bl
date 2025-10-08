# -*- coding: utf-8 -*-
from flask import Blueprint, send_from_directory



assersRouter = Blueprint('asses', __name__, url_prefix='/asses')


@assersRouter.route('/css/<path:filename>')
def admin_assess_css(filename):
    return send_from_directory('admin/asses/css', filename)


@assersRouter.route('/js/<path:filename>')
def admin_assess_js(filename):
    return send_from_directory('admin/asses/js', filename)
