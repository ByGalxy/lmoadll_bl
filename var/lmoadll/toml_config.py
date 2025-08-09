# -*- coding: utf-8 -*-

def toml_config():
    import tomllib
    import os
    # 获取配置文件路径
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.toml')

    # 读取TOML配置
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)
    return config
