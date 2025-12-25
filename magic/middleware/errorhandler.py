# -*- coding: utf-8 -*-
#lmoadll_bl platform
#
#@copyright  Copyright (c) 2025 lmoadll_bl team
#@license  GNU General Public License 3.0
"""
错误处理中间件模块

本模块提供统一的错误处理装饰器, 简化try-except代码
"""
import logging
from functools import wraps
from typing import Callable, Any, TypeVar, Optional

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class ErrorHandler:
    """错误处理中间件类"""
    
    def __init__(self, logger_name: str = "magic"):
        self.logger = logging.getLogger(logger_name)
    
    def handle_errors(
        self, 
        error_message: str, 
        default_return: Optional[Any] = None,
        log_level: str = "error"
    ) -> Callable[[F], F]:
        """
        错误处理装饰器
        
        Args:
            error_message: 错误发生时的日志消息模板
            default_return: 发生错误时的默认返回值
            log_level: 日志级别 (error, warning, info, debug)
            
        Returns:
            装饰后的函数
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log_method = getattr(self.logger, log_level, self.logger.error)
                    log_method(f"{error_message}: {e}")
                    return default_return
            return wrapper  # type: ignore
        return decorator
    
    def handle_errors_with_callback(
        self,
        error_message: str,
        error_callback: Optional[Callable[[Exception], Any]] = None,
        log_level: str = "error"
    ) -> Callable[[F], F]:
        """
        带回调的错误处理装饰器
        
        Args:
            error_message: 错误发生时的日志消息模板
            error_callback: 错误发生时的回调函数
            log_level: 日志级别 (error, warning, info, debug)
            
        Returns:
            装饰后的函数
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log_method = getattr(self.logger, log_level, self.logger.error)
                    log_method(f"{error_message}: {e}")
                    if error_callback:
                        return error_callback(e)
                    return None
            return wrapper  # type: ignore
        return decorator

errorhandler = ErrorHandler()

def handle_errors(
    error_message: str, 
    default_return: Optional[Any] = None,
    log_level: str = "error"
) -> Callable[[F], F]:
    """便捷的错误处理装饰器"""
    return errorhandler.handle_errors(error_message, default_return, log_level)

def handle_errors_with_callback(
    error_message: str,
    error_callback: Optional[Callable[[Exception], Any]] = None,
    log_level: str = "error"
) -> Callable[[F], F]:
    """便捷的带回调错误处理装饰器"""
    return errorhandler.handle_errors_with_callback(error_message, error_callback, log_level)
