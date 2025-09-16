"""
-*- coding: utf-8 -*-

lmoadll_bl platform

@copyright  Copyright (c) 2025 lmoadll_bl team
@license  GNU General Public License 3.0

"""

from flask import Flask
import os

app = Flask(__name__)

if os.path.exists('install.py'):
    from install import installRouter
    app.register_blueprint(installRouter)

@app.get('/')
def root():
   return {'Status': 'OK'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2324, debug=True, threaded=True)
