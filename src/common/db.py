# -*- coding: utf-8 -*-
"""
数据库连接管理模块

提供 DuckDB 数据库连接管理。
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb
from duckdb import DuckDBPyConnection

from src.common.config import AppConfig


class DatabaseManager:
    """
    DuckDB 数据库连接管理器

    管理四个数据库：
    - daily_kline: 日K线数据
    - stock_meta: 股票元信息
    - realtime: 实时数据
    - backtest: 回测数据

    Examples
    --------
    >>> db_mgr = DatabaseManager(config)
    >>> with db_mgr.get_connection("daily_kline") as conn:
    ...     df = conn.execute("SELECT * FROM daily_kline LIMIT 10").df()
    """

    # 有效的数据库名称
    VALID_DB_NAMES = ("daily_kline", "stock_meta", "realtime", "backtest")

    def __init__(self, config: AppConfig) -> None:
        """
        初始化

        Parameters
        ----------
        config : AppConfig
            应用配置对象
        """
        self.config = config
        self._ensure_data_dirs()

    def _ensure_data_dirs(self) -> None:
        """确保数据目录存在"""
        for db_name in self.VALID_DB_NAMES:
            db_path = getattr(self.config.database, db_name)
            db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self, db_name: str) -> Iterator[DuckDBPyConnection]:
        """
        获取数据库连接（上下文管理器）

        Parameters
        ----------
        db_name : str
            数据库名称: daily_kline / stock_meta / realtime / backtest

        Yields
        ------
        DuckDBPyConnection
            DuckDB 连接对象
        """
        if db_name not in self.VALID_DB_NAMES:
            raise ValueError(f"无效的数据库名称: {db_name}，有效值: {self.VALID_DB_NAMES}")

        db_path = getattr(self.config.database, db_name)
        conn = duckdb.connect(str(db_path))
        try:
            yield conn
        finally:
            conn.close()
