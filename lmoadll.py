import time
import threading
from config import DEFAULT_LANG
from utils import log, print_banner
from language import load_language, get_string
from module_loader import load_plugins, load_themes, unload_all, reload_all
from val.endpoint.console import start_console, stop_console

# 全局状态
running = False

def start_loader():
    global running
    
    if running:
        log("WARN", get_string("already_running"))
        return
    
    # 加载语言文件
    lang_strings = load_language(DEFAULT_LANG)
    
    # 显示启动横幅
    print_banner()
    
    log("INFO", get_string("starting"), lang_strings)
    running = True
    
    # 加载插件和主题
    plugins_ok = load_plugins()
    themes_ok = load_themes()
    
    if not plugins_ok and not themes_ok:
        log("WARN", get_string("no_modules_loaded"), lang_strings)
    
    log("SUCCESS", get_string("start_complete"), lang_strings)
    
    # 启动控制台监听线程
    console_thread = start_console(lang_strings)
    
    try:
        while running:
            # 这里可以添加主循环逻辑
            # 例如处理事件或保持程序运行
            threading.Event().wait(0.1)
    except KeyboardInterrupt:
        stop_loader()
    
    log("INFO", get_string("stopped"), lang_strings)

def stop_loader():
    """
    停止加载器
    """
    global running
    
    if not running:
        return
    
    log("INFO", get_string("stopping"))
    running = False
    stop_console()
    unload_all()
    log("INFO", get_string("cleanup_complete"))

if __name__ == "__main__":
    start_loader()