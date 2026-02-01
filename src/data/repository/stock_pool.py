# -*- coding: utf-8 -*-
"""
股票池仓库

存储和查询股票基本信息。
"""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src.data.repository.base import BaseRepository
from src.data.types import StockInfo


class StockPoolRepository(BaseRepository):
    """
    股票池仓库

    存储股票基本信息，每日更新（ST/停牌状态可能变化）。
    """

    TABLE_NAME = "stock_pool"
    META_TABLE = "sync_meta"

    def __init__(self, db_path: Path) -> None:
        super().__init__(db_path)
        self._ensure_meta_table()

    def _create_table_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS stock_pool (
            symbol VARCHAR PRIMARY KEY,
            code VARCHAR,
            exchange VARCHAR,
            name VARCHAR,
            board VARCHAR,
            is_st BOOLEAN,
            is_suspended BOOLEAN,
            listed_date DATE,
            pre_close DOUBLE,
            upper_limit DOUBLE,
            lower_limit DOUBLE,
            adj_factor DOUBLE,
            updated_at TIMESTAMP
        )
        """

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

    def get_last_sync_time(self) -> datetime | None:
        """获取上次同步时间"""
        df = self.query(
            f"SELECT last_sync_at FROM {self.META_TABLE} WHERE table_name = ?",
            (self.TABLE_NAME,)
        )
        if df.empty or pd.isna(df["last_sync_at"].iloc[0]):
            return None
        return pd.to_datetime(df["last_sync_at"].iloc[0]).to_pydatetime()

    def needs_sync(self, max_age_hours: int = 23) -> bool:
        """判断是否需要同步（默认23小时）"""
        last_sync = self.get_last_sync_time()
        if last_sync is None:
            return True
        age = datetime.now() - last_sync
        return age > timedelta(hours=max_age_hours)

    def _update_sync_meta(self, count: int) -> None:
        """更新同步元信息"""
        sql = """
        INSERT OR REPLACE INTO sync_meta
        (table_name, last_sync_at, record_count)
        VALUES (?, ?, ?)
        """
        self.execute(sql, (self.TABLE_NAME, datetime.now(), count))

    def save(self, stocks: list[StockInfo]) -> int:
        """
        保存股票池（全量替换）

        Parameters
        ----------
        stocks : list[StockInfo]
            股票信息列表

        Returns
        -------
        int
            保存的记录数
        """
        if not stocks:
            return 0

        now = datetime.now()
        records = [
            {
                "symbol": s.symbol,
                "code": s.code,
                "exchange": s.exchange,
                "name": s.name,
                "board": s.board,
                "is_st": s.is_st,
                "is_suspended": s.is_suspended,
                "listed_date": s.listed_date,
                "pre_close": s.pre_close,
                "upper_limit": s.upper_limit,
                "lower_limit": s.lower_limit,
                "adj_factor": s.adj_factor,
                "updated_at": now,
            }
            for s in stocks
        ]
        df = pd.DataFrame(records)
        count = self.insert_df(df, mode="replace")
        self._update_sync_meta(count)
        return count

    def get_all(self) -> list[StockInfo]:
        """获取全部股票"""
        df = self.query(f"SELECT * FROM {self.TABLE_NAME}")
        return self._df_to_stocks(df)

    def get_by_board(self, board: str) -> list[StockInfo]:
        """按板块获取股票"""
        df = self.query(
            f"SELECT * FROM {self.TABLE_NAME} WHERE board = ?",
            (board,)
        )
        return self._df_to_stocks(df)

    def get_tradable(self, exclude_st: bool = True, exclude_suspended: bool = True) -> list[StockInfo]:
        """
        获取可交易股票

        Parameters
        ----------
        exclude_st : bool
            是否排除ST股票
        exclude_suspended : bool
            是否排除停牌股票
        """
        conditions = []
        if exclude_st:
            conditions.append("is_st = false")
        if exclude_suspended:
            conditions.append("is_suspended = false")

        where = " AND ".join(conditions) if conditions else "1=1"
        df = self.query(f"SELECT * FROM {self.TABLE_NAME} WHERE {where}")
        return self._df_to_stocks(df)

    def get_symbols(self, board: str | None = None) -> list[str]:
        """获取股票代码列表"""
        if board:
            df = self.query(
                f"SELECT symbol FROM {self.TABLE_NAME} WHERE board = ?",
                (board,)
            )
        else:
            df = self.query(f"SELECT symbol FROM {self.TABLE_NAME}")
        return df["symbol"].tolist() if not df.empty else []

    def _df_to_stocks(self, df: pd.DataFrame) -> list[StockInfo]:
        """DataFrame 转 StockInfo 列表"""
        if df.empty:
            return []
        result = []
        for _, row in df.iterrows():
            # 处理日期
            listed = row.get("listed_date")
            if pd.isna(listed):
                listed_date = None
            elif hasattr(listed, 'date'):
                listed_date = listed.date()
            else:
                listed_date = listed

            result.append(StockInfo(
                symbol=row["symbol"],
                code=row["code"],
                exchange=row["exchange"],
                name=row["name"],
                board=row["board"],
                is_st=bool(row["is_st"]),
                is_suspended=bool(row["is_suspended"]),
                listed_date=listed_date,
                pre_close=float(row.get("pre_close", 0) or 0),
                upper_limit=float(row.get("upper_limit", 0) or 0),
                lower_limit=float(row.get("lower_limit", 0) or 0),
                adj_factor=float(row.get("adj_factor", 1) or 1),
            ))
        return result
