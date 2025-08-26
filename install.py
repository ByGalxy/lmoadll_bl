from flask import Blueprint, Response, send_file, request, jsonify
from var.lmoadll.sql.mysql.mysql import sc_verificat_db_conn as svdc
import os

installRouter = Blueprint('install', __name__, url_prefix='/install')

@installRouter.route('/', methods=['GET'])
def install_index() -> Response:
    config_path = "config.toml"
    if not os.path.exists(config_path):
        return send_file("install/base/install.html")

@installRouter.route('/verificat_db_conn', methods=['POST'])
def install_verificat_db_conn() -> Response:
    data = request.get_json()

    if not data: 
        return jsonify({'success': False, 'message': '请求的数据为空'})

    # 你什么也做不到，也选择不了(不是)
    if data['db_type'] == 'mysql':
        result = svdc(data.get("db_host"), data.get("db_port"), data.get("db_name"), data.get("db_user"), data.get("db_password")
        )
        
        if result[0]:
            return jsonify({'success': True, 'message': 'MySQL连接成功'})
        else:
            return jsonify({'success': False, 'message': f'数据库连接错误: {result[1]}'})
    else:
        return jsonify({
            'success': False, 
            'message': f'数据类型本喵不认识 {data["db_type"]}'
        })
