# -*- coding: utf-8 -*-
from flask import Blueprint, send_from_directory



assersRouter = Blueprint('asses', __name__, url_prefix='/asses')


@assersRouter.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('admin/asses/css', filename)
