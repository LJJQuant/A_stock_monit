# -*- coding: utf-8 -*-
"""
数据仓库基类

提供 DuckDB 表操作的通用方法。
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import duckdb
import pandas as pd
from duckdb import DuckDBPyConnection

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    数据仓库基类

    提供 DuckDB 连接管理和通用表操作。

    Parameters
    ----------
    db_path : Path
        DuckDB 数据库文件路径

    Notes
    -----
    子类需要实现:
    - TABLE_NAME: 表名常量
    - _create_table_sql(): 返回建表SQL
    """

    TABLE_NAME: str = ""  # 子类必须定义

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._ensure_db_dir()
        self._ensure_table()

    def _ensure_db_dir(self) -> None:
        """确保数据库目录存在"""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> DuckDBPyConnection:
        """获取数据库连接"""
        return duckdb.connect(str(self._db_path))

    @abstractmethod
    def _create_table_sql(self) -> str:
        """
        返回建表SQL

        Returns
        -------
        str
            CREATE TABLE IF NOT EXISTS 语句
        """
        pass

    def _ensure_table(self) -> None:
        """确保表存在"""
        sql = self._create_table_sql()
        with self._get_connection() as conn:
            conn.execute(sql)
            logger.debug(f"表 {self.TABLE_NAME} 已就绪")

    def execute(self, sql: str, params: tuple | None = None) -> None:
        """
        执行SQL（无返回值）

        Parameters
        ----------
        sql : str
            SQL语句
        params : tuple, optional
            参数
        """
        with self._get_connection() as conn:
            if params:
                conn.execute(sql, params)
            else:
                conn.execute(sql)

    def query(self, sql: str, params: tuple | None = None) -> pd.DataFrame:
        """
        查询并返回DataFrame

        Parameters
        ----------
        sql : str
            SQL语句
        params : tuple, optional
            参数

        Returns
        -------
        pd.DataFrame
            查询结果
        """
        with self._get_connection() as conn:
            if params:
                return conn.execute(sql, params).df()
            return conn.execute(sql).df()

    def insert_df(self, df: pd.DataFrame, mode: str = "append") -> int:
        """
        插入DataFrame数据

        Parameters
        ----------
        df : pd.DataFrame
            要插入的数据
        mode : str
            插入模式: append(追加) / replace(替换全表)

        Returns
        -------
        int
            插入的行数
        """
        if df.empty:
            return 0

        with self._get_connection() as conn:
            if mode == "replace":
                conn.execute(f"DELETE FROM {self.TABLE_NAME}")

            conn.register("_tmp_df", df)
            conn.execute(f"INSERT INTO {self.TABLE_NAME} SELECT * FROM _tmp_df")
            conn.unregister("_tmp_df")

        logger.debug(f"插入 {len(df)} 行到 {self.TABLE_NAME}")
        return len(df)

    def count(self) -> int:
        """返回表中记录数"""
        df = self.query(f"SELECT COUNT(*) as cnt FROM {self.TABLE_NAME}")
        return int(df["cnt"].iloc[0])

    def truncate(self) -> None:
        """清空表"""
        self.execute(f"DELETE FROM {self.TABLE_NAME}")
        logger.info(f"已清空表 {self.TABLE_NAME}")
