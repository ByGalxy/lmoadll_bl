# -*- coding: utf-8 -*-
"""
目前支持SQLite、MySQL、PostgreSQL数据库
"""
import os
import threading
import time
from queue import Queue, Empty
from var.TomlConfig import DoesitexistConfigToml, WriteConfigToml

try:
    import sqlite3
except ImportError:
    pass
try:
    import pymysql
except ImportError:
    pass
try:
    import psycopg2
except ImportError:
    pass



__all__ = [
    "db_orm",
    "Model",
    "UserModel",
    "OptionModel",
    "CheckSuperadminExists",
    "CreateSiteOption",
    "InitVerificationDbConn",
    "GetDbConnection",
    "GetOrSetSiteOption",
    "GetSiteOptionByName",
    "GetUserByEmail",
    "GetUserRoleByIdentity",
    "GetUserNameByIdentity",
    "GetUserCount"
]


class ConnectionPool:
    """数据库连接池基类"""
    
    def __init__(self, db_type, config, pool_size=5, max_idle_time=300):
        """
        初始化连接池
        
        :param db_type: 数据库类型
        :param config: 数据库配置
        :param pool_size: 连接池大小
        :param max_idle_time: 连接最大空闲时间(秒)

        参数
        ==============================

            * self.db_type
            * self.config
            * self.pool_size
            * self.max_idle_time
            * self.pool
            * self.connection_count
            * self.lock
            * self.closed
        """

        self.db_type = db_type
        """
        数据库类型
            type: str
            取值: 'mysql', 'postgresql', 'sqlite', 'oracle'
            说明: 指定要连接的数据库类型
        """
        
        self.config = config
        """
        数据库配置
            type: dict
            必需键: host, port, user, password, database
            说明: 包含数据库连接所需的所有配置参数
        """

        self.pool_size = pool_size
        """
        连接池大小
            type: int
            默认: 5
            说明: 连接池中维护的最大连接数量
        """

        self.max_idle_time = max_idle_time
        """
        最大空闲时间
            type: int
            单位: 秒
            默认: 300
            说明: 连接在池中空闲的最大时间, 超时将被回收
        """

        self.pool = Queue(maxsize=pool_size)
        """
        连接队列
            type: Queue
            说明: 线程安全的队列, 用于存储和管理可用的数据库连接
        """

        self.connection_count = 0
        """
        连接计数
            type: int
            说明: 当前已创建的连接总数, 用于监控和限制
        """

        self.lock = threading.RLock()
        """
        线程锁
            type: threading.RLock
            说明: 可重入锁, 确保多线程环境下的线程安全操作
        """

        self.closed = False
        """
        连接池状态
            type: bool
            说明: 标记连接池是否已关闭, True时不再接受新请求
        """
        
        # 预创建连接
        for _ in range(pool_size):
            self._create_connection()
    

    def _create_connection(self):
        """创建新的数据库连接"""
        if self.closed:
            return None
        
        try:
            adapter = DatabaseFactory.create_adapter(self.db_type, self.config)
            adapter.connect()
            adapter._created_at = time.time()
            
            with self.lock:
                self.connection_count += 1
            
            return adapter
        except Exception as e:
            print(f"创建数据库连接失败: {e}")
            return None
        

    def _is_connection_valid(self, adapter):
        """验证连接是否有效"""
        # 检查连接是否超时
        idle_time = time.time() - adapter._created_at
        if idle_time > self.max_idle_time:
            return False
        
        # 尝试简单查询验证连接
        try:
            if adapter.db_type == 'sqlite':
                adapter.execute("SELECT 1")
            else:
                adapter.execute("SELECT 1;")
            return True
        except (sqlite3.Error, pymysql.Error, psycopg2.Error, Exception):
            return False
        
    
    def _clean_transaction_state(self, adapter):
        """清理事务状态, 确保连接在不同线程间传递时的一致性"""
        try:
            # 回滚任何未提交的事务
            adapter.rollback()
            # 确保自动提交模式 (可选, 根据需求设置)
            if hasattr(adapter.conn, 'autocommit'):
                adapter.conn.autocommit = True
        except (sqlite3.Error, pymysql.Error, psycopg2.Error, Exception):
            pass
    

    def get_connection(self):
        """从连接池获取连接"""
        if self.closed:
            raise RuntimeError("连接池已关闭")
        
        # 尝试从队列获取连接
        try:
            adapter = self.pool.get_nowait()
        except Empty:
            # 队列为空, 创建新连接
            adapter = self._create_connection()
        
        # 验证连接是否有效且未超时
        if adapter and self._is_connection_valid(adapter):
            # 清理事务状态
            self._clean_transaction_state(adapter)
            return adapter
        
        # 连接无效, 重新创建
        if adapter:
            try:
                adapter.disconnect()
                with self.lock:
                    self.connection_count -= 1
            except (sqlite3.Error, pymysql.Error, psycopg2.Error, Exception):
                pass
        
        return self._create_connection()
    
    
    def return_connection(self, adapter):
        """归还连接到连接池"""
        if self.closed or adapter is None:
            return
        
        try:
            # 更新连接的最后使用时间
            adapter._created_at = time.time()
            # 尝试将连接放回队列
            self.pool.put_nowait(adapter)
        except Exception:
            # 如果队列已满或发生其他错误，关闭连接
            try:
                adapter.disconnect()
                with self.lock:
                    self.connection_count -= 1
            except (sqlite3.Error, pymysql.Error, psycopg2.Error, Exception):
                pass
    
    def close(self):
        """关闭连接池"""
        with self.lock:
            if self.closed:
                return
            self.closed = True
        
        # 关闭所有连接
        while True:
            try:
                adapter = self.pool.get_nowait()
                try:
                    adapter.disconnect()
                except (sqlite3.Error, pymysql.Error, psycopg2.Error, Exception):
                    pass
            except Empty:
                break
        
        with self.lock:
            self.connection_count = 0


class DatabaseAdapter:
    """数据库适配器基类, 定义统一的接口"""
    def __init__(self, config):
        self.config = config
        self.db_type = config.get('type', '')  # 保存数据库类型
        self.conn = None
        self.cursor = None
        self._created_at = time.time()  # 记录连接创建时间
    
    def connect(self):
        """建立数据库连接"""
        raise NotImplementedError
    
    def disconnect(self):
        """关闭数据库连接"""
        raise NotImplementedError
    
    def execute(self, query, params=None):
        """执行SQL查询"""
        raise NotImplementedError
    
    def fetchone(self):
        """获取单条结果"""
        raise NotImplementedError
    
    def fetchall(self):
        """获取所有结果"""
        raise NotImplementedError
    
    def commit(self):
        """提交事务"""
        raise NotImplementedError

    def rollback(self):
        """回滚事务"""
        raise NotImplementedError
    
    def get_connection(self):
        """获取数据库连接"""
        if not self.conn:
            self.connect()
        return self.conn
    
    def get_cursor(self):
        """获取数据库游标"""
        if not self.cursor:
            self.connect()
        return self.cursor
    
    def _initialize_tables(self):
        """初始化数据库表结构"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器"""
    def __init__(self, config):
        super().__init__(config)
        self.db_path = config.get('path', '')
        self.db_prefix = config.get('prefix', '')
        
    def connect(self):
        import sqlite3
        
        # 确保目录存在
        directory_path = os.path.dirname(self.db_path)
        if directory_path and not os.path.exists(directory_path):
            os.makedirs(directory_path)
            
        # check_same_thread=False以支持跨线程使用SQLite连接, 禁止在生产环境False这个
        self.conn = sqlite3.connect(self.db_path, check_same_thread=True)
        self.cursor = self.conn.cursor()
        
        # 初始化表结构
        self._initialize_tables()

    def _initialize_tables(self):
        """初始化数据库表结构"""
        # 创建users表
        users_table = f"{self.db_prefix}users"
        create_users_sql = f"""
            CREATE TABLE IF NOT EXISTS {users_table} (
            uid INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(32) DEFAULT NULL,
            password VARCHAR(64) DEFAULT NULL,
            mail VARCHAR(150) DEFAULT NULL,
            url VARCHAR(150) DEFAULT NULL,
            createdAt INTEGER DEFAULT 0,
            isActive INTEGER DEFAULT 0,
            isLoggedIn INTEGER DEFAULT 0,
            "group" VARCHAR(16) DEFAULT 'visitor'
        )
        """
        self.execute(create_users_sql)
        
        # 创建options表
        options_table = f"{self.db_prefix}options"
        create_options_sql = f"""
            CREATE TABLE IF NOT EXISTS {options_table} (
            name VARCHAR(32) NOT NULL,
            user INT(10) DEFAULT '0' NOT NULL,
            value TEXT
        )
        """
        self.execute(create_options_sql)
        
        # 创建唯一索引
        create_index_sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {self.db_prefix}options__name_user ON {options_table} (name, user)"
        self.execute(create_index_sql)
        
        self.commit()
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def execute(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
    
    def fetchone(self):
        return self.cursor.fetchone()
    
    def fetchall(self):
        return self.cursor.fetchall()
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()


class MySQLAdapter(DatabaseAdapter):
    """MySQL数据库适配器"""
    def __init__(self, config):
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 3306)
        self.user = config.get('user', '')
        self.password = config.get('password', '')
        self.database = config.get('database', '')
        self.charset = config.get('charset', 'utf8mb4')
        self.db_prefix = config.get('prefix', '')
    
    def connect(self):
        import pymysql
        
        self.conn = pymysql.connect(
            host=self.host,
            port=int(self.port),
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset
        )
        self.cursor = self.conn.cursor()
        
        # 初始化表结构
        self._initialize_tables()
    
    def _initialize_tables(self):
        """初始化数据库表结构"""
        # 创建users表
        users_table = f"{self.db_prefix}users"
        create_users_sql = f"""
            CREATE TABLE IF NOT EXISTS {users_table} (
            uid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(32) DEFAULT NULL,
            password VARCHAR(64) DEFAULT NULL,
            mail VARCHAR(150) DEFAULT NULL,
            url VARCHAR(150) DEFAULT NULL,
            createdAt INT DEFAULT 0,
            isActive INT DEFAULT 0,
            isLoggedIn INT DEFAULT 0,
            `group` VARCHAR(16) DEFAULT 'visitor'
        )
        """
        self.execute(create_users_sql)
        
        # 创建options表
        options_table = f"{self.db_prefix}options"
        create_options_sql = f"""
            CREATE TABLE IF NOT EXISTS {options_table} (
            name VARCHAR(32) NOT NULL,
            user INT(10) DEFAULT '0' NOT NULL,
            value TEXT,
            PRIMARY KEY (name, user)
        )
        """
        self.execute(create_options_sql)
        
        self.commit()
    
    def disconnect(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def execute(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
    
    def fetchone(self):
        return self.cursor.fetchone()
    
    def fetchall(self):
        return self.cursor.fetchall()
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL数据库适配器"""
    def __init__(self, config):
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.user = config.get('user', '')
        self.password = config.get('password', '')
        self.database = config.get('database', '')
        self.db_prefix = config.get('prefix', '')
    
    def connect(self):
        import psycopg2
        
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.database
        )
        self.cursor = self.conn.cursor()
        
        # 初始化表结构
        self._initialize_tables()
    
    def _initialize_tables(self):
        """初始化数据库表结构"""
        # 创建users表
        users_table = f"{self.db_prefix}users"
        create_users_sql = f"""
            CREATE TABLE IF NOT EXISTS {users_table} (
            uid SERIAL PRIMARY KEY,
            name VARCHAR(32) DEFAULT NULL,
            password VARCHAR(64) DEFAULT NULL,
            mail VARCHAR(150) DEFAULT NULL,
            url VARCHAR(150) DEFAULT NULL,
            createdAt INTEGER DEFAULT 0,
            isActive INTEGER DEFAULT 0,
            isLoggedIn INTEGER DEFAULT 0,
            "group" VARCHAR(16) DEFAULT 'visitor'
        )
        """
        self.execute(create_users_sql)
        
        # 创建options表
        options_table = f"{self.db_prefix}options"
        create_options_sql = f"""
            CREATE TABLE IF NOT EXISTS {options_table} (
            name VARCHAR(32) NOT NULL,
            user INTEGER DEFAULT 0 NOT NULL,
            value TEXT,
            PRIMARY KEY (name, user)
        )
        """
        self.execute(create_options_sql)
        
        self.commit()
    
    def disconnect(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def execute(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
    
    def fetchone(self):
        return self.cursor.fetchone()
    
    def fetchall(self):
        return self.cursor.fetchall()
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()


class DatabaseFactory:
    """数据库工厂类，用于创建不同类型的数据库适配器"""
    @staticmethod
    def create_adapter(db_type, config):
        """创建数据库适配器实例"""
        adapters = {
            'sqlite': SQLiteAdapter,
            'mysql': MySQLAdapter,
            'postgresql': PostgreSQLAdapter
        }
        
        adapter_class = adapters.get(db_type)
        if not adapter_class:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        
        return adapter_class(config)


class Model:
    """ORM模型基类"""
    _table_name = None
    _primary_key = 'uid'
    
    @classmethod
    def set_table_name(cls, table_name):
        """设置表名"""
        cls._table_name = table_name
    
    @classmethod
    def get_table_name(cls):
        """获取表名"""
        if not cls._table_name:
            # 默认使用类名的小写形式作为表名
            cls._table_name = cls.__name__.lower()
        return cls._table_name
    
    @classmethod
    def find(cls, db, **kwargs):
        """根据条件查找记录"""
        table_name = cls.get_table_name()
        
        # 构建查询条件
        if not kwargs:
            query = f"SELECT * FROM {table_name}"
            params = None
        else:
            conditions = []
            params = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            
            # 替换参数占位符为数据库特定的格式
            query = f"SELECT * FROM {table_name} WHERE {' AND '.join(conditions)}"
            if db.config.get('type') == 'mysql':
                query = query.replace('?', '%s')
            elif db.config.get('type') == 'postgresql':
                query = query.replace('?', '%s')
        
        db.execute(query, params)
        return db.fetchall()
    
    @classmethod
    def find_by_id(cls, db, id_value):
        """根据主键查找记录"""
        table_name = cls.get_table_name()
        query = f"SELECT * FROM {table_name} WHERE {cls._primary_key} = ?"
        
        # 替换参数占位符为数据库特定的格式
        if db.config.get('type') == 'mysql':
            query = query.replace('?', '%s')
        elif db.config.get('type') == 'postgresql':
            query = query.replace('?', '%s')
        
        db.execute(query, [id_value])
        return db.fetchone()
    
    @classmethod
    def create(cls, db, **kwargs):
        """创建新记录"""
        table_name = cls.get_table_name()
        
        # 构建插入语句
        columns = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?' for _ in kwargs])
        params = list(kwargs.values())
        
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        # 替换参数占位符为数据库特定的格式
        if db.config.get('type') == 'mysql':
            query = query.replace('?', '%s')
        elif db.config.get('type') == 'postgresql':
            query = query.replace('?', '%s')
        
        db.execute(query, params)
        db.commit()
        
        # 返回插入的ID
        if db.config.get('type') == 'sqlite':
            return db.cursor.lastrowid
        elif db.config.get('type') == 'mysql':
            db.execute("SELECT LAST_INSERT_ID()")
            return db.fetchone()[0]
        elif db.config.get('type') == 'postgresql':
            db.execute("SELECT CURRVAL(pg_get_serial_sequence('%s', '%s'))" % (table_name, cls._primary_key))
            return db.fetchone()[0]
    
    @classmethod
    def update(cls, db, id_value, **kwargs):
        """更新记录"""
        table_name = cls.get_table_name()
        
        # 构建更新语句
        updates = []
        params = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            params.append(value)
        params.append(id_value)
        
        query = f"UPDATE {table_name} SET {' ,'.join(updates)} WHERE {cls._primary_key} = ?"
        
        # 替换参数占位符为数据库特定的格式
        if db.config.get('type') == 'mysql':
            query = query.replace('?', '%s')
        elif db.config.get('type') == 'postgresql':
            query = query.replace('?', '%s')
        
        db.execute(query, params)
        db.commit()
        
        return db.cursor.rowcount
    
    @classmethod
    def delete(cls, db, id_value):
        """删除记录"""
        table_name = cls.get_table_name()
        
        query = f"DELETE FROM {table_name} WHERE {cls._primary_key} = ?"
        
        # 替换参数占位符为数据库特定的格式
        if db.config.get('type') == 'mysql':
            query = query.replace('?', '%s')
        elif db.config.get('type') == 'postgresql':
            query = query.replace('?', '%s')
        
        db.execute(query, [id_value])
        db.commit()
        
        return db.cursor.rowcount


class UserModel(Model):
    """用户模型"""
    _primary_key = 'uid'


class OptionModel(Model):
    """选项模型"""
    _primary_key = 'name'


class ORM:
    """ORM主类, 提供统一的数据库操作接口"""
    _instance = None
    _pools = {}  # 使用连接池替换直接的适配器
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """确保初始化只执行一次"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._default_db = None
    
    def register_db(self, name, db_type, config, pool_size=5):
        """注册数据库连接"""
        config['type'] = db_type  # 保存数据库类型
        
        # 创建连接池而不是直接的适配器
        pool = ConnectionPool(db_type, config, pool_size=pool_size)
        self._pools[name] = pool
        
        # 如果是第一个注册的数据库，设置为默认数据库
        if self._default_db is None:
            self._default_db = name
    
    def get_db(self, name=None):
        """从连接池获取数据库连接"""
        if name is None:
            name = self._default_db
        
        if name not in self._pools:
            raise ValueError(f"未注册的数据库: {name}")
        
        # 从连接池获取连接
        return self._pools[name].get_connection()
    
    def return_db(self, adapter, name=None):
        """归还数据库连接到连接池"""
        if name is None:
            name = self._default_db
        
        if name in self._pools:
            self._pools[name].return_connection(adapter)
    
    def set_default_db(self, name):
        """设置默认数据库"""
        if name not in self._pools:
            raise ValueError(f"未注册的数据库: {name}")
        
        self._default_db = name
    
    def close_all(self):
        """关闭所有连接池"""
        for pool in self._pools.values():
            pool.close()
        self._pools.clear()

db_orm = ORM()
"""全局ORM实例"""


def CheckSuperadminExists(db_prefix, sql_sqlite_path, admin_username, admin_email, admin_password):
    """检查超级管理员是否存在"""
    db = None
    try:
        # 确保default数据库已注册到连接池
        if 'default' not in db_orm._pools:
            db_orm.register_db('default', 'sqlite', {
                'path': sql_sqlite_path,
                'prefix': db_prefix,
                'type': 'sqlite'
            })
        
        # 从连接池获取连接
        db = db_orm.get_db('default')
        
        table_name = f"{db_prefix}users"
        
        # 检查超级管理员是否已经存在
        db.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE `group` = ?",
            ("superadministrator",)
        )
        count = db.fetchone()[0]
        
        if count > 0:
            return [False, "超级管理员账号已存在"]
        
        # 创建超级管理员账号
        import time
        current_time = int(time.time())
        
        db.execute(
            f"INSERT INTO {table_name} (name, password, mail, createdAt, isActive, `group`) VALUES (?, ?, ?, ?, ?, ?)",
            (
                admin_username,
                admin_password,
                admin_email,
                current_time,
                1,
                "superadministrator",
            ),
        )
        db.commit()
        
        return [True, "超级管理员账号创建成功"]
    except Exception as e:
        return [False, str(e)]
    finally:
        # 归还连接到连接池
        if db:
            db_orm.return_db(db, 'default')


def CreateSiteOption(option_name, option_value, user_id=0):
    """创建网站设置"""
    success, message, db, cursor, table_name = GetDbConnection('options')
    if not success:
        return [False, message]
    
    try:
        # 插入新选项
        db.execute(
            f"INSERT INTO {table_name} (name, user, value) VALUES (?, ?, ?)",
            (option_name, user_id, option_value)
        )
        db.commit()
        return [True, "网站选项创建成功"]
    except Exception as e:
        print(f"创建网站设置失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            # 归还连接到连接池而不是直接关闭
            db_orm.return_db(db, 'default')


def InitVerificationDbConn(db_type, **kwargs):
    """验证数据库连接并初始化"""
    
    try:
        if db_type == 'sqlite':
            db_path = kwargs.get('sql_sqlite_path', '')
            db_prefix = kwargs.get('db_prefix', '')
            
            # 保存配置
            WriteConfigToml("db", "sql_rd", "sqlite3")
            WriteConfigToml("db", "sql_prefix", db_prefix)
            WriteConfigToml("db", "sql_sqlite_path", db_path)
            
            # 注册数据库
            db_orm.register_db('default', 'sqlite', {
                'path': db_path,
                'prefix': db_prefix
            })
            
            # 测试连接
            db = db_orm.get_db()
            db.connect()
            db.disconnect()
            
            return [True, 0]
        elif db_type == 'mysql':
            db_host = kwargs.get('db_host', 'localhost')
            db_port = kwargs.get('db_port', 3306)
            db_name = kwargs.get('db_name', '')
            db_user = kwargs.get('db_user', '')
            db_password = kwargs.get('db_password', '')
            db_prefix = kwargs.get('db_prefix', '')
            
            # 保存配置
            WriteConfigToml("db", "sql_rd", "mysql")
            WriteConfigToml("db", "sql_prefix", db_prefix)
            
            # 注册数据库
            db_orm.register_db('default', 'mysql', {
                'host': db_host,
                'port': db_port,
                'user': db_user,
                'password': db_password,
                'database': db_name,
                'prefix': db_prefix
            })
            
            # 测试连接
            db = db_orm.get_db()
            db.connect()
            db.disconnect()
            
            return [True, 0]
        elif db_type == 'postgresql':
            db_host = kwargs.get('db_host', 'localhost')
            db_port = kwargs.get('db_port', 5432)
            db_name = kwargs.get('db_name', '')
            db_user = kwargs.get('db_user', '')
            db_password = kwargs.get('db_password', '')
            db_prefix = kwargs.get('db_prefix', '')
            
            # 保存配置
            WriteConfigToml("db", "sql_rd", "postgresql")
            WriteConfigToml("db", "sql_prefix", db_prefix)
            
            # 注册数据库
            db_orm.register_db('default', 'postgresql', {
                'host': db_host,
                'port': db_port,
                'user': db_user,
                'password': db_password,
                'database': db_name,
                'prefix': db_prefix
            })
            
            # 测试连接
            db = db_orm.get_db()
            db.connect()
            db.disconnect()
            
            return [True, 0]
        else:
            return [False, f"不支持的数据库类型: {db_type}"]
    except Exception as e:
        return [False, str(e)]


def GetDbConnection(tablename=None):
    """从连接池获取数据库连接"""
    try:
        db_type = DoesitexistConfigToml("db", "sql_rd")
        db_prefix = DoesitexistConfigToml("db", "sql_prefix")
        
        if not db_type or not db_prefix:
            return [False, "数据库配置缺失", None, None, None]
        
        # 确保default数据库已注册到连接池
        if 'default' not in db_orm._pools:
            # 根据数据库类型获取配置并注册
            if db_type == 'sqlite3':
                sql_sqlite_path = DoesitexistConfigToml("db", "sql_sqlite_path")
                if not sql_sqlite_path:
                    return [False, "SQLite路径配置缺失", None, None, None]
                
                db_orm.register_db('default', 'sqlite', {
                    'path': sql_sqlite_path,
                    'prefix': db_prefix,
                    'type': 'sqlite'
                })
            elif db_type == 'mysql':
                # 从配置中获取MySQL连接信息
                db_host = DoesitexistConfigToml("db", "sql_host", "localhost")
                db_port = DoesitexistConfigToml("db", "sql_port", 3306)
                db_name = DoesitexistConfigToml("db", "sql_database", "lmoadll_bl")
                db_user = DoesitexistConfigToml("db", "sql_user", "root")
                db_password = DoesitexistConfigToml("db", "sql_password", "")
                
                db_orm.register_db('default', 'mysql', {
                    'host': db_host,
                    'port': db_port,
                    'user': db_user,
                    'password': db_password,
                    'database': db_name,
                    'prefix': db_prefix,
                    'type': 'mysql'
                })
            elif db_type == 'postgresql':
                # 从配置中获取PostgreSQL连接信息
                db_host = DoesitexistConfigToml("db", "sql_host", "localhost")
                db_port = DoesitexistConfigToml("db", "sql_port", 5432)
                db_name = DoesitexistConfigToml("db", "sql_database", "lmoadll_bl")
                db_user = DoesitexistConfigToml("db", "sql_user", "postgres")
                db_password = DoesitexistConfigToml("db", "sql_password", "")
                
                db_orm.register_db('default', 'postgresql', {
                    'host': db_host,
                    'port': db_port,
                    'user': db_user,
                    'password': db_password,
                    'database': db_name,
                    'prefix': db_prefix,
                    'type': 'postgresql'
                })
            else:
                return [False, f"不支持的数据库类型: {db_type}", None, None, None]
        
        # 从连接池获取连接
        db = db_orm.get_db('default')
        
        table_name = f"{db_prefix}{tablename}" if tablename else None
        
        return [True, "数据库连接成功", db, db.cursor, table_name]
    except Exception as e:
        return [False, str(e), None, None, None]


def GetOrSetSiteOption(db_prefix, sql_sqlite_path, option_name, option_value=None, user_id=0):
    """获取或设置网站选项"""
    db = None
    try:
        # 确保default数据库已注册到连接池
        if 'default' not in db_orm._pools:
            db_orm.register_db('default', 'sqlite', {
                'path': sql_sqlite_path,
                'prefix': db_prefix,
                'type': 'sqlite'
            })
        
        # 从连接池获取连接
        db = db_orm.get_db('default')
        
        table_name = f"{db_prefix}options"
        
        # 如果提供了option_value，则设置或更新选项
        if option_value is not None:
            # 检查选项是否已存在
            db.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE name = ? AND user = ?",
                (option_name, user_id)
            )
            count = db.fetchone()[0]
            
            if count > 0:
                # 更新现有选项
                db.execute(
                    f"UPDATE {table_name} SET value = ? WHERE name = ? AND user = ?",
                    (option_value, option_name, user_id)
                )
            else:
                # 插入新选项
                db.execute(
                    f"INSERT INTO {table_name} (name, user, value) VALUES (?, ?, ?)",
                    (option_name, user_id, option_value)
                )
            
            db.commit()
            return [True, "网站选项设置成功"]
        else:
            # 如果没有提供option_value，则获取选项
            db.execute(
                f"SELECT value FROM {table_name} WHERE name = ? AND user = ?",
                (option_name, user_id)
            )
            result = db.fetchone()
            
            if result:
                return [True, result[0]]
            return [False, "选项不存在"]
    except Exception as e:
        return [False, str(e)]
    finally:
        # 归还连接到连接池
        if db:
            db_orm.return_db(db, 'default')


def GetSiteOptionByName(option_name):
    """查询网站设置"""
    success, message, db, cursor, _ = GetDbConnection('users')
    if not success:
        return [False, message]
    
    try:
        db_prefix = DoesitexistConfigToml("db", "sql_prefix")
        if not db_prefix:
            return [False, "数据库前缀配置缺失"]
        
        table_name = f"{db_prefix}options"
        
        # 查询name
        db.execute(
            f"SELECT name, user, value FROM {table_name} WHERE name = ?", (option_name,)
        )
        result = db.fetchone()
        
        if result:
            name, user, value = result
            """
            为了安全,先判断user是否为0
                - True, 返回name、user、value
                - False, 跳过, 等后面添加功能
            """
            if user == 0:
                return [True, {"name": name, "user": user, "value": value}]
            else:
                # 如果user不是0，则跳过
                return [True, None]
        else:
            return [False, "未找到指定的设置"]
    except Exception as e:
        print(f"查询网站设置失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            # 归还连接到连接池而不是直接关闭
            db_orm.return_db(db, 'default')


def GetUserByEmail(db_prefix, sql_sqlite_path, username_email):
    """根据用户名或邮箱获取用户信息"""
    db = None
    try:
        # 确保default数据库已注册到连接池
        if 'default' not in db_orm._pools:
            db_orm.register_db('default', 'sqlite', {
                'path': sql_sqlite_path,
                'prefix': db_prefix,
                'type': 'sqlite'
            })
        
        # 从连接池获取连接
        db = db_orm.get_db('default')
        
        table_name = f"{db_prefix}users"
        
        # 查询用户信息
        db.execute(
            f"SELECT uid, name, password, mail, `group` FROM {table_name} WHERE mail = ?",
            (username_email,)
        )
        user = db.fetchone()
        
        if user:
            # 返回用户信息字典
            return {
                "uid": user[0],
                "name": user[1],
                "password": user[2],
                "email": user[3],
                "group": user[4],
            }
        return None
    except Exception as e:
        print(f"查询用户信息失败: {e}")
        return None
    finally:
        # 归还连接到连接池
        if db:
            db_orm.return_db(db, 'default')


def GetUserRoleByIdentity(user_identity):
    """通过用户的uid查找用户的身份权限"""
    success, message, db, cursor, table_name = GetDbConnection('users')
    if not success:
        return [False, message]
    
    try:
        db.execute(
            f"SELECT `group` FROM {table_name} WHERE uid = ?", (user_identity,)
        )
        user_group = db.fetchone()
        return user_group  # 期望返回,如: ('superadministrator',)
    except Exception as e:
        print(f"查询用户角色失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            # 归还连接到连接池而不是直接关闭
            db_orm.return_db(db, 'default')


def GetUserNameByIdentity(user_identity):
    """通过用户的uid查找用户名"""
    success, message, db, cursor, table_name = GetDbConnection('users')
    if not success:
        return [False, message]
    
    try:
        db.execute(f"SELECT name FROM {table_name} WHERE uid = ?", (user_identity,))
        user_name = db.fetchone()
        return user_name  # 期望返回,如: ('admin',)
    except Exception as e:
        print(f"查询用户名失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            # 归还连接到连接池而不是直接关闭
            db_orm.return_db(db, 'default')


def GetUserCount():
    """获取用户数量"""
    success, message, db, cursor, table_name = GetDbConnection('users')
    if not success:
        return [False, message]
    
    try:
        db.execute(f"SELECT COUNT(*) FROM {table_name}")
        user_count = db.fetchone()[0]
        return user_count
    except Exception as e:
        print(f"查询用户数量失败: {e}")
        return [False, str(e)]
    finally:
        if db:
            # 归还连接到连接池而不是直接关闭
            db_orm.return_db(db, 'default')
