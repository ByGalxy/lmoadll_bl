# -*- coding: utf-8 -*-
import os
import tomllib
import tomli_w



config_path = 'config.toml'

# 检查配置文件是否存在并读取
def Doesitexist_configtoml(a,b):
    if not os.path.exists(config_path):
        return False
    else:
        with open(config_path,'rb') as f:
            config = tomllib.load(f)

        if not config[a][b]:
            return False
        else:
            return config[a][b]

# 检查键并写入配置文件
def red_configtoml(a,b,c):
    if Doesitexist_configtoml(a,b):
        with open(config_path,'rb') as f:
            config = tomllib.load(f)
        config[a][b] = c
        with open('config.toml', 'wb') as f:
            tomli_w.dump(config, f)
