# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
from flask import Blueprint
from magic.api.AdminEndpoints import admin_bp
from magic.api.auth import auth_bp
from magic.api.PluginApi import plugin_api_bp


api_bp = Blueprint('api', __name__, url_prefix='/api')


api_bp.register_blueprint(admin_bp, url_prefix='/admin')
api_bp.register_blueprint(auth_bp, url_prefix='/auth')
api_bp.register_blueprint(plugin_api_bp, url_prefix='/plugin')
