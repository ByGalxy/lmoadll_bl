import colorama
colorama.init(autoreset=True)
import sys
import time
import queue
import os
import msvcrt
import threading
from utils import color_text
from language import get_string
from module_loader import (
    unload_plugin, unload_theme,
    reload_plugin, reload_theme,
    reload_all, get_loaded_plugins,
    get_loaded_themes, get_plugin_pid,
    get_theme_pid
)

# 创建队列和输出锁
log_queue = queue.Queue()
running = True
output_lock = threading.Lock()
logger_thread = None


class LoggerThread(threading.Thread):
    """日志输出线程"""
    def __init__(self):
        super().__init__()
        self.daemon = True
        
    def run(self):
        global running
        while running:
            try:
                # 检查队列是否有消息，但不阻塞
                if not log_queue.empty():
                    # 从队列获取日志消息
                    level, message = log_queue.get_nowait()
                    
                    with output_lock:
                        # 先清除当前行
                        sys.stdout.write("\r\033[K")
                        # 输出日志
                        timestamp = time.strftime("%H:%M:%S")
                        color_code = LOG_COLORS.get(level, "97")
                        level_display = color_text(level, color_code)
                        sys.stdout.write(f"[{timestamp} {level_display}] {message}\n")
                        # 在新行显示提示符
                        sys.stdout.write(color_text("> ", "96"))
                        sys.stdout.flush()
                    
                    log_queue.task_done()
                else:
                    # 短暂休眠，减少CPU使用率
                    time.sleep(0.05)
            except Exception as e:
                with output_lock:
                    sys.stdout.write(f"\n[SYSTEM ERROR] 日志线程错误: {str(e)}\n")
                    sys.stdout.write(color_text("> ", "96"))
                    sys.stdout.flush()
        
        # 线程退出前的清理工作
        with output_lock:
            sys.stdout.write("\n[INFO] 日志线程已停止\n")
            sys.stdout.flush()


def log(level, message):
    """发送日志到队列"""
    log_queue.put((level, message))




def console_listener(lang_strings):
    """控制台命令监听器"""
    global running, logger_thread
    
    # 启动日志线程
    logger_thread = LoggerThread()
    logger_thread.start()
    
    # 显示初始提示符
    print(color_text("> ", "96"), end="", flush=True)
    
    while running:
        try:
            # 检查是否有键盘输入（非阻塞）
            if msvcrt.kbhit():
                # 读取输入行
                cmd = sys.stdin.readline().strip().lower()
                
                # 清屏并处理命令
                parts = cmd.split()
                
                if not parts:
                    # 重新显示提示符
                    print(color_text("> ", "96"), end="", flush=True)
                    continue
                     
                command = parts[0]
                args = parts[1:]
                
                if command == "stop":
                    running = False
                    log("INFO", "正在停止加载器...")
                    stop_console()
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
                    if themes and (theme_pid := get_theme_pid()):
                        log("INFO", f"已加载主题: {themes[0]} (PID: {theme_pid})")
                    elif themes:
                        log("INFO", f"已加载主题: {themes[0]} (PID: N/A)")
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
                    # 保存光标位置
                    sys.stdout.write("\033[s")
                    # 移动到上一行并清除
                    sys.stdout.write("\033[1A\033[K")
                    # 输出帮助信息
                    print(help_text.strip())
                    # 恢复光标位置并显示提示符
                    sys.stdout.write("\033[u")
                else:
                    log("ERROR", f"未知命令: {command}")
                
                # 重新显示提示符
                print(color_text("> ", "96"), end="", flush=True)
            else:
                # 没有输入，短暂休眠以减少CPU使用率
                time.sleep(0.05)
        except (EOFError, KeyboardInterrupt):
            running = False
            log("INFO", "捕获到退出信号，正在停止加载器...")
            stop_console()
            break
        except Exception as e:
            log("ERROR", f"命令错误: {str(e)}")
            # 重新显示提示符
            print(color_text("> ", "96"), end="", flush=True)



def start_console(lang_strings):
    """启动控制台线程"""
    
    console_thread = threading.Thread(target=console_listener, args=(lang_strings,))
    console_thread.daemon = True
    console_thread.start()
    
    return console_thread

def stop_console():
    """停止控制台"""
    global running, logger_thread
    running = False
    
    # 发送终止信号
    with output_lock:
        sys.stdout.write("\n\033[91m[SYSTEM] 正在停止加载器...\033[0m\n")
        sys.stdout.flush()
    
    # 等待日志线程结束
    if logger_thread and logger_thread.is_alive():
        logger_thread.join(timeout=1.0)  # 设置1秒超时，避免无限等待
    
    # 确保日志队列为空
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
            log_queue.task_done()
        except queue.Empty:
            break
    
    # 显示停止信息
    with output_lock:
        sys.stdout.write("[INFO] 控制台已停止\n")
        sys.stdout.write("[INFO] 所有资源已清理完毕\n")
        sys.stdout.flush()
    
    # 强制退出程序
    os._exit(0)

LOG_COLORS = {
    'INFO': '94',    # 亮蓝色
    'WARN': '93',    # 亮黄色
    'ERROR': '91',   # 亮红色
    'DEBUG': '92',   # 亮绿色
    'SUCCESS': '95'  # 亮紫色
}