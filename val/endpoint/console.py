import threading
import config
from utils import color_text, log
from language import get_string
from module_loader import (
    unload_plugin, unload_theme,
    reload_plugin, reload_theme,
    reload_all, get_loaded_plugins,
    get_loaded_themes
)

running = True

def console_listener(lang_strings):
    """
    控制台命令监听器
    """
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
                    log("INFO", "Loaded plugins: " + ", ".join(plugins))
                else:
                    log("INFO", "No plugins loaded")
            elif command == "themes":
                themes = get_loaded_themes()
                if themes:
                    log("INFO", "Loaded themes: " + ", ".join(themes))
                else:
                    log("INFO", "No themes loaded")
            elif command == "unload":
                if len(args) < 2:
                    log("ERROR", "Usage: unload [plugin|theme] <name>")
                else:
                    module_type = args[0]
                    name = args[1]
                    if module_type == "plugin":
                        unload_plugin(name)
                    elif module_type == "theme":
                        unload_theme(name)
                    else:
                        log("ERROR", "Invalid type. Use 'plugin' or 'theme'")
            elif command == "reload":
                if len(args) < 2:
                    log("ERROR", "Usage: reload [plugin|theme] <name>")
                else:
                    module_type = args[0]
                    name = args[1]
                    if module_type == "plugin":
                        reload_plugin(name)
                    elif module_type == "theme":
                        reload_theme(name)
                    else:
                        log("ERROR", "Invalid type. Use 'plugin' or 'theme'")
            elif command == "reloadall":
                reload_all()
            elif command == "help":
                help_text = """
                Available commands:
                  stop         - Stop loader
                  plugins      - Show loaded plugins
                  themes       - Show loaded themes
                  unload       - Unload module (usage: unload [plugin|theme] <name>)
                  reload       - Reload module (usage: reload [plugin|theme] <name>)
                  reloadall    - Reload all modules
                  help         - Show this help
                """
                print(help_text.strip())
            else:
                log("ERROR", f"Unknown command: {command}")
        except (EOFError, KeyboardInterrupt):
            running = False
            break
        except Exception as e:
            log("ERROR", f"Command error: {str(e)}")

def start_console(lang_strings):
    """
    启动控制台线程
    """
    console_thread = threading.Thread(target=console_listener, args=(lang_strings,))
    console_thread.daemon = True
    console_thread.start()
    return console_thread

def stop_console():
    """
    停止控制台
    """
    global running
    running = False