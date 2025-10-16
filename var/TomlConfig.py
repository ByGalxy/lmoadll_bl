# -*- coding: utf-8 -*-
"""用于处理 TOML 配置文件的读取和写入操作"""
import os
import tomllib
import tomli_w



__all__ = [
    'DoesitexistConfigToml', 
    'WriteConfigToml'
]

config_path = 'config.toml'


def DoesitexistConfigToml(a,b):
    """检查配置文件是否存在并读取"""
    if not os.path.exists(config_path):
        return False
    else:
        with open(config_path,'rb') as f:
            config = tomllib.load(f)

        if not config[a][b]:
            return False
        else:
            return config[a][b]


def WriteConfigToml(a,b,c):
    """检查键并写入配置文件"""
    # 检查配置文件是否存在, 不存在则创建新的配置文件和配置项
    if not os.path.exists(config_path):
        config = {a: {b: c}}
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)
        return
    
    # 读取现有配置文件
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)
    
    # 确保部分a存在
    if a not in config:
        config[a] = {}
    
    # 设置配置值
    config[a][b] = c
    
    # 写回配置文件
    with open(config_path, 'wb') as f:
        tomli_w.dump(config, f)
