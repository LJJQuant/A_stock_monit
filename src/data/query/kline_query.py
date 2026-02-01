# -*- coding: utf-8 -*-
"""
K线数据查询

使用示例：
    from src.data.query import KlineQuery

    q = KlineQuery()
    df = q.get_kline("SHSE.600000", "2024-01-01", "2024-06-30")
    df = q.get_kline_by_date("2024-01-15")
"""

import pandas as pd

from src.common.config import load_config
from src.data.repository.kline import KlineRepository


class KlineQuery:
    """K线数据查询"""

    def __init__(self, kline_repo: KlineRepository | None = None) -> None:
        if kline_repo is None:
            config = load_config()
            kline_repo = KlineRepository(config.database.daily_kline)
        self._repo = kline_repo

    def get_kline(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """
        获取单只股票区间K线

        Parameters
        ----------
        symbol : str
            股票代码，如 "SHSE.600000"
        start : str
            开始日期，如 "2024-01-01"
        end : str
            结束日期，如 "2024-06-30"

        Returns
        -------
        pd.DataFrame
            K线数据，按日期升序
        """
        sql = """
        SELECT * FROM daily_kline
        WHERE symbol = ?
          AND date >= ?
          AND date <= ?
        ORDER BY date
        """
        return self._repo.query(sql, (symbol, start, end))

    def get_kline_multi(self, symbols: list[str], start: str, end: str) -> pd.DataFrame:
        """
        获取多只股票区间K线

        Parameters
        ----------
        symbols : list[str]
            股票代码列表
        start : str
            开始日期
        end : str
            结束日期

        Returns
        -------
        pd.DataFrame
            K线数据，按股票、日期升序
        """
        if not symbols:
            return pd.DataFrame()

        placeholders = ",".join(["?"] * len(symbols))
        sql = f"""
        SELECT * FROM daily_kline
        WHERE symbol IN ({placeholders})
          AND date >= ?
          AND date <= ?
        ORDER BY symbol, date
        """
        params = tuple(symbols) + (start, end)
        return self._repo.query(sql, params)

    def get_kline_by_date(self, date: str) -> pd.DataFrame:
        """
        获取某一天所有股票K线

        Parameters
        ----------
        date : str
            日期，如 "2024-01-15"

        Returns
        -------
        pd.DataFrame
            当天所有股票K线，按股票代码排序
        """
        sql = """
        SELECT * FROM daily_kline
        WHERE date = ?
        ORDER BY symbol
        """
        return self._repo.query(sql, (date,))
