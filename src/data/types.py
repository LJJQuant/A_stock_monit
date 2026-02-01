# -*- coding: utf-8 -*-
"""
数据层类型定义

定义数据层核心数据结构。
"""

from dataclasses import dataclass
from datetime import date
from typing import TypeAlias

import pandas as pd


# ============================================================
# 类型别名
# ============================================================

Symbol: TypeAlias = str  # 掘金格式股票代码，如 "SHSE.600000"
StockCode: TypeAlias = str  # 纯数字代码，如 "600000"
ExchangeCode: TypeAlias = str  # 交易所代码，如 "SHSE" / "SZSE"


# ============================================================
# 股票信息
# ============================================================

@dataclass(frozen=True, slots=True)
class StockInfo:
    """
    股票基本信息（来自 get_symbols）

    Attributes
    ----------
    symbol : str
        掘金格式代码，如 SHSE.600000
    code : str
        纯数字代码，如 600000
    exchange : str
        交易所代码: SHSE(上海) / SZSE(深圳)
    name : str
        股票名称
    board : str
        板块: main(主板) / gem(创业板) / star(科创板) / bse(北交所)
    is_st : bool
        是否ST股票
    is_suspended : bool
        是否停牌
    listed_date : date | None
        上市日期
    pre_close : float
        昨收价
    upper_limit : float
        涨停价
    lower_limit : float
        跌停价
    adj_factor : float
        复权因子
    """
    symbol: str
    code: str
    exchange: str
    name: str
    board: str
    is_st: bool
    is_suspended: bool
    listed_date: date | None
    pre_close: float
    upper_limit: float
    lower_limit: float
    adj_factor: float


# ============================================================
# 交易日信息
# ============================================================

@dataclass(frozen=True, slots=True)
class TradingDay:
    """
    交易日信息

    Attributes
    ----------
    exchange : str
        交易所代码: SHSE / SZSE
    date : date
        日期
    is_trading_day : bool
        是否交易日
    prev_trading_day : date | None
        前一交易日（非交易日为None）
    next_trading_day : date | None
        下一交易日（非交易日为None）
    """
    exchange: str
    date: date
    is_trading_day: bool
    prev_trading_day: date | None
    next_trading_day: date | None


# ============================================================
# K线数据
# ============================================================

@dataclass(frozen=True, slots=True)
class KlineBar:
    """
    单根K线数据

    Attributes
    ----------
    symbol : str
        股票代码
    date : date
        日期
    open : float
        开盘价（后复权）
    high : float
        最高价（后复权）
    low : float
        最低价（后复权）
    close : float
        收盘价（后复权）
    volume : int
        成交量（股）
    amount : float
        成交额（元）
    adj_factor : float
        复权因子
    """
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    adj_factor: float


# ============================================================
# DataFrame 列名常量（用于统一列命名）
# ============================================================

class KlineColumns:
    """K线DataFrame列名"""
    SYMBOL = "symbol"
    DATE = "date"
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"
    AMOUNT = "amount"
    ADJ_FACTOR = "adj_factor"

    # 所有列名列表
    ALL = [SYMBOL, DATE, OPEN, HIGH, LOW, CLOSE, VOLUME, AMOUNT, ADJ_FACTOR]
    # 价格列
    PRICE_COLUMNS = [OPEN, HIGH, LOW, CLOSE]


class StockPoolColumns:
    """股票池DataFrame列名"""
    SYMBOL = "symbol"
    CODE = "code"
    EXCHANGE = "exchange"
    NAME = "name"
    BOARD = "board"
    IS_ST = "is_st"
    IS_SUSPENDED = "is_suspended"
    UPDATED_AT = "updated_at"

    ALL = [SYMBOL, CODE, EXCHANGE, NAME, BOARD, IS_ST, IS_SUSPENDED, UPDATED_AT]


class TradingCalendarColumns:
    """交易日历DataFrame列名"""
    EXCHANGE = "exchange"
    DATE = "date"
    IS_TRADING_DAY = "is_trading_day"
    PREV_TRADING_DAY = "prev_trading_day"
    NEXT_TRADING_DAY = "next_trading_day"

    ALL = [EXCHANGE, DATE, IS_TRADING_DAY, PREV_TRADING_DAY, NEXT_TRADING_DAY]
