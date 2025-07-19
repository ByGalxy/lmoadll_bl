import time
import config

def color_text(text, color_code):
    """
    添加颜色到文本
    """
    if config.USE_COLORS:
        return f"\033[{color_code}m{text}\033[0m"
    return text

def log(level, message, lang_strings=None):
    """
    带颜色和时间的日志记录
    """
    color_code = config.LOG_COLORS.get(level, "97")
    level_display = color_text(level, color_code)
    timestamp = time.strftime("%H:%M:%S")
    
    if lang_strings and message in lang_strings:
        msg = lang_strings[message]
    else:
        msg = message
    
    print(f"[{timestamp} {level_display}] {msg}")

def print_banner():
    """
    打印启动横幅
    """
    banner = r"""
 __                                          __        __  __  __ 
/  |                                        /  |      /  |/  |/  |
$$ | _____  ____    ______    ______    ____$$ |  ____$$ |$$ |$$ |
$$ |/     \/    \  /      \  /      \  /    $$ | /    $$ |$$ |$$ |
$$ |$$$$$$ $$$$  |/$$$$$$  | $$$$$$  |/$$$$$$$ |/$$$$$$$ |$$ |$$ |
$$ |$$ | $$ | $$ |$$ |  $$ | /    $$ |$$ |  $$ |$$ |  $$ |$$ |$$ |
$$ |$$ | $$ | $$ |$$ \__$$ |/$$$$$$$ |$$ \__$$ |$$ \__$$ |$$ |$$ |
$$ |$$ | $$ | $$ |$$    $$/ $$    $$ |$$    $$ |$$    $$ |$$ |$$ |
$$/ $$/  $$/  $$/  $$$$$$/   $$$$$$$/  $$$$$$$/  $$$$$$$/ $$/ $$/                                    
    """
    print(color_text(banner, "95"))  # 紫色