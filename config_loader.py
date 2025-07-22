import sys

# 检查Python版本，使用适当的TOML库
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError("Python < 3.11 requires tomli package. Please install with 'pip install tomli'")
import os

class ConfigLoader:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'config.toml')
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'rb') as f:
                return tomllib.load(f)
        except FileNotFoundError:
            raise Exception(f"配置文件 {self.config_path} 不存在")
        except Exception as e:
            raise Exception(f"加载配置文件失败: {str(e)}")

    def get(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)

# 单例模式
config_loader = ConfigLoader()
get_config = config_loader.get