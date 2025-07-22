from pathlib import Path
import json
from typing import Dict, Optional
from utils import log
from pathlib import Path

from config_loader import get_config

class Localization:
    """
    多语言管理类，负责加载和提供本地化字符串
    
    特性：
    - 支持自动回退语言
    - 详细的错误日志
    - 类型安全的字符串访问
    """
    _instance: Optional['Localization'] = None
    
    def __init__(self, lang_dir: Path):
        """
        :param lang_dir: 语言文件目录路径
        """
        self.lang_dir = lang_dir
        self.strings: Dict[str, str] = {}
        self.current_lang = ''

    @classmethod
    def instance(cls) -> 'Localization':
        """获取单例实例"""

        if cls._instance is None:
            lang_path = (Path(__file__).parent / get_config('directories', 'lang_dir')).resolve()  # 修复Path导入并使用LANG_DIR
            cls._instance = cls(lang_path)  # 已通过resolve()获取绝对路径，无需重复解析
        return cls._instance

    def load_language(self, lang_code: str) -> bool:
        """
        加载指定语言文件
        
        :param lang_code: 语言代码 (如zh_CN)
        :return: 是否加载成功
        """
        self.current_lang = lang_code
        target_file = self.lang_dir / f"{lang_code}.json"  # 确保主语言文件路径包含.json扩展名

        try:
            if not target_file.exists():
                available = self._find_available_languages()
                fallback = self._select_fallback_language(available)
                
                if not fallback:
                    log("ERROR", "No available language files")
                    return False
                
                target_file = self.lang_dir / f"{fallback}.json"  # 添加.json扩展名以正确读取语言文件
                log("WARN", f"Using fallback language: {fallback}")

            with target_file.open(encoding='utf-8') as f:
                self.strings = json.load(f)
                log("INFO", f"Successfully loaded {target_file.name}")
                return True

        except json.JSONDecodeError as e:
            log("ERROR", f"Invalid JSON format in {target_file}: {e}")
        except PermissionError as e:
            log("ERROR", f"Permission denied: {target_file}: {e}")
        except Exception as e:
            log("ERROR", f"Unexpected error loading {target_file}: {e}")
        
        return False

    def _find_available_languages(self) -> list[str]:
        """扫描语言目录获取可用语言列表"""
        return [
            f.stem for f in self.lang_dir.glob("*.json") 
            if f.is_file() and not f.name.startswith('.')
        ]

    def _select_fallback_language(self, available: list[str]) -> Optional[str]:
        """选择备用语言，优先zh_CN"""
        from config_loader import get_config
        priority_list = [get_config('language', 'default_lang')]  # 严格使用用户配置，不启用任何备用语言
        
        for lang in priority_list:
            if lang in available:
                return lang
        return available[0] if available else None

    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        安全获取翻译字符串
        
        :param key: 字符串键
        :param default: 找不到时的默认值
        :return: 翻译后的字符串或占位符
        """
        value = self.strings.get(key)
        
        if not value:
            log("DEBUG", f"Missing translation: {key}")
            return default or f'[{key}]'
            
        return value

# 兼容旧接口
def load_language(current_lang: str) -> dict:
    """[兼容接口] 加载语言文件"""
    instance = Localization.instance()
    success = instance.load_language(current_lang)
    return instance.strings if success else {}

def get_string(key: str, default: Optional[str] = None) -> str:
    """[兼容接口] 获取翻译字符串"""
    return Localization.instance().get(key, default)