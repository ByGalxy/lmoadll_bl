# -*- coding: utf-8 -*-
from var.lmoadll.toml_config import red_configtoml
import sqlite3
import os


# 创建数据库 
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

        import re
        table_name = f'{db_prefix}users'
        # Validate table_name: only allow alphanumeric and underscores
        if not re.match(r'^\w+$', table_name):
            raise ValueError("Invalid table name. Only alphanumeric characters and underscores are allowed.")
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
