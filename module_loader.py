import os
import sys
import importlib.util
import traceback
import config
from utils import log
from language import get_string

# 全局状态
loaded_plugins = {}
loaded_themes = {}
current_theme = None

def _load_module(folder_path, expected_file, module_type):
    """
    加载单个模块
    """
    if not os.path.isdir(folder_path):
        return None, f"Path is not a directory: {folder_path}"
    
    module_file = os.path.join(folder_path, expected_file)
    if not os.path.exists(module_file):
        return None, f"Main file not found: {expected_file}"
    
    module_name = os.path.basename(folder_path)
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None:
            return None, f"Failed to create spec for: {module_name}"
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # 如果是主题，检查是否实现了必要的方法
        if module_type == "theme":
            if not hasattr(module, 'apply'):
                return None, "Theme must implement apply() method"
        
        return module, None
    except Exception as e:
        error_msg = f"Error loading module '{module_name}': {str(e)}\n{traceback.format_exc()}"
        return None, error_msg

def load_plugins():
    """
    加载所有插件
    """
    global loaded_plugins
    plugin_dir = os.path.join(os.path.dirname(__file__), config.PLUGINS_DIR)
    
    if not os.path.exists(plugin_dir):
        log("ERROR", get_string("plugin_dir_missing") + f" {plugin_dir}")
        return False
    
    plugin_count = 0
    success = True
    
    for plugin_name in os.listdir(plugin_dir):
        plugin_path = os.path.join(plugin_dir, plugin_name)
        
        if not os.path.isdir(plugin_path):
            continue
            
        main_file = f"{plugin_name}.py"
        plugin_module, error = _load_module(plugin_path, main_file, "plugin")
        
        if error:
            success = False
            log("ERROR", get_string("plugin_load_error") + f" {plugin_name}\n{error}")
            continue
        
        loaded_plugins[plugin_name] = plugin_module
        log("SUCCESS", get_string("plugin_loaded") + f" {plugin_name}")
        plugin_count += 1
    
    log("INFO", f"Loaded plugins: {plugin_count}")
    return plugin_count > 0

def load_themes():
    """
    加载主题
    """
    global loaded_themes, current_theme
    theme_dir = os.path.join(os.path.dirname(__file__), config.THEMES_DIR)
    
    if not os.path.exists(theme_dir):
        log("ERROR", get_string("theme_dir_missing") + f" {theme_dir}")
        return False
    
    theme_count = 0
    loaded_theme = None
    
    for theme_name in os.listdir(theme_dir):
        theme_path = os.path.join(theme_dir, theme_name)
        
        if not os.path.isdir(theme_path):
            continue
            
        theme_module, error = _load_module(theme_path, "main.py", "theme")
        
        if error:
            log("ERROR", get_string("theme_load_error") + f" {theme_name}\n{error}")
            continue
        
        if not loaded_theme:
            loaded_theme = theme_name
            loaded_themes[theme_name] = theme_module
            current_theme = theme_name
            log("SUCCESS", get_string("theme_loaded") + f" {theme_name}")
            theme_count = 1
            
            # 应用主题
            try:
                theme_module.apply()
                log("INFO", f"Theme applied: {theme_name}")
            except Exception as e:
                log("ERROR", f"Error applying theme: {str(e)}")
        
        # 只加载一个主题，所以找到第一个后就停止, 暂时这样写
        break
    
    log("INFO", f"Loaded themes: {theme_count}")
    return theme_count > 0

def unload_plugin(plugin_name):
    """
    卸载指定插件
    """
    global loaded_plugins
    
    if plugin_name in loaded_plugins:
        plugin_module = loaded_plugins[plugin_name]
        
        if hasattr(plugin_module, 'unload'):
            try:
                plugin_module.unload()
                log("INFO", get_string("plugin_unloaded") + f" {plugin_name}")
            except Exception as e:
                log("ERROR", get_string("plugin_unload_error") + f" {plugin_name}\n{str(e)}")
        
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]
        
        del loaded_plugins[plugin_name]
        return True
    
    log("WARN", f"Plugin not loaded: {plugin_name}")
    return False

def unload_theme(theme_name):
    """
    卸载指定主题
    """
    global loaded_themes, current_theme
    
    if theme_name in loaded_themes:
        theme_module = loaded_themes[theme_name]
        
        if hasattr(theme_module, 'unload'):
            try:
                theme_module.unload()
                log("INFO", get_string("theme_unloaded") + f" {theme_name}")
            except Exception as e:
                log("ERROR", get_string("theme_unload_error") + f" {theme_name}\n{str(e)}")
        
        if theme_name in sys.modules:
            del sys.modules[theme_name]
        
        del loaded_themes[theme_name]
        
        if current_theme == theme_name:
            current_theme = None
        
        return True
    
    log("WARN", f"Theme not loaded: {theme_name}")
    return False

def reload_plugin(plugin_name):
    """
    重新加载指定插件
    """
    global loaded_plugins
    
    if plugin_name in loaded_plugins:
        unload_plugin(plugin_name)
        
        plugin_dir = os.path.join(os.path.dirname(__file__), config.PLUGINS_DIR)
        plugin_path = os.path.join(plugin_dir, plugin_name)
        main_file = f"{plugin_name}.py"
        
        plugin_module, error = _load_module(plugin_path, main_file, "plugin")
        
        if error:
            log("ERROR", f"Failed to reload plugin: {plugin_name}\n{error}")
            return False
        
        loaded_plugins[plugin_name] = plugin_module
        log("SUCCESS", f"Plugin reloaded: {plugin_name}")
        return True
    
    log("WARN", f"Plugin not loaded: {plugin_name}")
    return False

def reload_theme(theme_name):
    """
    重新加载指定主题
    """
    global loaded_themes, current_theme
    
    if theme_name in loaded_themes:
        unload_theme(theme_name)
        
        theme_dir = os.path.join(os.path.dirname(__file__), config.THEMES_DIR)
        theme_path = os.path.join(theme_dir, theme_name)
        
        theme_module, error = _load_module(theme_path, "main.py", "theme")
        
        if error:
            log("ERROR", f"Failed to reload theme: {theme_name}\n{error}")
            return False
        
        loaded_themes[theme_name] = theme_module
        current_theme = theme_name
        log("SUCCESS", f"Theme reloaded: {theme_name}")
        
        try:
            theme_module.apply()
            log("INFO", f"Theme applied: {theme_name}")
        except Exception as e:
            log("ERROR", f"Error applying theme: {str(e)}")
        
        return True
    
    log("WARN", f"Theme not loaded: {theme_name}")
    return False

def unload_all():
    """
    卸载所有插件和主题
    """
    for plugin_name in list(loaded_plugins.keys()):
        unload_plugin(plugin_name)
    
    for theme_name in list(loaded_themes.keys()):
        unload_theme(theme_name)

def reload_all():
    """
    重新加载所有插件和主题
    """
    log("INFO", get_string("reloading"))
    unload_all()
    plugins_ok = load_plugins()
    themes_ok = load_themes()
    
    if not plugins_ok and not themes_ok:
        log("WARN", get_string("no_modules_loaded"))
    elif not plugins_ok or not themes_ok:
        log("WARN", get_string("reload_errors"))
    else:
        log("SUCCESS", get_string("reload_complete"))
    
    return plugins_ok or themes_ok

def get_loaded_plugins():
    """
    获取已加载插件列表
    """
    return list(loaded_plugins.keys())

def get_loaded_themes():
    """
    获取已加载主题列表
    """
    return list(loaded_themes.keys())

def get_current_theme():
    """
    获取当前主题
    """
    return current_theme