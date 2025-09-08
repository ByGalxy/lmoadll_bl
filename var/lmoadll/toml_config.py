# -*- coding: utf-8 -*-
import os
import tomllib


config_path = "config.toml"


# 检查配置文件是否存在并读取
def Doesitexist_configtoml(a, b):
    if not os.path.exists(config_path):
        return False
    else:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)

        if not config[a][b]:
            return False
        else:
            return config[a][b]
