# -*- coding: utf-8 -*-
"""
lmoadll_bl platform

@copyright  Copyright (c) 2025 lmoadll_bl team
@license  GNU General Public License 3.0
"""

from flask import Flask
from var.Inits import Init_module
from dotenv import load_dotenv
import os


load_dotenv()
env_debug = os.getenv('debug')
app = Flask(__name__)
Init_module(app)


@app.get('/')
def root():
   return {'Status': 'OK'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2324, debug=env_debug, threaded=True)
