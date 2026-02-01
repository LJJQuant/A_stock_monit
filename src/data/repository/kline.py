# -*- coding: utf-8 -*-
"""
K线数据仓库

存储日线K线数据，支持断点续传初始化。
"""

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.data.repository.base import BaseRepository


class KlineRepository(BaseRepository):
    """
    K线数据仓库

    包含两个表：
    - daily_kline: K线数据
    - kline_sync_status: 每只股票的同步状态（用于断点续传）
    """

    TABLE_NAME = "daily_kline"
    STATUS_TABLE = "kline_sync_status"
    META_TABLE = "sync_meta"

    def __init__(self, db_path: Path) -> None:
        super().__init__(db_path)
        self._ensure_status_table()
        self._ensure_meta_table()

    def _create_table_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS daily_kline (
            symbol VARCHAR,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            amount DOUBLE,
            pre_close DOUBLE,
            PRIMARY KEY (symbol, date)
        );
        CREATE INDEX IF NOT EXISTS idx_kline_date ON daily_kline(date);
        """

    def _ensure_status_table(self) -> None:
        """确保同步状态表存在"""
        sql = """
        CREATE TABLE IF NOT EXISTS kline_sync_status (
            symbol VARCHAR PRIMARY KEY,
            status VARCHAR,
            last_date DATE,
            updated_at TIMESTAMP
        )
        """
        self.execute(sql)

    def _ensure_meta_table(self) -> None:
        """确保元数据表存在"""
        sql = """
        CREATE TABLE IF NOT EXISTS sync_meta (
            table_name VARCHAR PRIMARY KEY,
            last_sync_at TIMESTAMP,
            sync_start_date DATE,
            sync_end_date DATE,
            record_count INTEGER,
            extra_info VARCHAR
        )
        """
        self.execute(sql)

    # ========== 初始化状态管理 ==========

    def is_init_completed(self) -> bool:
        """检查初始化是否完成"""
        df = self.query(
            f"SELECT extra_info FROM {self.META_TABLE} WHERE table_name = ?",
            (self.TABLE_NAME,)
        )
        if df.empty:
            return False
        return df["extra_info"].iloc[0] == "init_completed"

    def set_init_status(self, status: str) -> None:
        """设置初始化状态: init_in_progress / init_completed"""
        sql = """
        INSERT OR REPLACE INTO sync_meta
        (table_name, last_sync_at, extra_info)
        VALUES (?, ?, ?)
        """
        self.execute(sql, (self.TABLE_NAME, datetime.now(), status))

    def get_last_sync_date(self) -> date | None:
        """获取最后同步日期（增量更新用）"""
        df = self.query(
            f"SELECT sync_end_date FROM {self.META_TABLE} WHERE table_name = ?",
            (self.TABLE_NAME,)
        )
        if df.empty or pd.isna(df["sync_end_date"].iloc[0]):
            return None
        val = df["sync_end_date"].iloc[0]
        if hasattr(val, 'date'):
            return val.date()
        return val

    def update_sync_date(self, end_date: date) -> None:
        """更新同步日期"""
        sql = """
        UPDATE sync_meta
        SET sync_end_date = ?, last_sync_at = ?
        WHERE table_name = ?
        """
        self.execute(sql, (end_date, datetime.now(), self.TABLE_NAME))

    # ========== 股票同步状态（断点续传） ==========

    def get_completed_symbols(self) -> set[str]:
        """获取已完成同步的股票代码"""
        df = self.query(
            f"SELECT symbol FROM {self.STATUS_TABLE} WHERE status = 'completed'"
        )
        return set(df["symbol"].tolist()) if not df.empty else set()

    def mark_symbol_completed(self, symbol: str, last_date: date) -> None:
        """标记股票同步完成"""
        sql = """
        INSERT OR REPLACE INTO kline_sync_status
        (symbol, status, last_date, updated_at)
        VALUES (?, 'completed', ?, ?)
        """
        self.execute(sql, (symbol, last_date, datetime.now()))

    def get_symbol_count(self) -> int:
        """获取已同步股票数量"""
        df = self.query(
            f"SELECT COUNT(*) as cnt FROM {self.STATUS_TABLE} WHERE status = 'completed'"
        )
        return int(df["cnt"].iloc[0]) if not df.empty else 0

    def clear_sync_status(self) -> None:
        """清空同步状态（重新初始化用）"""
        self.execute(f"DELETE FROM {self.STATUS_TABLE}")

    # ========== K线数据操作 ==========

    def save_kline(self, df: pd.DataFrame) -> int:
        """
        保存K线数据

        Parameters
        ----------
        df : pd.DataFrame
            包含列: symbol, date, open, high, low, close, volume, amount, pre_close

        Returns
        -------
        int
            保存的记录数
        """
        if df.empty:
            return 0

        # 确保列顺序
        cols = ["symbol", "date", "open", "high", "low", "close", "volume", "amount", "pre_close"]
        df = df[[c for c in cols if c in df.columns]]

        return self.insert_df(df, mode="replace")

    def get_kline(
        self,
        symbols: list[str] | str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        获取K线数据

        Parameters
        ----------
        symbols : list[str] | str
            股票代码或代码列表
        start_date : date
            开始日期
        end_date : date
            结束日期

        Returns
        -------
        pd.DataFrame
            K线数据
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        placeholders = ",".join(["?"] * len(symbols))
        sql = f"""
        SELECT * FROM {self.TABLE_NAME}
        WHERE symbol IN ({placeholders})
          AND date >= ?
          AND date <= ?
        ORDER BY symbol, date
        """
        params = tuple(symbols) + (start_date, end_date)
        return self.query(sql, params)

    def get_latest_date(self, symbol: str) -> date | None:
        """获取某只股票最新K线日期"""
        df = self.query(
            f"SELECT MAX(date) as max_date FROM {self.TABLE_NAME} WHERE symbol = ?",
            (symbol,)
        )
        if df.empty or pd.isna(df["max_date"].iloc[0]):
            return None
        val = df["max_date"].iloc[0]
        if hasattr(val, 'date'):
            return val.date()
        return val

    def count(self) -> int:
        """获取K线记录总数"""
        df = self.query(f"SELECT COUNT(*) as cnt FROM {self.TABLE_NAME}")
        return int(df["cnt"].iloc[0]) if not df.empty else 0

    def count_symbols(self) -> int:
        """获取有K线数据的股票数量"""
        df = self.query(f"SELECT COUNT(DISTINCT symbol) as cnt FROM {self.TABLE_NAME}")
        return int(df["cnt"].iloc[0]) if not df.empty else 0
