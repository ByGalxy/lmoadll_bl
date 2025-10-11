"""
-*- coding: utf-8 -*-
usertype:
    - superadministrator / 超级管理员
    - administrator / 管理员
    - regularUser / 普通用户
    - visitor / 访客
"""

from var.toml_config import red_configtoml
from var.toml_config import Doesitexist_configtoml
import sqlite3
import os
import re


__all__ = [
    "sc_verification_db_conn",
    "check_superadmin_exists",
    "get_user_by_username_or_email",
    "get_user_role_by_identity",
    "get_user_count",
    "get_user_name_by_identity",
    "get_or_set_site_option",
    "get_db_connection",
    "get_site_option_by_name",
    "create_site_option"
]


# 创建数据库和表
def sc_verification_db_conn(db_prefix, sql_sqlite_path):
    conn = None
    try:
        red_configtoml("db", "sql_rd", "sqlite3")
        red_configtoml("db", "sql_prefix", db_prefix)

        directory_path = os.path.dirname(sql_sqlite_path)
        if directory_path and not os.path.exists(directory_path):
            os.makedirs(directory_path)

        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()
        table_name = f"{db_prefix}users"
        # 验证表名: 仅允许字母数字和下划线
        if not re.match(r"^\w+$", table_name):
            raise ValueError("无效表名, 只允许使用字母数字字符和下划线.")

        # 创建users表
        create_users_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
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
        cursor.execute(create_users_table_sql)

        # 创建options表
        options_table_name = f"{db_prefix}options"
        create_options_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {options_table_name} (
            name VARCHAR(32) NOT NULL,
            user INT(10) DEFAULT '0' NOT NULL,
            value TEXT
        )
        """
        cursor.execute(create_options_table_sql)

        # 创建唯一索引
        create_index_sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {db_prefix}options__name_user ON {options_table_name} (name, user)"
        cursor.execute(create_index_sql)
        conn.commit()
        red_configtoml("db", "sql_sqlite_path", sql_sqlite_path)
        return [True, 0]
    except sqlite3.Error as e:
        return [False, e]
    finally:
        if conn:
            conn.close()


# 获取数据库连接和配置
def get_db_connection(tablename):
    """获取数据库连接、游标和表名，处理配置检查逻辑"""
    db_prefix = Doesitexist_configtoml("db", "sql_prefix")
    sql_sqlite_path = Doesitexist_configtoml("db", "sql_sqlite_path")
    if not db_prefix or not sql_sqlite_path:
        print("数据库配置缺失")
        return [False, "数据库配置缺失", None, None, None]
    try:
        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()
        table_name = f"{db_prefix}{tablename}"
        return [True, "数据库连接成功", conn, cursor, table_name]
    except sqlite3.Error as e:
        return [False, str(e), None, None, None]


"""
P24
仅修改网站设置
"""
def get_or_set_site_option(
    db_prefix, sql_sqlite_path, option_name, option_value=None, user_id=0
):
    conn = None
    try:
        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()
        table_name = f"{db_prefix}options"

        # 如果提供了option_value，则设置或更新选项
        if option_value is not None:
            # 检查选项是否已存在
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE name = ? AND user = ?",
                (option_name, user_id),
            )
            count = cursor.fetchone()[0]
            print(count)
            if count > 0:
                # 更新现有选项
                cursor.execute(
                    f"UPDATE {table_name} SET value = ? WHERE name = ? AND user = ?",
                    (option_value, option_name, user_id),
                )
            else:
                # 插入新选项
                cursor.execute(
                    f"INSERT INTO {table_name} (name, user, value) VALUES (?, ?, ?)",
                    (option_name, user_id, option_value),
                )

            conn.commit()
            return [True, "网站选项设置成功"]
        else:
            # 如果没有提供option_value，则获取选项
            cursor.execute(
                f"SELECT value FROM {table_name} WHERE name = ? AND user = ?",
                (option_name, user_id),
            )
            result = cursor.fetchone()
            if result:
                return [True, result[0]]
            return [False, "选项不存在"]
    except sqlite3.Error as e:
        return [False, str(e)]
    finally:
        if conn:
            conn.close()


"""
P26
查询网站设置
"""
def get_site_option_by_name(option_name):
    success, message, conn, cursor, _ = get_db_connection('users')
    if not success:
        return [False, message]
    try:
        db_prefix = Doesitexist_configtoml("db", "sql_prefix")
        if not db_prefix:
            return [False, "数据库前缀配置缺失"]

        table_name = f"{db_prefix}options"

        # 查询name
        cursor.execute(
            f"SELECT name, user, value FROM {table_name} WHERE name = ?", (option_name,)
        )
        result = cursor.fetchone()

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
    except sqlite3.Error as e:
        print(f"查询网站设置失败: {e}")
        return [False, str(e)]
    finally:
        if conn:
            conn.close()


# 创建网站设置
def create_site_option(option_name, option_value, user_id=0):
    success, message, conn, cursor, table_name = get_db_connection('options')
    if not success:
        return [False, message]
    try:
        # 插入新选项
        cursor.execute(
            f"INSERT INTO {table_name} (name, user, value) VALUES (?, ?, ?)",
            (option_name, user_id, option_value),
        )
        conn.commit()
        return [True, "网站选项创建成功"]
    except sqlite3.Error as e:
        print(f"创建网站设置失败: {e}")
        return [False, str(e)]
    finally:
        if conn:
            conn.close()


# 根据用户名或邮箱获取用户信息
def get_user_by_username_or_email(db_prefix, sql_sqlite_path, username_or_email):
    conn = None
    try:
        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()

        table_name = f"{db_prefix}users"

        # 查询用户信息
        cursor.execute(
            f"SELECT uid, name, password, mail, `group` FROM {table_name} WHERE mail = ?",
            (username_or_email,),  # 注意这里的逗号，确保是元组格式!!!
        )
        user = cursor.fetchone()

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

    except sqlite3.Error as e:
        print(f"查询用户信息失败: {e}")
        return None
    finally:
        if conn:
            conn.close()


# 检查超级管理员是否存在，如果不存在则创建超级管理员账号，如果存在则返回false
def check_superadmin_exists(
    db_prefix, sql_sqlite_path, admin_username, admin_email, admin_password
):
    conn = None
    try:
        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()

        table_name = f"{db_prefix}users"

        # 检查超级管理员是否已经存在
        cursor.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE `group` = ?",
            ("superadministrator",),
        )
        count = cursor.fetchone()[0]

        if count > 0:
            return [False, "超级管理员账号已存在"]

        # 创建超级管理员账号
        import time

        current_time = int(time.time())

        cursor.execute(
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
        conn.commit()

        return [True, "超级管理员账号创建成功"]

    except sqlite3.Error as e:
        return [False, str(e)]
    finally:
        if conn:
            conn.close()


# 通过用户的uid查找用户的身份权限
def get_user_role_by_identity(user_identity):
    success, message, conn, cursor, table_name = get_db_connection('users')
    if not success:
        return [False, message]

    try:
        cursor.execute(
            f"SELECT `group` FROM {table_name} WHERE uid = ?", (user_identity,)
        )
        user_group = cursor.fetchone()
        return user_group  # 期望返回,如: ('superadministrator',)
    except sqlite3.Error as e:
        print(f"查询用户角色失败: {e}")
        return [False, str(e)]
    finally:
        if conn:
            conn.close()


# 通过用户的uid查找用户名
def get_user_name_by_identity(user_identity):
    success, message, conn, cursor, table_name = get_db_connection('users')
    if not success:
        return [False, message]

    try:
        cursor.execute(f"SELECT name FROM {table_name} WHERE uid = ?", (user_identity,))
        user_name = cursor.fetchone()
        return user_name  # 期望返回,如: ('admin',)
    except sqlite3.Error as e:
        print(f"查询用户名失败: {e}")
        return [False, str(e)]
    finally:
        if conn:
            conn.close()


# 获取用户数量
def get_user_count():
    success, message, conn, cursor, table_name = get_db_connection('users')
    if not success:
        return [False, message]

    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        user_count = cursor.fetchone()[0]
        return user_count
    except sqlite3.Error as e:
        print(f"查询用户数量失败: {e}")
        return [False, str(e)]
    finally:
        if conn:
            conn.close()
