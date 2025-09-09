# -*- coding: utf-8 -*-
from var.lmoadll.toml_config import red_configtoml
import sqlite3
import os


# 创建数据库 
def sc_verification_db_conn(db_prefix, sql_sqlite_path):
    try:
        red_configtoml('db', 'sql_rd', 'sqlite3')
        red_configtoml('db', 'sql_prefix', db_prefix)

        directory_path = os.path.dirname(sql_sqlite_path)
        if directory_path and not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sqlite3.connect(sql_sqlite_path)

        red_configtoml("db", "sql_sqlite_path", sql_sqlite_path)

        return [True, 0]

    except sqlite3.Error as e:
        return [False, e]
