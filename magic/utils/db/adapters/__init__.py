"""
数据库适配器模块
包含DatabaseAdapter基类、SQLiteAdapter、MySQLAdapter、PostgreSQLAdapter和DatabaseFactory工厂类。
"""

from .adapters import (
    DatabaseAdapter,
    SQLiteAdapter,
    MySQLAdapter,
    PostgreSQLAdapter,
    DatabaseFactory
)

__all__ = [
    'DatabaseAdapter',
    'SQLiteAdapter',
    'MySQLAdapter',
    'PostgreSQLAdapter',
    'DatabaseFactory'
]
