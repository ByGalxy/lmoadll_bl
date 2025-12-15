'''
数据库模块

提供数据库连接池、适配器、模型和工具函数。
'''

from .connection_pool import ConnectionPool
from .adapters import DatabaseAdapter, SQLiteAdapter, MySQLAdapter, PostgreSQLAdapter, DatabaseFactory
from .models import Model, UserModel, OptionModel
from .orm import ORM, db_orm
from .db_utils import (
    CheckSuperadminExists,
    CreateSiteOption,
    InitVerificationDbConn,
    GetDbConnection,
    GetOrSetSiteOption,
    GetSiteOptionByName,
    GetUserByEmail,
    GetUserRoleByIdentity,
    GetUserNameByIdentity,
    GetUserCount,
    SearchUsers,
)

__all__ = [
    # 连接池
    'ConnectionPool',
    # 适配器
    'DatabaseAdapter',
    'SQLiteAdapter',
    'MySQLAdapter',
    'PostgreSQLAdapter',
    'DatabaseFactory',
    # 模型
    'Model',
    'UserModel',
    'OptionModel',
    # ORM核心
    'ORM',
    'db_orm',
    # 工具函数
    'CheckSuperadminExists',
    'CreateSiteOption',
    'InitVerificationDbConn',
    'GetDbConnection',
    'GetOrSetSiteOption',
    'GetSiteOptionByName',
    'GetUserByEmail',
    'GetUserRoleByIdentity',
    'GetUserNameByIdentity',
    'GetUserCount',
    'SearchUsers',
]
