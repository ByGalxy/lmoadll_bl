# -*- coding: utf-8 -*-
# lmoadll_bl platform
#
# @copyright  Copyright (c) 2025 lmoadll_bl team
# @license  GNU General Public License 3.0
"""
插件管理API

提供插件的动态加载、卸载、状态查询等功能
"""

from flask import Blueprint, request, jsonify
from magic.PluginSystem import get_plugin_manager
import logging
import os
import json
from typing import Any

plugin_api_bp = Blueprint('plugin_api', __name__)


@plugin_api_bp.route('/plugins', methods=['GET'])
def get_plugins():
    """获取所有插件信息

    GET /api/plugin/plugins
    
    响应格式：
    ```json
    {
        "code": 200,
        "data": {
            "plugins": [
                {
                    "name": "插件名称",
                    "version": "版本号",
                    "description": "插件描述",
                    "author": "作者",
                    "status": "状态",
                    "type": "folder|file",
                    "config": {}
                }
            ]
        }
    }
    ```
    """
    try:
        plugin_manager = get_plugin_manager()
        plugins = plugin_manager.get_all_plugins()
        
        # 获取插件目录路径
        plugin_dir = plugin_manager.plugin_dir
        
        plugin_list = []
        
        # 获取已加载的插件信息
        for plugin_name, plugin in plugins.items():
            plugin_info: dict[str, Any] = {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "status": "enabled",
                "type": "file", # 默认为文件类型
                "config": {}  # 初始化为空字典
            }
            
            # 检查是否为文件夹插件
            plugin_folder_path = os.path.join(plugin_dir, plugin_name)
            if os.path.isdir(plugin_folder_path):
                plugin_info["type"] = "folder"
                
                # 读取配置文件
                config_path = os.path.join(plugin_folder_path, "config.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            plugin_info["config"] = json.load(f)
                    except Exception as e:
                        logging.warning(f"读取插件 {plugin_name} 配置文件失败: {e}")
                        plugin_info["config"] = {}
            
            plugin_list.append(plugin_info)
        
        # 扫描插件目录，获取所有可用的插件（包括未加载的）
        if os.path.exists(plugin_dir):
            for item in os.listdir(plugin_dir):
                plugin_path = os.path.join(plugin_dir, item)
                
                # 只支持文件夹插件且未加载
                if os.path.isdir(plugin_path) and item not in plugins:
                    init_file = os.path.join(plugin_path, "__init__.py")
                    if os.path.exists(init_file):
                        plugin_info = {
                            "name": item,
                            "type": "folder",
                            "status": "disabled"
                        }
                        
                        # 读取配置文件
                        config_path = os.path.join(plugin_path, "config.json")
                        if os.path.exists(config_path):
                            try:
                                with open(config_path, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                                    plugin_info.update({
                                        "version": config.get("version", "1.0.0"),
                                        "description": config.get("description", ""),
                                        "author": config.get("author", ""),
                                        "config": config
                                    })
                            except Exception as e:
                                logging.warning(f"读取插件 {item} 配置文件失败: {e}")
                                plugin_info["config"] = {}
                        
                        plugin_list.append(plugin_info)
        
        return jsonify({
            "code": 200,
            "data": {
                "plugins": plugin_list
            }
        }), 200
        
    except Exception as e:
        logging.error(f"获取插件列表失败: {e}")
        return jsonify({
            "code": 500,
            "message": "获取插件列表失败"
        }), 500


@plugin_api_bp.route('/plugins/<plugin_name>', methods=['POST'])
def load_plugin(plugin_name):
    """加载指定插件
    
    POST /api/plugin/plugins/<plugin_name>

    请求格式：
    ```json
    {
        "action": "load"
    }
    ```
    
    响应格式：
    ```json
    {
        "code": 200,
        "message": "插件加载成功"
    }
    ```
    """
    try:
        data = request.get_json()
        if not data or data.get('action') != 'load':
            return jsonify({
                "code": 400,
                "message": "请求参数错误"
            }), 400
        
        plugin_manager = get_plugin_manager()
        plugin_dir = plugin_manager.plugin_dir
        
        # 检查插件是否已加载
        if plugin_name in plugin_manager.get_all_plugins():
            return jsonify({
                "code": 400,
                "message": "插件已加载"
            }), 400
        
        plugin_path = os.path.join(plugin_dir, plugin_name)
        
        # 优先尝试加载文件夹插件
        if os.path.isdir(plugin_path):
            init_file = os.path.join(plugin_path, "__init__.py")
            if os.path.exists(init_file):
                if plugin_manager.load_plugin_from_folder(plugin_name, plugin_path):
                    return jsonify({
                        "code": 200,
                        "message": "插件加载成功"
                    }), 200
                else:
                    return jsonify({
                        "code": 500,
                        "message": "插件加载失败"
                    }), 500
            else:
                return jsonify({
                    "code": 404,
                    "message": "插件初始化文件不存在"
                }), 404
        else:
            return jsonify({
                "code": 404,
                "message": "插件不存在"
            }), 404
            
    except Exception as e:
        logging.error(f"加载插件失败: {e}")
        return jsonify({
            "code": 500,
            "message": "加载插件失败"
        }), 500


@plugin_api_bp.route('/plugins/<plugin_name>', methods=['DELETE'])
def unload_plugin(plugin_name):
    """卸载指定插件

    DELETE /api/plugin/plugins/<plugin_name>
    
    响应格式：
    ```json
    {
        "code": 200,
        "message": "插件卸载成功"
    }
    ```
    """
    try:
        plugin_manager = get_plugin_manager()
        
        if plugin_manager.unload_plugin(plugin_name):
            return jsonify({
                "code": 200,
                "message": "插件卸载成功"
            }), 200
        else:
            return jsonify({
                "code": 404,
                "message": "插件不存在"
            }), 404
            
    except Exception as e:
        logging.error(f"卸载插件失败: {e}")
        return jsonify({
            "code": 500,
            "message": "卸载插件失败"
        }), 500


@plugin_api_bp.route('/plugins/hooks', methods=['GET'])
def get_hooks():
    """获取所有钩子信息

    GET /api/plugin/plugins/hooks
    
    响应格式：
    ```json
    {
        "code": 200,
        "data": {
            "hooks": {
                "hook_name": ["plugin1", "plugin2"]
            }
        }
    }
    ```
    """
    try:
        plugin_manager = get_plugin_manager()
        hooks = plugin_manager.hooks
        
        hook_info = {}
        for hook_name, hook_funcs in hooks.items():
            plugin_names = []
            for hook_func in hook_funcs:
                if hasattr(hook_func, '__self__'):
                    plugin_names.append(hook_func.__self__.name)
            hook_info[hook_name] = plugin_names
        
        return jsonify({
            "code": 200,
            "data": {
                "hooks": hook_info
            }
        }), 200
        
    except Exception as e:
        logging.error(f"获取钩子信息失败: {e}")
        return jsonify({
            "code": 500,
            "message": "获取钩子信息失败"
        }), 500
