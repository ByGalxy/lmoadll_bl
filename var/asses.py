# -*- coding: utf-8 -*-
from flask import Blueprint, send_from_directory



assetsRouter = Blueprint('asses', __name__, url_prefix='/asses')


@assetsRouter.route('/admin/<path:filename>')
def admin_assess_css(filename):
    return send_from_directory('admin/asses/', filename)

@assetsRouter.route('/install/<path:filename>')
def install_assess(filename):
    return send_from_directory('install/asses/', filename)
