# -*- coding: utf-8 -*-
"""
常量定义模块

定义系统核心常量，按需扩展。
"""

from enum import Enum
from typing import Final


# ============================================================
# 交易所代码
# ============================================================

class Exchange(str, Enum):
    """交易所"""
    SH = "SH"  # 上海
    SZ = "SZ"  # 深圳


# ============================================================
# 市场类型
# ============================================================

class Market(str, Enum):
    """市场类型"""
    MAIN = "main"  # 主板
    GEM = "gem"    # 创业板


# 涨跌停幅度（小数）
LIMIT_PCT: Final[dict[Market, float]] = {
    Market.MAIN: 0.10,  # 主板 10%
    Market.GEM: 0.20,   # 创业板 20%
}


# ============================================================
# 数据库表名
# ============================================================

class TableName(str, Enum):
    """DuckDB 表名"""
    # 日K线数据库 (daily_kline.duckdb)
    DAILY_KLINE = "daily_kline"

    # 股票元信息数据库 (stock_meta.duckdb)
    STOCK_POOL = "stock_pool"
    TRADING_CALENDAR = "trading_calendar"

    # 实时数据库 (realtime.duckdb)
    CHIP_CONCENTRATION = "chip_concentration"
    CAPITAL_FLOW = "capital_flow"
    ALERT_RECORD = "alert_record"

    # 回测数据库 (backtest.duckdb)
    KLINE_30MIN = "kline_30min"


# ============================================================
# 掘金量化交易所前缀
# ============================================================

JUEJIN_EXCHANGE_PREFIX: Final[dict[Exchange, str]] = {
    Exchange.SH: "SHSE",  # 上海
    Exchange.SZ: "SZSE",  # 深圳
}
