import threading
import config
from utils import color_text, log
from language import get_string
from module_loader import (
    unload_plugin, unload_theme,
    reload_plugin, reload_theme,
    reload_all, get_loaded_plugins,
    get_loaded_themes, get_plugin_pid,
    get_theme_pid
)

running = True

def console_listener(lang_strings):
    """控制台命令监听器"""
    global running
    
    while running:
        try:
            cmd = input(color_text("> ", "96")).strip().lower()
            parts = cmd.split()
            
            if not parts:
                continue
                
            command = parts[0]
            args = parts[1:]
            
            if command == "stop":
                running = False
                break
            elif command == "plugins":
                plugins = get_loaded_plugins()
                if plugins:
                    plugin_info = []
                    for plugin in plugins:
                        pid = get_plugin_pid(plugin)
                        plugin_info.append(f"{plugin} (PID: {pid if pid else 'N/A'})")
                    log("INFO", "已加载插件: " + ", ".join(plugin_info))
                else:
                    log("INFO", "没有加载任何插件")
            elif command == "themes":
                themes = get_loaded_themes()
                if themes:
                    theme_pid = get_theme_pid()
                    log("INFO", f"已加载主题: {themes[0]} (PID: {theme_pid if theme_pid else 'N/A'})")
                else:
                    log("INFO", "没有加载任何主题")
            elif command == "unload":
                if len(args) < 2:
                    log("ERROR", "用法: unload [plugin|theme] <名称>")
                else:
                    module_type = args[0]
                    name = args[1]
                    if module_type == "plugin":
                        unload_plugin(name)
                    elif module_type == "theme":
                        unload_theme(name)
                    else:
                        log("ERROR", "无效类型。使用 'plugin' 或 'theme'")
            elif command == "reload":
                if len(args) < 2:
                    log("ERROR", "用法: reload [plugin|theme] <名称>")
                else:
                    module_type = args[0]
                    name = args[1]
                    if module_type == "plugin":
                        reload_plugin(name)
                    elif module_type == "theme":
                        reload_theme(name)
                    else:
                        log("ERROR", "无效类型。使用 'plugin' 或 'theme'")
            elif command == "reloadall":
                reload_all()
            elif command == "restart":
                if len(args) < 2:
                    log("ERROR", "用法: restart [plugin|theme] <名称>")
                else:
                    module_type = args[0]
                    name = args[1]
                    if module_type == "plugin":
                        if unload_plugin(name):
                            reload_plugin(name)
                    elif module_type == "theme":
                        if unload_theme(name):
                            reload_theme(name)
                    else:
                        log("ERROR", "无效类型。使用 'plugin' 或 'theme'")
            elif command == "kill":
                if len(args) < 2:
                    log("ERROR", "用法: kill [plugin|theme] <名称>")
                else:
                    module_type = args[0]
                    name = args[1]
                    if module_type == "plugin":
                        unload_plugin(name)
                    elif module_type == "theme":
                        unload_theme(name)
                    else:
                        log("ERROR", "无效类型。使用 'plugin' 或 'theme'")
            elif command == "help":
                help_text = """
                可用命令:
                  stop         - 停止加载器
                  plugins      - 显示已加载插件
                  themes       - 显示已加载主题
                  unload       - 卸载模块 (用法: unload [plugin|theme] <名称>)
                  reload       - 重新加载模块 (用法: reload [plugin|theme] <名称>)
                  restart      - 重启模块 (用法: restart [plugin|theme] <名称>)
                  kill         - 强制停止模块 (用法: kill [plugin|theme] <名称>)
                  reloadall    - 重新加载所有模块
                  help         - 显示帮助信息
                """
                print(help_text.strip())
            else:
                log("ERROR", f"未知命令: {command}")
        except (EOFError, KeyboardInterrupt):
            running = False
            break
        except Exception as e:
            log("ERROR", f"命令错误: {str(e)}")

def start_console(lang_strings):
    """启动控制台线程"""
    console_thread = threading.Thread(target=console_listener, args=(lang_strings,))
    console_thread.daemon = True
    console_thread.start()
    return console_thread

def stop_console():
    """停止控制台"""
    global running
    running = False