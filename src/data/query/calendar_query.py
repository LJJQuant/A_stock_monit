# -*- coding: utf-8 -*-
"""
交易日历查询

使用示例：
    from src.data.query import CalendarQuery

    q = CalendarQuery()
    days = q.get_trading_days("SHSE", "2024-01-01", "2024-06-30")
    is_td = q.is_trading_day("SHSE", "2024-01-15")
"""

import pandas as pd

from src.common.config import load_config
from src.data.repository.trading_calendar import TradingCalendarRepository


class CalendarQuery:
    """交易日历查询"""

    def __init__(self, repo: TradingCalendarRepository | None = None) -> None:
        if repo is None:
            config = load_config()
            repo = TradingCalendarRepository(config.database.stock_meta)
        self._repo = repo

    def get_trading_days(self, exchange: str, start: str, end: str) -> list[str]:
        """
        获取指定范围内的交易日

        Parameters
        ----------
        exchange : str
            交易所代码，如 "SHSE"
        start : str
            开始日期，如 "2024-01-01"
        end : str
            结束日期，如 "2024-06-30"

        Returns
        -------
        list[str]
            交易日列表，格式 "YYYY-MM-DD"
        """
        df = self._repo.query(
            "SELECT date FROM trading_calendar "
            "WHERE exchange = ? AND date >= ? AND date <= ? AND is_trading_day = true "
            "ORDER BY date",
            (exchange, start, end)
        )
        if df.empty:
            return []
        return [self._date_to_str(d) for d in df["date"].tolist()]

    def get_prev_trading_day(self, exchange: str, date: str) -> str | None:
        """
        获取指定日期的前一交易日

        Parameters
        ----------
        exchange : str
            交易所代码
        date : str
            日期

        Returns
        -------
        str | None
            前一交易日，无则返回 None
        """
        df = self._repo.query(
            "SELECT date FROM trading_calendar "
            "WHERE exchange = ? AND date < ? AND is_trading_day = true "
            "ORDER BY date DESC LIMIT 1",
            (exchange, date)
        )
        if df.empty:
            return None
        return self._date_to_str(df["date"].iloc[0])

    def get_next_trading_day(self, exchange: str, date: str) -> str | None:
        """
        获取指定日期的下一交易日

        Parameters
        ----------
        exchange : str
            交易所代码
        date : str
            日期

        Returns
        -------
        str | None
            下一交易日，无则返回 None
        """
        df = self._repo.query(
            "SELECT date FROM trading_calendar "
            "WHERE exchange = ? AND date > ? AND is_trading_day = true "
            "ORDER BY date ASC LIMIT 1",
            (exchange, date)
        )
        if df.empty:
            return None
        return self._date_to_str(df["date"].iloc[0])

    def is_trading_day(self, exchange: str, date: str) -> bool:
        """
        判断是否为交易日

        Parameters
        ----------
        exchange : str
            交易所代码
        date : str
            日期

        Returns
        -------
        bool
            是否为交易日
        """
        df = self._repo.query(
            "SELECT is_trading_day FROM trading_calendar "
            "WHERE exchange = ? AND date = ?",
            (exchange, date)
        )
        if df.empty:
            return False
        return bool(df["is_trading_day"].iloc[0])

    def get_all_trading_days(self, exchange: str) -> list[str]:
        """
        获取数据库中全部交易日

        Parameters
        ----------
        exchange : str
            交易所代码

        Returns
        -------
        list[str]
            全部交易日列表
        """
        df = self._repo.query(
            "SELECT date FROM trading_calendar "
            "WHERE exchange = ? AND is_trading_day = true "
            "ORDER BY date",
            (exchange,)
        )
        if df.empty:
            return []
        return [self._date_to_str(d) for d in df["date"].tolist()]

    def get_date_range(self, exchange: str) -> tuple[str | None, str | None]:
        """
        获取数据库中日历的日期范围

        Returns
        -------
        tuple[str | None, str | None]
            (最早日期, 最晚日期)，无数据返回 (None, None)
        """
        df = self._repo.query(
            "SELECT MIN(date) as min_date, MAX(date) as max_date "
            "FROM trading_calendar WHERE exchange = ?",
            (exchange,)
        )
        if df.empty or pd.isna(df["min_date"].iloc[0]):
            return None, None
        return self._date_to_str(df["min_date"].iloc[0]), self._date_to_str(df["max_date"].iloc[0])

    def _date_to_str(self, d) -> str:
        """日期转字符串"""
        if hasattr(d, 'strftime'):
            return d.strftime("%Y-%m-%d")
        return str(d)[:10]
