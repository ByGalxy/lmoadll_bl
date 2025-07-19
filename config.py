# -*- coding: utf-8 -*-
# 加载器配置文件

# 目录设置
PLUGINS_DIR = "usr/plugins"  # 插件目录
THEMES_DIR = "usr/themes"    # 主题目录
LANG_DIR = "usr/lang"        # 语言目录

# 语言设置
DEFAULT_LANG = "zh"          # 默认语言

# 终端颜色设置
USE_COLORS = True            # 是否使用终端颜色

# 主题设置
LOAD_ONLY_ONE_THEME = True   # 是否只加载一个主题

# 日志级别颜色配置
LOG_COLORS = {
    "INFO": "94",    # 亮蓝色
    "WARN": "93",    # 亮黄色
    "ERROR": "91",   # 亮红色
    "DEBUG": "92",   # 亮绿色
    "SUCCESS": "95"  # 亮紫色
}