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
    带颜色和时间的日志记录 - 通过队列输出
    """
    from var.lmoadll.endpoint.console import log_queue
    
    if lang_strings and message in lang_strings:
        msg = lang_strings[message]
    else:
        msg = message
    
    # 发送到日志队列而不是直接打印
    log_queue.put((level, msg))

def print_banner():
    """
    打印启动横幅
    Ciallo～(∠・ω< )⌒☆ 𝑪𝒊𝒂𝒍𝒍𝒐～(∠・ω< )⌒☆ 𝓒𝓲𝓪𝓵𝓵𝓸～(∠・ω< )⌒☆ 𝐂𝐢𝐚𝐥𝐥𝐨～(∠・ω< )⌒☆ ℂ𝕚𝕒𝕝𝕝𝕠～(∠・ω< )⌒☆ 𝘊𝘪𝘢𝘭𝘭𝘰～(∠・ω< )⌒☆ 𝗖𝗶𝗮𝗹𝗹𝗼～(∠・ω< )⌒☆ 𝙲𝚒𝚊𝚕𝚕𝚘～(∠・ω< )⌒☆ ᴄɪᴀʟʟᴏ～(∠・ω< )⌒☆ 𝕮𝖎𝖆𝖑𝖑𝖔～(∠・ω< )⌒☆ ℭ𝔦𝔞𝔩𝔩𝔬～(∠・ω< )⌒☆ ᶜⁱᵃˡˡᵒ～(∠・ω< )⌒☆ ᑕ⫯Ꭿ𝘭𝘭𝖮～(∠・ω< )⌒☆ ☆⌒( >ω・∠)～ollɐıɔ
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