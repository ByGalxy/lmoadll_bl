"""
-*- coding: utf-8 -*-
usertype:
    - superadministrator / 超级管理员
    - administrator / 管理员
    - regularUser / 普通用户
    - visitor / 访客
"""

from var.toml_config import red_configtoml
import sqlite3
import os
import re



__all__ = ['sc_verification_db_conn', 'check_superadmin_exists', 'get_user_by_username_or_email']


# 创建数据库和表
def sc_verification_db_conn(db_prefix, sql_sqlite_path):
    conn = None
    try:
        red_configtoml('db', 'sql_rd', 'sqlite3')
        red_configtoml('db', 'sql_prefix', db_prefix)

        directory_path = os.path.dirname(sql_sqlite_path)
        if directory_path and not os.path.exists(directory_path):
            os.makedirs(directory_path)

        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()

        table_name = f'{db_prefix}users'
        # 验证表名: 仅允许字母数字和下划线
        if not re.match(r'^\w+$', table_name):
            raise ValueError("无效表名, 只允许使用字母数字字符和下划线.")
        create_table_sql = f'''CREATE TABLE IF NOT EXISTS {table_name} (
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
        '''

        cursor.execute(create_table_sql)
        conn.commit()

        red_configtoml("db", "sql_sqlite_path", sql_sqlite_path)

        return [True, 0]

    except sqlite3.Error as e:
        return [False, e]
    finally:
        if conn:
            conn.close()


# 根据用户名或邮箱获取用户信息
def get_user_by_username_or_email(db_prefix, sql_sqlite_path, username_or_email):
    conn = None
    try:
        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()
        
        table_name = f'{db_prefix}users'
        
        # 查询用户信息
        cursor.execute(f"SELECT uid, name, password, mail, `group` FROM {table_name} WHERE name = ? OR mail = ?", 
                      (username_or_email, username_or_email))
        user = cursor.fetchone()
        
        if user:
            # 返回用户信息字典
            return {
                'uid': user[0],
                'name': user[1],
                'password': user[2],
                'email': user[3],
                'group': user[4]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"查询用户信息失败: {e}")
        return None
    finally:
        if conn:
            conn.close()


# 检查超级管理员是否存在，如果不存在则创建超级管理员账号，如果存在则返回false
def check_superadmin_exists(db_prefix, sql_sqlite_path, admin_username, admin_email, admin_password):
    conn = None
    try:
        conn = sqlite3.connect(sql_sqlite_path)
        cursor = conn.cursor()
        
        table_name = f'{db_prefix}users'
        
        # 检查超级管理员是否已经存在
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE `group` = ?", ('superadministrator',))
        count = cursor.fetchone()[0]
        
        if count > 0:
            return [False, "超级管理员账号已存在"]
        
        # 创建超级管理员账号
        import time
        current_time = int(time.time())
        
        cursor.execute(f"INSERT INTO {table_name} (name, password, mail, createdAt, isActive, `group`) VALUES (?, ?, ?, ?, ?, ?)",
                      (admin_username, admin_password, admin_email, current_time, 1, 'superadministrator'))
        conn.commit()
        
        return [True, "超级管理员账号创建成功"]
        
    except sqlite3.Error as e:
        return [False, str(e)]
    finally:
        if conn:
            conn.close()
