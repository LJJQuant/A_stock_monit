# -*- coding: utf-8 -*-
"""
股票池查询

使用示例：
    from src.data.query import StockQuery

    q = StockQuery()
    stocks = q.get_all()
    symbols = q.get_symbols("main")
"""

import pandas as pd

from src.common.config import load_config
from src.data.repository.stock_pool import StockPoolRepository
from src.data.types import StockInfo


class StockQuery:
    """股票池查询"""

    def __init__(self, repo: StockPoolRepository | None = None) -> None:
        if repo is None:
            config = load_config()
            repo = StockPoolRepository(config.database.stock_meta)
        self._repo = repo

    def get_all(self) -> list[StockInfo]:
        """获取全部股票"""
        df = self._repo.query("SELECT * FROM stock_pool")
        return self._df_to_stocks(df)

    def get_by_board(self, board: str) -> list[StockInfo]:
        """
        按板块获取股票

        Parameters
        ----------
        board : str
            板块: main(主板) / gem(创业板) / star(科创板) / bse(北交所)
        """
        df = self._repo.query(
            "SELECT * FROM stock_pool WHERE board = ?",
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
        df = self._repo.query(f"SELECT * FROM stock_pool WHERE {where}")
        return self._df_to_stocks(df)

    def get_symbols(self, board: str | None = None) -> list[str]:
        """
        获取股票代码列表

        Parameters
        ----------
        board : str | None
            板块，None 表示全部
        """
        if board:
            df = self._repo.query(
                "SELECT symbol FROM stock_pool WHERE board = ?",
                (board,)
            )
        else:
            df = self._repo.query("SELECT symbol FROM stock_pool")
        return df["symbol"].tolist() if not df.empty else []

    def get_stock(self, symbol: str) -> StockInfo | None:
        """
        获取单只股票信息

        Parameters
        ----------
        symbol : str
            股票代码，如 "SHSE.600000"
        """
        df = self._repo.query(
            "SELECT * FROM stock_pool WHERE symbol = ?",
            (symbol,)
        )
        stocks = self._df_to_stocks(df)
        return stocks[0] if stocks else None

    def _df_to_stocks(self, df: pd.DataFrame) -> list[StockInfo]:
        """DataFrame 转 StockInfo 列表"""
        if df.empty:
            return []
        result = []
        for _, row in df.iterrows():
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
