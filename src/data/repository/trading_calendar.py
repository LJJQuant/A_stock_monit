# -*- coding: utf-8 -*-
"""
交易日历仓库

存储和查询交易日历数据。
"""

from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from src.data.repository.base import BaseRepository
from src.data.types import TradingDay, TradingCalendarColumns


class TradingCalendarRepository(BaseRepository):
    """
    交易日历仓库

    表结构：
    - exchange: 交易所代码 (SHSE/SZSE)
    - date: 日期
    - is_trading_day: 是否交易日
    - prev_trading_day: 前一交易日
    - next_trading_day: 下一交易日

    Parameters
    ----------
    db_path : Path
        stock_meta.duckdb 路径
    """

    TABLE_NAME = "trading_calendar"
    META_TABLE = "sync_meta"

    def __init__(self, db_path: Path) -> None:
        super().__init__(db_path)
        self._ensure_meta_table()

    def _create_table_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS trading_calendar (
            exchange VARCHAR NOT NULL,
            date DATE NOT NULL,
            is_trading_day BOOLEAN NOT NULL,
            prev_trading_day DATE,
            next_trading_day DATE,
            PRIMARY KEY (exchange, date)
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
        """
        获取上次同步时间

        Returns
        -------
        datetime | None
            上次同步时间，从未同步返回 None
        """
        df = self.query(
            f"SELECT last_sync_at FROM {self.META_TABLE} WHERE table_name = ?",
            (self.TABLE_NAME,)
        )
        if df.empty or pd.isna(df["last_sync_at"].iloc[0]):
            return None
        return pd.to_datetime(df["last_sync_at"].iloc[0]).to_pydatetime()

    def needs_sync(self, max_age_days: int = 30) -> bool:
        """
        判断是否需要同步

        Parameters
        ----------
        max_age_days : int
            最大允许的过期天数，默认30天

        Returns
        -------
        bool
            True 表示需要同步
        """
        last_sync = self.get_last_sync_time()
        if last_sync is None:
            return True
        age = datetime.now() - last_sync
        return age > timedelta(days=max_age_days)

    def _update_sync_meta(self, start_date: date, end_date: date, count: int) -> None:
        """更新同步元信息"""
        sql = """
        INSERT OR REPLACE INTO sync_meta
        (table_name, last_sync_at, sync_start_date, sync_end_date, record_count)
        VALUES (?, ?, ?, ?, ?)
        """
        self.execute(sql, (
            self.TABLE_NAME,
            datetime.now(),
            start_date,
            end_date,
            count,
        ))

    def save(self, trading_days: list[TradingDay]) -> int:
        """
        保存交易日历

        Parameters
        ----------
        trading_days : list[TradingDay]
            交易日列表

        Returns
        -------
        int
            保存的记录数
        """
        if not trading_days:
            return 0

        # 转换为 DataFrame
        records = [
            {
                TradingCalendarColumns.EXCHANGE: td.exchange,
                TradingCalendarColumns.DATE: td.date,
                TradingCalendarColumns.IS_TRADING_DAY: td.is_trading_day,
                TradingCalendarColumns.PREV_TRADING_DAY: td.prev_trading_day,
                TradingCalendarColumns.NEXT_TRADING_DAY: td.next_trading_day,
            }
            for td in trading_days
        ]
        df = pd.DataFrame(records)

        # 按 exchange + date 去重（保留最新）
        with self._get_connection() as conn:
            # 删除已存在的日期范围数据
            exchange = trading_days[0].exchange
            min_date = min(td.date for td in trading_days)
            max_date = max(td.date for td in trading_days)

            conn.execute(
                f"DELETE FROM {self.TABLE_NAME} "
                f"WHERE exchange = ? AND date >= ? AND date <= ?",
                (exchange, min_date, max_date)
            )

            # 插入新数据
            conn.register("_tmp_df", df)
            conn.execute(f"INSERT INTO {self.TABLE_NAME} SELECT * FROM _tmp_df")
            conn.unregister("_tmp_df")

        # 更新元信息
        self._update_sync_meta(min_date, max_date, len(df))

        return len(df)

    def get_trading_days(
        self,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> list[date]:
        """
        获取指定范围内的交易日

        Parameters
        ----------
        exchange : str
            交易所代码
        start_date : date
            开始日期
        end_date : date
            结束日期

        Returns
        -------
        list[date]
            交易日列表（已排序）
        """
        df = self.query(
            f"SELECT date FROM {self.TABLE_NAME} "
            f"WHERE exchange = ? AND date >= ? AND date <= ? AND is_trading_day = true "
            f"ORDER BY date",
            (exchange, start_date, end_date)
        )
        if df.empty:
            return []
        return [d.date() if hasattr(d, 'date') else d for d in df["date"].tolist()]

    def get_prev_trading_day(self, exchange: str, dt: date) -> date | None:
        """获取指定日期的前一交易日"""
        df = self.query(
            f"SELECT date FROM {self.TABLE_NAME} "
            f"WHERE exchange = ? AND date < ? AND is_trading_day = true "
            f"ORDER BY date DESC LIMIT 1",
            (exchange, dt)
        )
        if df.empty:
            return None
        d = df["date"].iloc[0]
        return d.date() if hasattr(d, 'date') else d

    def get_next_trading_day(self, exchange: str, dt: date) -> date | None:
        """获取指定日期的下一交易日"""
        df = self.query(
            f"SELECT date FROM {self.TABLE_NAME} "
            f"WHERE exchange = ? AND date > ? AND is_trading_day = true "
            f"ORDER BY date ASC LIMIT 1",
            (exchange, dt)
        )
        if df.empty:
            return None
        d = df["date"].iloc[0]
        return d.date() if hasattr(d, 'date') else d

    def is_trading_day(self, exchange: str, dt: date) -> bool:
        """判断是否为交易日"""
        df = self.query(
            f"SELECT is_trading_day FROM {self.TABLE_NAME} "
            f"WHERE exchange = ? AND date = ?",
            (exchange, dt)
        )
        if df.empty:
            return False
        return bool(df["is_trading_day"].iloc[0])

    def get_all_trading_days(self, exchange: str) -> list[date]:
        """
        获取数据库中全部交易日

        Parameters
        ----------
        exchange : str
            交易所代码

        Returns
        -------
        list[date]
            全部交易日列表（已排序）
        """
        df = self.query(
            f"SELECT date FROM {self.TABLE_NAME} "
            f"WHERE exchange = ? AND is_trading_day = true "
            f"ORDER BY date",
            (exchange,)
        )
        if df.empty:
            return []
        return [d.date() if hasattr(d, 'date') else d for d in df["date"].tolist()]

    def get_date_range(self, exchange: str) -> tuple[date | None, date | None]:
        """
        获取数据库中日历的日期范围

        Returns
        -------
        tuple[date | None, date | None]
            (最早日期, 最晚日期)，无数据返回 (None, None)
        """
        df = self.query(
            f"SELECT MIN(date) as min_date, MAX(date) as max_date "
            f"FROM {self.TABLE_NAME} WHERE exchange = ?",
            (exchange,)
        )
        if df.empty or pd.isna(df["min_date"].iloc[0]):
            return None, None

        min_d = df["min_date"].iloc[0]
        max_d = df["max_date"].iloc[0]
        min_date = min_d.date() if hasattr(min_d, 'date') else min_d
        max_date = max_d.date() if hasattr(max_d, 'date') else max_d
        return min_date, max_date
