# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0


from flask import Blueprint, send_from_directory



assets_bp = Blueprint('asses', __name__, url_prefix='/asses')


@assets_bp.route('/admin/<path:filename>')
def admin_assess_css(filename):
    return send_from_directory('admin/asses/', filename)

@assets_bp.route('/install/<path:filename>')
def install_assess(filename):
    return send_from_directory('admin/asses/', filename)
