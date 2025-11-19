# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0


from flask import Flask
from magic import Init_module
from dotenv import load_dotenv
import os


load_dotenv()
app = Flask(__name__)
app.config["DEBUG"] = os.getenv("debug", "False").lower() in ("true", "1", "t")
app.json.sort_keys = False # type: ignore
Init_module(app)


@app.get("/")
def root():
    return {"Status": "OK"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2324, threaded=True)
