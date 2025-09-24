"""
-*- coding: utf-8 -*-

lmoadll_bl platform

@copyright  Copyright (c) 2025 lmoadll_bl team
@license  GNU General Public License 3.0

"""

from flask import Flask
from flask import send_from_directory
from var.Inits import Init_module



app = Flask(__name__)


@app.route('/asses/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('admin/asses/css', filename)


Init_module(app)


@app.get('/')
def root():
   return {'Status': 'OK'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2324, debug=False, threaded=True)
