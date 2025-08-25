'''
-*- coding: utf-8 -*-

lmoadll_bl platform

@copyright  Copyright (c) 2025 lmoadll_bl team
@license  GNU General Public License 3.0

'''

from flask import Flask
from install import installRouter

app = Flask(__name__)

app.register_blueprint(installRouter)

@app.get("/")
async def root():
   return {"message": "Hello world"}

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8002,
        debug=True,
        threaded=True
    )
