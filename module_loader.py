import os
import sys
import importlib.util
import traceback
from config_loader import get_config
from utils import log
from language import get_string
import multiprocessing
import time

# 全局状态
loaded_plugins = {}
loaded_themes = {}
current_theme = None
plugin_processes = {}  # 存储插件进程
theme_process = None  # 主题进程

class PluginProcess(multiprocessing.Process):
    """插件进程类"""
    def __init__(self, plugin_name, module_path):
        super().__init__()
        self.plugin_name = plugin_name
        self.module_path = module_path
        self.daemon = True  # 设置为守护进程
        self.running = multiprocessing.Event()
        self.running.set()
    
    def run(self):
        """运行插件"""
        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(self.plugin_name, self.module_path)
            if spec is None:
                log("ERROR", f"无法为插件 {self.plugin_name} 创建规范")
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[self.plugin_name] = module
            spec.loader.exec_module(module)
            
            # 检查是否有 run 方法
            if not hasattr(module, 'run'):
                log("ERROR", f"插件 {self.plugin_name} 缺少 run() 方法")
                return
            
            # 运行插件
            log("INFO", f"插件 {self.plugin_name} 开始运行")
            module.run(self.running)
            log("INFO", f"插件 {self.plugin_name} 已停止")
            
        except Exception as e:
            log("ERROR", f"插件 {self.plugin_name} 运行时出错: {str(e)}\n{traceback.format_exc()}")

class ThemeProcess(multiprocessing.Process):
    """主题进程类"""
    def __init__(self, theme_name, module_path):
        super().__init__()
        self.theme_name = theme_name
        self.module_path = module_path
        self.daemon = True  # 设置为守护进程
        self.running = multiprocessing.Event()
        self.running.set()
    
    def run(self):
        """运行主题"""
        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(self.theme_name, self.module_path)
            if spec is None:
                log("ERROR", f"无法为主题 {self.theme_name} 创建规范")
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[self.theme_name] = module
            spec.loader.exec_module(module)
            
            # 检查是否有 run 方法
            if not hasattr(module, 'run'):
                log("ERROR", f"主题 {self.theme_name} 缺少 run() 方法")
                return
            
            # 运行主题
            log("INFO", f"主题 {self.theme_name} 开始运行")
            module.run(self.running)
            log("INFO", f"主题 {self.theme_name} 已停止")
            
        except Exception as e:
            log("ERROR", f"主题 {self.theme_name} 运行时出错: {str(e)}\n{traceback.format_exc()}")

def _load_module(folder_path, expected_file, module_type):
    """加载单个模块"""
    if not os.path.isdir(folder_path):
        return None, f"路径不是目录: {folder_path}"
    
    module_file = os.path.join(folder_path, expected_file)
    if not os.path.exists(module_file):
        return None, f"主文件未找到: {expected_file}"
    
    module_name = os.path.basename(folder_path)
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec is None:
            return None, f"无法为模块创建规范: {module_name}"
        
        # 只加载模块规范，不执行
        return spec, None
    except Exception as e:
        error_msg = f"加载模块 '{module_name}' 时出错: {str(e)}\n{traceback.format_exc()}"
        return None, error_msg

def load_plugins():
    """加载所有插件到独立进程"""
    global loaded_plugins, plugin_processes
    plugin_dir = os.path.join(os.path.dirname(__file__), get_config('directories', 'plugins_dir'))
    
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
        plugin_spec, error = _load_module(plugin_path, main_file, "plugin")
        
        if error:
            success = False
            log("ERROR", get_string("plugin_load_error") + f" {plugin_name}\n{error}")
            continue
        
        # 创建并启动插件进程
        try:
            module_file = os.path.join(plugin_path, main_file)
            process = PluginProcess(plugin_name, module_file)
            process.start()
            
            plugin_processes[plugin_name] = process
            loaded_plugins[plugin_name] = plugin_spec
            plugin_count += 1
            
            log("SUCCESS", get_string("plugin_loaded") + f" {plugin_name} (PID: {process.pid})")
        except Exception as e:
            log("ERROR", f"启动插件进程失败: {plugin_name}\n{str(e)}")
            success = False
    
    log("INFO", f"已加载插件数量: {plugin_count}")
    return plugin_count > 0

def load_themes():
    """加载主题到独立进程（只加载第一个有效主题）"""
    global loaded_themes, current_theme, theme_process
    theme_dir = os.path.join(os.path.dirname(__file__), get_config('directories', 'themes_dir'))
    
    if not os.path.exists(theme_dir):
        log("ERROR", get_string("theme_dir_missing") + f" {theme_dir}")
        return False
    
    theme_count = 0
    loaded_theme = None
    
    for theme_name in os.listdir(theme_dir):
        theme_path = os.path.join(theme_dir, theme_name)
        
        if not os.path.isdir(theme_path):
            continue
            
        theme_spec, error = _load_module(theme_path, "main.py", "theme")
        
        if error:
            log("ERROR", get_string("theme_load_error") + f" {theme_name}\n{error}")
            continue
        
        # 只加载第一个有效的主题
        if not loaded_theme:
            try:
                module_file = os.path.join(theme_path, "main.py")
                process = ThemeProcess(theme_name, module_file)
                process.start()
                
                theme_process = process
                loaded_themes[theme_name] = theme_spec
                current_theme = theme_name
                theme_count = 1
                
                log("SUCCESS", get_string("theme_loaded") + f" {theme_name} (PID: {process.pid})")
                loaded_theme = theme_name
                
                # 只加载一个主题，所以找到第一个后就停止
                break
            except Exception as e:
                log("ERROR", f"启动主题进程失败: {theme_name}\n{str(e)}")
    
    log("INFO", f"已加载主题数量: {theme_count}")
    return theme_count > 0

def unload_plugin(plugin_name):
    """卸载指定插件"""
    global loaded_plugins, plugin_processes
    
    if plugin_name in loaded_plugins and plugin_name in plugin_processes:
        process = plugin_processes[plugin_name]
        
        try:
            # 通知插件停止
            process.running.clear()
            
            # 等待进程结束
            log("INFO", f"等待插件 {plugin_name} 停止...")
            process.join()  # 无限期等待，不加超时限制
            log("INFO", get_string("plugin_unloaded") + f" {plugin_name}")
        except Exception as e:
            log("ERROR", get_string("plugin_unload_error") + f" {plugin_name}\n{str(e)}")
        
        # 清理
        del plugin_processes[plugin_name]
        del loaded_plugins[plugin_name]
        return True
    
    log("WARN", f"插件未加载: {plugin_name}")
    return False

def unload_theme(theme_name):
    """卸载指定主题"""
    global loaded_themes, current_theme, theme_process
    
    if theme_name in loaded_themes and theme_process is not None:
        try:
            # 通知主题停止
            theme_process.running.clear()
            
            # 等待进程结束
            log("INFO", f"等待主题 {theme_name} 停止...")
            theme_process.join()  # 无限期等待，不加超时限制
            log("INFO", get_string("theme_unloaded") + f" {theme_name}")
        except Exception as e:
            log("ERROR", get_string("theme_unload_error") + f" {theme_name}\n{str(e)}")
        
        # 清理
        theme_process = None
        del loaded_themes[theme_name]
        
        if current_theme == theme_name:
            current_theme = None
        
        return True
    
    log("WARN", f"主题未加载: {theme_name}")
    return False

def reload_plugin(plugin_name):
    """重新加载指定插件"""
    # 先卸载
    if unload_plugin(plugin_name):
        # 重新加载
        plugin_dir = os.path.join(os.path.dirname(__file__), config.PLUGINS_DIR)
        plugin_path = os.path.join(plugin_dir, plugin_name)
        main_file = f"{plugin_name}.py"
        
        plugin_spec, error = _load_module(plugin_path, main_file, "plugin")
        
        if error:
            log("ERROR", f"重新加载插件失败: {plugin_name}\n{error}")
            return False
        
        try:
            module_file = os.path.join(plugin_path, main_file)
            process = PluginProcess(plugin_name, module_file)
            process.start()
            
            plugin_processes[plugin_name] = process
            loaded_plugins[plugin_name] = plugin_spec
            
            log("SUCCESS", f"插件重新加载成功: {plugin_name} (PID: {process.pid})")
            return True
        except Exception as e:
            log("ERROR", f"启动插件进程失败: {plugin_name}\n{str(e)}")
            return False
    
    log("WARN", f"插件未加载: {plugin_name}")
    return False

def reload_theme(theme_name):
    """重新加载指定主题"""
    # 先卸载
    if unload_theme(theme_name):
        # 重新加载
        theme_dir = os.path.join(os.path.dirname(__file__), config.THEMES_DIR)
        theme_path = os.path.join(theme_dir, theme_name)
        
        theme_spec, error = _load_module(theme_path, "main.py", "theme")
        
        if error:
            log("ERROR", f"重新加载主题失败: {theme_name}\n{error}")
            return False
        
        try:
            module_file = os.path.join(theme_path, "main.py")
            process = ThemeProcess(theme_name, module_file)
            process.start()
            
            theme_process = process
            loaded_themes[theme_name] = theme_spec
            current_theme = theme_name
            
            log("SUCCESS", f"主题重新加载成功: {theme_name} (PID: {process.pid})")
            return True
        except Exception as e:
            log("ERROR", f"启动主题进程失败: {theme_name}\n{str(e)}")
            return False
    
    log("WARN", f"主题未加载: {theme_name}")
    return False

def unload_all():
    """卸载所有插件和主题"""
    # 卸载所有插件
    for plugin_name in list(loaded_plugins.keys()):
        unload_plugin(plugin_name)
    
    # 卸载主题
    if current_theme:
        unload_theme(current_theme)

def reload_all():
    """重新加载所有插件和主题"""
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
    """获取已加载插件列表"""
    return list(loaded_plugins.keys())

def get_loaded_themes():
    """获取已加载主题列表"""
    return list(loaded_themes.keys())

def get_current_theme():
    """获取当前主题"""
    return current_theme

def get_plugin_pid(plugin_name):
    """获取插件进程ID"""
    if plugin_name in plugin_processes:
        return plugin_processes[plugin_name].pid
    return None

def get_theme_pid():
    """获取主题进程ID"""
    if theme_process:
        return theme_process.pid
    return None