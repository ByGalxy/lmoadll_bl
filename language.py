import os
import json
import config
from utils import log

lang_strings = {}

def load_language(current_lang):
    """
    加载语言文件
    """
    global lang_strings
    lang_dir = os.path.join(os.path.dirname(__file__), config.LANG_DIR)
    lang_file = os.path.join(lang_dir, f"{current_lang}.json")
    
    try:
        if os.path.exists(lang_file):
            with open(lang_file, 'r', encoding='utf-8') as f:
                lang_strings = json.load(f)
            log("INFO", f"Loaded language file: {current_lang}.json")
        else:
            log("WARN", f"Language file not found: {current_lang}.json")
            
            # 查找可用的语言文件
            available_langs = [f[:-5] for f in os.listdir(lang_dir) 
                              if f.endswith('.json')]
            
            if available_langs:
                # 使用找到的第一个语言文件
                first_lang = available_langs[0]
                lang_file = os.path.join(lang_dir, f"{first_lang}.json")
                
                with open(lang_file, 'r', encoding='utf-8') as f:
                    lang_strings = json.load(f)
                log("INFO", f"Loaded alternative language file: {first_lang}.json")
            else:
                log("ERROR", "No language files found!")
                lang_strings = {}
    except Exception as e:
        log("ERROR", f"Error loading language file: {e}")
        lang_strings = {}
    
    return lang_strings

def get_string(key, default=None):
    """
    获取翻译字符串
    """
    return lang_strings.get(key, default or key)