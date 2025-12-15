# -*- coding: utf-8 -*-
# lmoadll_bl platform
#
# @copyright  Copyright (c) 2025 lmoadll_bl team
# @license  GNU General Public License 3.0
"""
数据库适配器模块
包含DatabaseAdapter基类、SQLiteAdapter、MySQLAdapter、PostgreSQLAdapter和DatabaseFactory工厂类。
"""

import os
import logging

try:
    import sqlite3
except ImportError:
    sqlite3 = None
try:
    import pymysql
except ImportError:
    pymysql = None
try:
    import psycopg2
except ImportError:
    psycopg2 = None


class DatabaseAdapter:
    """数据库适配器基类"""

    def __init__(self, config: dict):
        """
        初始化适配器
        
        :param config: 数据库配置字典
        """
        self.config = config
        self.connection = None
        self.cursor = None
        self._in_transaction = False
        # 保存数据库前缀
        self.db_prefix = self.config.get("prefix", "")
        
    def connect(self):
        """建立数据库连接"""
        raise NotImplementedError("子类必须实现connect方法")
        
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None
        
    def execute(self, query: str, params: tuple | None = None):
        """执行SQL查询"""
        if not self.cursor:
            self.connect()
            # 确保connect()成功创建了游标
            if not self.cursor:
                raise RuntimeError("无法创建数据库游标")
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
        except Exception as e:
            logging.error(f"执行SQL查询失败: {query}, 参数: {params}, 错误: {e}")
            raise
            
    def fetchone(self):
        """获取一条查询结果"""
        if not self.cursor:
            raise RuntimeError("没有活动的游标")
        return self.cursor.fetchone()
        
    def fetchall(self):
        """获取所有查询结果"""
        if not self.cursor:
            raise RuntimeError("没有活动的游标")
        return self.cursor.fetchall()
        
    def commit(self):
        """提交事务"""
        if self.connection:
            self.connection.commit()
            self._in_transaction = False
        
    def rollback(self):
        """回滚事务"""
        if self.connection:
            self.connection.rollback()
            self._in_transaction = False
        
    def begin_transaction(self):
        """开始事务"""
        if not self._in_transaction:
            self._in_transaction = True
            # 某些数据库需要在连接级别开始事务
            # 对于支持自动提交的数据库,这里可以留空
        
    def close(self):
        """关闭连接"""
        self.disconnect()
        

        
    def _execute_script(self, sql_script: str):
        """执行SQL脚本"""
        if not self.cursor:
            self.connect()
            # 确保connect()成功创建了游标
            if not self.cursor:
                raise RuntimeError("无法创建数据库游标")
        try:
            self.cursor.executescript(sql_script)
            self.commit()
        except Exception as e:
            logging.error(f"执行SQL脚本失败: {e}")
            self.rollback()
            raise
            
    def _initialize_tables(self):
        """初始化数据库表结构"""
        
        # 创建users表
        users_table = f"{self.db_prefix}users"
        create_users_sql = self._get_create_users_sql(users_table)
        self.execute(create_users_sql)
        
        # 创建options表
        options_table = f"{self.db_prefix}options"
        create_options_sql = self._get_create_options_sql(options_table)
        self.execute(create_options_sql)
        
        # 创建options表索引
        self._create_options_index(options_table)
        
        # 创建用户元数据表
        usermeta_table = f"{self.db_prefix}usermeta"
        create_usermeta_sql = self._get_create_usermeta_sql(usermeta_table, users_table)
        self.execute(create_usermeta_sql)
        
        # 创建usermeta表索引
        self._create_usermeta_indexes(usermeta_table)
        
        # 创建扣子平台服务表
        coze_ai_table = f"{self.db_prefix}coze_ai"
        create_coze_ai_sql = self._get_create_coze_ai_sql(coze_ai_table)
        self.execute(create_coze_ai_sql)
        
        # 创建coze_ai表索引
        self._create_coze_ai_indexes(coze_ai_table)
        
        self.commit()
        
    def _get_create_users_sql(self, users_table):
        """获取创建users表的SQL语句"""
        raise NotImplementedError("子类必须实现此方法")
        
    def _get_create_options_sql(self, options_table):
        """获取创建options表的SQL语句"""
        raise NotImplementedError("子类必须实现此方法")
        
    def _get_create_usermeta_sql(self, usermeta_table, users_table):
        """获取创建usermeta表的SQL语句"""
        raise NotImplementedError("子类必须实现此方法")
        
    def _get_create_coze_ai_sql(self, coze_ai_table):
        """获取创建coze_ai表的SQL语句"""
        raise NotImplementedError("子类必须实现此方法")
        
    def _create_options_index(self, options_table):
        """创建options表索引"""
        create_index_sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {self.db_prefix}options__name_user ON {options_table} (name, user)"
        self.execute(create_index_sql)
        
    def _create_usermeta_indexes(self, usermeta_table):
        """创建usermeta表索引"""
        create_index1_sql = f"CREATE INDEX IF NOT EXISTS {self.db_prefix}usermeta_user_id ON {usermeta_table} (user_id)"
        self.execute(create_index1_sql)
        create_index2_sql = f"CREATE INDEX IF NOT EXISTS {self.db_prefix}usermeta_meta_key ON {usermeta_table} (meta_key)"
        self.execute(create_index2_sql)
        create_index3_sql = f"CREATE INDEX IF NOT EXISTS {self.db_prefix}usermeta_user_meta ON {usermeta_table} (user_id, meta_key)"
        self.execute(create_index3_sql)
        
    def _create_coze_ai_indexes(self, coze_ai_table):
        """创建coze_ai表索引"""
        create_index1_sql = f"CREATE INDEX IF NOT EXISTS {self.db_prefix}coze_ai_user_id ON {coze_ai_table} (user_id)"
        self.execute(create_index1_sql)
        create_index2_sql = f"CREATE INDEX IF NOT EXISTS {self.db_prefix}coze_ai_cozehh_id ON {coze_ai_table} (cozehh_id)"
        self.execute(create_index2_sql)
        create_index3_sql = f"CREATE INDEX IF NOT EXISTS {self.db_prefix}coze_ai_user_cozehh ON {coze_ai_table} (user_id, cozehh_id)"
        self.execute(create_index3_sql)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器"""
    
    def connect(self):
        """建立SQLite数据库连接"""
        try:
            db_path = self.config.get("path")
            if not db_path:
                raise ValueError("SQLite数据库路径未配置")
                
            # 确保数据库文件所在目录存在
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            # logging.info(f"成功连接到SQLite数据库: {db_path}")
            
            # 初始化表结构
            self._initialize_tables()
        except Exception as e:
            logging.error(f"连接SQLite数据库失败: {e}")
            raise
            
    def _get_create_users_sql(self, users_table):
        """获取创建users表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {users_table} (
            uid INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(32) DEFAULT NULL,
            password VARCHAR(64) DEFAULT NULL,
            mail VARCHAR(150) DEFAULT NULL,
            url VARCHAR(150) DEFAULT NULL,
            createdAt INTEGER DEFAULT 0,
            lastLogin INTEGER DEFAULT 0,
            isActive INTEGER DEFAULT 0,
            isLoggedIn INTEGER DEFAULT 0,
            "group" VARCHAR(16) DEFAULT 'visitor'
        )
        """
        
    def _get_create_options_sql(self, options_table):
        """获取创建options表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {options_table} (
            name VARCHAR(32) NOT NULL,
            user INT(10) DEFAULT '0' NOT NULL,
            value TEXT
        )
        """
        
    def _get_create_usermeta_sql(self, usermeta_table, users_table):
        """获取创建usermeta表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {usermeta_table} (
            umeta_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            meta_key VARCHAR(255) NOT NULL,
            meta_value TEXT,
            created_at INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES {users_table} (uid) ON DELETE CASCADE
        )
        """
        
    def _get_create_coze_ai_sql(self, coze_ai_table):
        """获取创建coze_ai表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {coze_ai_table} (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cozehh_id INTEGER NOT NULL,
            name VARCHAR(64) DEFAULT NULL,
            created_at INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES {self.db_prefix}users (uid) ON DELETE CASCADE,
            UNIQUE (user_id, cozehh_id)
        )
        """
        



class MySQLAdapter(DatabaseAdapter):
    """MySQL数据库适配器"""
    
    def connect(self):
        """建立MySQL数据库连接"""
        if pymysql is None:
            raise ImportError("pymysql模块未安装,请使用 'pip install pymysql' 安装")
            
        try:
            self.connection = pymysql.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
                database=self.config.get("database", "lmoadll_bl"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            logging.info(f"成功连接到MySQL数据库: {self.config.get('host')}:{self.config.get('port')}/{self.config.get('database')}")
            
            # 初始化表结构
            self._initialize_tables()
        except Exception as e:
            logging.error(f"连接MySQL数据库失败: {e}")
            raise
            
    def _get_create_users_sql(self, users_table):
        """获取创建users表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {users_table} (
            uid INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(32) DEFAULT NULL,
            password VARCHAR(64) DEFAULT NULL,
            mail VARCHAR(150) DEFAULT NULL,
            url VARCHAR(150) DEFAULT NULL,
            createdAt INTEGER DEFAULT 0,
            lastLogin INTEGER DEFAULT 0,
            isActive INTEGER DEFAULT 0,
            isLoggedIn INTEGER DEFAULT 0,
            `group` VARCHAR(16) DEFAULT 'visitor'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
            
    def _get_create_options_sql(self, options_table):
        """获取创建options表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {options_table} (
            name VARCHAR(32) NOT NULL,
            user INT(10) DEFAULT '0' NOT NULL,
            value TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
            
    def _get_create_usermeta_sql(self, usermeta_table, users_table):
        """获取创建usermeta表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {usermeta_table} (
            umeta_id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER NOT NULL,
            meta_key VARCHAR(255) NOT NULL,
            meta_value TEXT,
            created_at INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES {users_table} (uid) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
            
    def _get_create_coze_ai_sql(self, coze_ai_table):
        """获取创建coze_ai表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {coze_ai_table} (
            id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER NOT NULL,
            cozehh_id INTEGER NOT NULL,
            name VARCHAR(64) DEFAULT NULL,
            created_at INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES {self.db_prefix}users (uid) ON DELETE CASCADE,
            UNIQUE (user_id, cozehh_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL数据库适配器"""
    
    def connect(self):
        """建立PostgreSQL数据库连接"""
        if psycopg2 is None:
            raise ImportError("psycopg2模块未安装,请使用 'pip install psycopg2-binary' 安装")
            
        try:
            self.connection = psycopg2.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                user=self.config.get("user", "postgres"),
                password=self.config.get("password", ""),
                database=self.config.get("database", "lmoadll_bl")
            )
            self.cursor = self.connection.cursor()
            logging.info(f"成功连接到PostgreSQL数据库: {self.config.get('host')}:{self.config.get('port')}/{self.config.get('database')}")
            
            # 初始化表结构
            self._initialize_tables()
        except Exception as e:
            logging.error(f"连接PostgreSQL数据库失败: {e}")
            raise
            
    def execute(self, query: str, params: tuple | None = None):
        """执行SQL查询(PostgreSQL适配)"""
        if not self.cursor:
            self.connect()
            # 确保connect()成功创建了游标
            if not self.cursor:
                raise RuntimeError("无法创建数据库游标")
        try:
            if params:
                # PostgreSQL使用%s作为参数占位符
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
        except Exception as e:
            logging.error(f"执行SQL查询失败: {query}, 参数: {params}, 错误: {e}")
            raise
            
    def _get_create_users_sql(self, users_table):
        """获取创建users表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {users_table} (
            uid SERIAL NOT NULL PRIMARY KEY,
            name VARCHAR(32) DEFAULT NULL,
            password VARCHAR(64) DEFAULT NULL,
            mail VARCHAR(150) DEFAULT NULL,
            url VARCHAR(150) DEFAULT NULL,
            createdAt INTEGER DEFAULT 0,
            lastLogin INTEGER DEFAULT 0,
            isActive INTEGER DEFAULT 0,
            isLoggedIn INTEGER DEFAULT 0,
            "group" VARCHAR(16) DEFAULT 'visitor'
        )
        """
            
    def _get_create_options_sql(self, options_table):
        """获取创建options表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {options_table} (
            name VARCHAR(32) NOT NULL,
            user INTEGER DEFAULT 0 NOT NULL,
            value TEXT
        )
        """
            
    def _get_create_usermeta_sql(self, usermeta_table, users_table):
        """获取创建usermeta表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {usermeta_table} (
            umeta_id SERIAL NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            meta_key VARCHAR(255) NOT NULL,
            meta_value TEXT,
            created_at INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES {users_table} (uid) ON DELETE CASCADE
        )
        """
            
    def _get_create_coze_ai_sql(self, coze_ai_table):
        """获取创建coze_ai表的SQL语句"""
        return f"""
            CREATE TABLE IF NOT EXISTS {coze_ai_table} (
            id SERIAL NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            cozehh_id INTEGER NOT NULL,
            name VARCHAR(64) DEFAULT NULL,
            created_at INTEGER DEFAULT 0,
            updated_at INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES {self.db_prefix}users (uid) ON DELETE CASCADE,
            UNIQUE (user_id, cozehh_id)
        )
        """


class DatabaseFactory:
    """数据库适配器工厂类"""
    
    @staticmethod
    def create_adapter(db_type: str, config: dict) -> DatabaseAdapter:
        """
        创建数据库适配器实例
        
        :param db_type: 数据库类型(sqlite、mysql、postgresql)
        :param config: 数据库配置
        :return: 数据库适配器实例
        """
        if db_type == "sqlite":
            return SQLiteAdapter(config)
        elif db_type == "mysql":
            return MySQLAdapter(config)
        elif db_type == "postgresql":
            return PostgreSQLAdapter(config)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
