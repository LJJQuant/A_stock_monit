# -*- coding: utf-8 -*-
"""
掘金量化SDK封装

提供股票池、交易日历、K线数据获取功能。
包含懒加载认证、指数退避重试、分批请求等特性。
"""

import logging
import time
from datetime import date, datetime
from typing import Iterator

import pandas as pd
from gm.api import (
    set_token,
    get_symbols,
    get_trading_dates,
    history,
)

from src.data.types import StockInfo, TradingDay
from src.data.source.exceptions import (
    JuejinAuthError,
    JuejinAPIError,
    JuejinRateLimitError,
)

logger = logging.getLogger(__name__)


# ============================================================
# 常量
# ============================================================

# 掘金 board 字段值 -> 内部 board 名称
_BOARD_CODE_TO_NAME: dict[int, str] = {
    10100101: "main",   # 主板
    10100102: "gem",    # 创业板
    10100103: "star",   # 科创板
    10100104: "bse",    # 北交所
}

# 内部 board 名称 -> 掘金 board 字段值
_BOARD_NAME_TO_CODE: dict[str, int] = {
    "main": 10100101,
    "gem": 10100102,
    "star": 10100103,
    "bse": 10100104,
}

# 默认重试配置
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BASE_DELAY = 1.0  # 秒
_DEFAULT_BATCH_SIZE = 200  # 每批股票数量


class JuejinClient:
    """
    掘金量化SDK客户端封装

    特性：
    - 懒加载认证：首次API调用时自动设置Token
    - 指数退避重试：网络异常自动重试
    - 分批请求：大量股票自动分批处理

    Parameters
    ----------
    token : str
        掘金量化API Token
    max_retries : int
        最大重试次数，默认3次
    batch_size : int
        分批请求时每批股票数量，默认200

    Examples
    --------
    >>> client = JuejinClient(token="your_token")
    >>> stocks = client.get_stock_pool(["main"])
    >>> klines = client.get_kline(["SHSE.600000"], date(2024,1,1), date(2024,1,31))
    """

    def __init__(
        self,
        token: str,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        self._token = token
        self._max_retries = max_retries
        self._batch_size = batch_size
        self._authenticated = False

    def _ensure_auth(self) -> None:
        """确保已认证（懒加载）"""
        if self._authenticated:
            return

        if not self._token:
            raise JuejinAuthError("Token不能为空")

        try:
            set_token(self._token)
            self._authenticated = True
            logger.info("掘金量化认证成功")
        except Exception as e:
            raise JuejinAuthError(f"Token设置失败: {e}") from e

    def _retry_call(self, func: callable, *args, **kwargs):
        """
        带指数退避的重试调用

        Parameters
        ----------
        func : callable
            要调用的函数
        *args, **kwargs
            函数参数

        Returns
        -------
        Any
            函数返回值

        Raises
        ------
        JuejinAPIError
            重试耗尽后仍然失败
        """
        last_error = None

        for attempt in range(self._max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # 检查是否为频率限制
                if "rate" in error_msg or "limit" in error_msg:
                    raise JuejinRateLimitError() from e

                # 检查是否为认证错误（不重试）
                if "token" in error_msg or "auth" in error_msg:
                    raise JuejinAuthError(str(e)) from e

                # 计算退避时间：1s, 2s, 4s...
                delay = _DEFAULT_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"API调用失败 (尝试 {attempt + 1}/{self._max_retries}): {e}, "
                    f"{delay:.1f}秒后重试"
                )
                time.sleep(delay)

        raise JuejinAPIError(f"重试{self._max_retries}次后仍然失败: {last_error}")

    def get_stock_pool(self, boards: list[str] | None = None) -> list[StockInfo]:
        """
        获取股票池

        Parameters
        ----------
        boards : list[str] | None
            板块列表: main(主板) / gem(创业板) / star(科创板) / bse(北交所)
            None 表示获取全部A股

        Returns
        -------
        list[StockInfo]
            股票信息列表
        """
        self._ensure_auth()

        # 获取全部A股（sec_type1=1010, sec_type2=101001）
        # skip_suspended=False, skip_st=False 以获取完整信息
        infos = self._retry_call(
            get_symbols,
            sec_type1=1010,
            sec_type2=101001,
            skip_suspended=False,
            skip_st=False,
        )

        if not infos:
            return []

        result: list[StockInfo] = []

        for info in infos:
            board_code = info.get("board", 0)
            board_name = _BOARD_CODE_TO_NAME.get(board_code, "unknown")

            # 按板块过滤
            if boards and board_name not in boards:
                continue

            # 处理上市日期
            listed = info.get("listed_date")
            listed_date = None
            if listed:
                if hasattr(listed, 'date'):
                    listed_date = listed.date()
                elif isinstance(listed, str):
                    listed_date = datetime.strptime(listed[:10], "%Y-%m-%d").date()

            stock = StockInfo(
                symbol=info.get("symbol", ""),
                code=info.get("sec_id", ""),
                exchange=info.get("exchange", ""),
                name=info.get("sec_name", ""),
                board=board_name,
                is_st=bool(info.get("is_st", False)),
                is_suspended=bool(info.get("is_suspended", False)),
                listed_date=listed_date,
                pre_close=float(info.get("pre_close", 0) or 0),
                upper_limit=float(info.get("upper_limit", 0) or 0),
                lower_limit=float(info.get("lower_limit", 0) or 0),
                adj_factor=float(info.get("adj_factor", 1) or 1),
            )
            result.append(stock)

        logger.info(f"获取股票池完成，共 {len(result)} 只股票")
        return result

    def get_trading_calendar(
        self,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> list[TradingDay]:
        """
        获取交易日历

        Parameters
        ----------
        exchange : str
            交易所代码: SHSE / SZSE
        start_date : date
            开始日期
        end_date : date
            结束日期

        Returns
        -------
        list[TradingDay]
            交易日信息列表
        """
        self._ensure_auth()

        # 获取交易日列表
        trading_dates = self._retry_call(
            get_trading_dates,
            exchange=exchange,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        if not trading_dates:
            return []

        # 转换为 date 对象的 set
        trading_set: set[date] = set()
        for d in trading_dates:
            if isinstance(d, datetime):
                trading_set.add(d.date())
            elif isinstance(d, date):
                trading_set.add(d)
            elif isinstance(d, str):
                # 字符串格式: "2024-01-02" 或 "2024-01-02 00:00:00"
                trading_set.add(datetime.strptime(d[:10], "%Y-%m-%d").date())

        trading_list = sorted(trading_set)

        # 构建结果，计算前后交易日
        result: list[TradingDay] = []
        current = start_date

        while current <= end_date:
            is_trading = current in trading_set

            # 查找前一交易日
            prev_td = None
            if is_trading:
                idx = trading_list.index(current)
                if idx > 0:
                    prev_td = trading_list[idx - 1]

            # 查找下一交易日
            next_td = None
            if is_trading:
                idx = trading_list.index(current)
                if idx < len(trading_list) - 1:
                    next_td = trading_list[idx + 1]

            result.append(TradingDay(
                exchange=exchange,
                date=current,
                is_trading_day=is_trading,
                prev_trading_day=prev_td,
                next_trading_day=next_td,
            ))

            # 下一天
            current = date.fromordinal(current.toordinal() + 1)

        logger.info(
            f"获取交易日历完成: {exchange} {start_date} ~ {end_date}, "
            f"共 {len(trading_list)} 个交易日"
        )
        return result

    def get_kline(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date,
        adjust: str = "post",
    ) -> Iterator[pd.DataFrame]:
        """
        获取K线数据（分批迭代器）

        Parameters
        ----------
        symbols : list[str]
            股票代码列表，掘金格式如 ["SHSE.600000", "SZSE.000001"]
        start_date : date
            开始日期
        end_date : date
            结束日期
        adjust : str
            复权方式: post(后复权) / pre(前复权) / none(不复权)

        Yields
        ------
        pd.DataFrame
            每批股票的K线数据，包含列:
            symbol, date, open, high, low, close, volume, amount, adj_factor

        Notes
        -----
        为避免单次请求超时，自动分批请求，每批最多 batch_size 只股票。
        """
        self._ensure_auth()

        # 复权参数映射
        adjust_map = {"post": 2, "pre": 1, "none": 0}
        adj_mode = adjust_map.get(adjust, 2)

        # 日期格式
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # 分批请求
        for i in range(0, len(symbols), self._batch_size):
            batch = symbols[i : i + self._batch_size]
            batch_str = ",".join(batch)

            logger.debug(f"请求K线: 批次 {i // self._batch_size + 1}, {len(batch)} 只股票")

            result = self._retry_call(
                history,
                symbol=batch_str,
                frequency="1d",
                start_time=start_str,
                end_time=end_str,
                adjust=adj_mode,
                fields="symbol,eob,open,high,low,close,volume,amount,pre_close",
            )

            # 掘金返回 list，需要转换为 DataFrame
            if result is None or len(result) == 0:
                continue

            if isinstance(result, list):
                df = pd.DataFrame([vars(item) if hasattr(item, '__dict__') else item for item in result])
            else:
                df = result

            if df.empty:
                continue

            # 重命名列
            df = df.rename(columns={"eob": "date"})

            # 提取日期部分
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.date

            # 计算复权因子（后复权价 / 实际价 = adj_factor）
            # 掘金返回的已经是复权后价格，这里用 close/pre_close 近似
            if "pre_close" in df.columns and adj_mode != 0:
                # 简化处理：复权因子设为1（因掘金直接返回复权价）
                df["adj_factor"] = 1.0
                df = df.drop(columns=["pre_close"])
            else:
                df["adj_factor"] = 1.0

            # 确保列顺序
            expected_cols = [
                "symbol", "date", "open", "high", "low",
                "close", "volume", "amount", "adj_factor"
            ]
            df = df[[c for c in expected_cols if c in df.columns]]

            yield df

        logger.info(f"K线获取完成: {len(symbols)} 只股票, {start_date} ~ {end_date}")
