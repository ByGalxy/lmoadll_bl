#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型模块

包含ORM模型基类及核心数据模型。
"""
from __future__ import annotations
from magic.utils.db.adapters import DatabaseAdapter


class Model():
    """ORM模型基类"""

    _table_name: str | None = None
    _primary_key: str = "uid"

    @classmethod
    def set_table_name(cls, table_name: str):
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
    def find(cls, db: DatabaseAdapter, **kwargs: str) -> object:
        """根据条件查找记录"""
        table_name = cls.get_table_name()

        # 构建查询条件
        if not kwargs:
            query = f"SELECT * FROM {table_name}"
            params = None
        else:
            conditions: list[str] = []
            params_list: list[object] = []
            for key, value in kwargs.items():
                conditions.append(f"{key} = ?")
                params_list.append(value)

            # 替换参数占位符为数据库特定的格式
            query = f"SELECT * FROM {table_name} WHERE {' AND '.join(conditions)}"
            if db.config.get("type") == "mysql":
                query = query.replace("?", "%s")
            elif db.config.get("type") == "postgresql":
                query = query.replace("?", "%s")

            params = tuple(params_list) if params_list else None

        db.execute(query, params)
        return db.fetchall()

    @classmethod
    def find_by_id(cls, db, id_value):
        """根据主键查找记录"""
        table_name = cls.get_table_name()
        query = f"SELECT * FROM {table_name} WHERE {cls._primary_key} = ?"

        # 替换参数占位符为数据库特定的格式
        if db.config.get("type") == "mysql":
            query = query.replace("?", "%s")
        elif db.config.get("type") == "postgresql":
            query = query.replace("?", "%s")

        db.execute(query, (id_value,))
        return db.fetchone()

    @classmethod
    def create(cls, db, **kwargs):
        """创建新记录"""
        table_name = cls.get_table_name()

        # 构建插入语句
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?" for _ in kwargs])
        params_list = list(kwargs.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # 替换参数占位符为数据库特定的格式
        if db.config.get("type") == "mysql":
            query = query.replace("?", "%s")
        elif db.config.get("type") == "postgresql":
            query = query.replace("?", "%s")

        db.execute(query, tuple(params_list))
        db.commit()

        # 返回插入的ID
        if db.config.get("type") == "sqlite":
            return db.cursor.lastrowid
        elif db.config.get("type") == "mysql":
            db.execute("SELECT LAST_INSERT_ID()")
            return db.fetchone()[0]
        elif db.config.get("type") == "postgresql":
            db.execute(
                "SELECT CURRVAL(pg_get_serial_sequence('%s', '%s'))"
                % (table_name, cls._primary_key)
            )
            return db.fetchone()[0]

    @classmethod
    def update(cls, db, id_value, **kwargs):
        """更新记录"""
        table_name = cls.get_table_name()

        # 构建更新语句
        updates = []
        params_list: list[object] = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            params_list.append(value)
        # 将 id 放到参数末尾
        params_list.append(id_value)

        query = (
            f"UPDATE {table_name} SET {' ,'.join(updates)} WHERE {cls._primary_key} = ?"
        )

        # 替换参数占位符为数据库特定的格式
        if db.config.get("type") == "mysql":
            query = query.replace("?", "%s")
        elif db.config.get("type") == "postgresql":
            query = query.replace("?", "%s")

        db.execute(query, tuple(params_list))
        db.commit()

        return db.cursor.rowcount

    @classmethod
    def delete(cls, db, id_value):
        """删除记录"""
        table_name = cls.get_table_name()

        query = f"DELETE FROM {table_name} WHERE {cls._primary_key} = ?"

        # 替换参数占位符为数据库特定的格式
        if db.config.get("type") == "mysql":
            query = query.replace("?", "%s")
        elif db.config.get("type") == "postgresql":
            query = query.replace("?", "%s")

        db.execute(query, (id_value,))
        db.commit()

        return db.cursor.rowcount


class UserModel(Model):
    """用户模型"""

    _primary_key = "uid"


class OptionModel(Model):
    """选项模型"""

    _primary_key = "name"
