# -*- coding: utf-8 -*-
"""
K线同步服务

支持断点续传的初始化和增量更新。
"""

from datetime import date, timedelta

from loguru import logger

from src.common.config import load_config
from src.data.source.juejin_client import JuejinClient
from src.data.repository.kline import KlineRepository
from src.data.query.stock_query import StockQuery


class KlineSyncService:
    """
    K线同步服务

    功能：
    - 初始化同步：2023-01-01 至 2026-01-01，支持断点续传
    - 增量更新：仅在初始化完成后可用
    """

    # 初始化日期范围
    INIT_START = date(2023, 1, 1)
    INIT_END = date(2026, 1, 1)

    # 目标板块
    TARGET_BOARDS = ["main", "gem"]

    def __init__(
        self,
        juejin_client: JuejinClient,
        kline_repo: KlineRepository,
        stock_query: StockQuery,
    ) -> None:
        self._client = juejin_client
        self._kline_repo = kline_repo
        self._stock_query = stock_query

    def get_target_symbols(self) -> list[str]:
        """获取目标股票列表（主板+创业板，按代码排序）"""
        symbols = []
        for board in self.TARGET_BOARDS:
            symbols.extend(self._stock_query.get_symbols(board))
        return sorted(set(symbols))

    def init_sync(self) -> None:
        """
        初始化同步（支持断点续传）

        从2023-01-01同步到2026-01-01，逐只股票下载。
        中断后重新运行会自动跳过已完成的股票。
        """
        # 检查是否已完成
        if self._kline_repo.is_init_completed():
            logger.info("初始化已完成，跳过")
            return

        # 标记进行中
        self._kline_repo.set_init_status("init_in_progress")

        # 获取目标股票
        all_symbols = self.get_target_symbols()
        if not all_symbols:
            logger.error("股票池为空，请先同步股票池")
            return

        # 获取已完成的股票
        completed = self._kline_repo.get_completed_symbols()
        remaining = [s for s in all_symbols if s not in completed]

        logger.info(f"初始化同步: 总计 {len(all_symbols)} 只, 已完成 {len(completed)}, 剩余 {len(remaining)}")

        if not remaining:
            self._kline_repo.set_init_status("init_completed")
            logger.info("全部完成!")
            return

        # 逐只同步
        for i, symbol in enumerate(remaining):
            current = len(completed) + i + 1
            logger.info(f"[{current}/{len(all_symbols)}] {symbol} 开始...")

            try:
                self._sync_single_stock(symbol, self.INIT_START, self.INIT_END)
                self._kline_repo.mark_symbol_completed(symbol, self.INIT_END)
                logger.info(f"[{current}/{len(all_symbols)}] {symbol} 完成")
            except Exception as e:
                logger.error(f"[{current}/{len(all_symbols)}] {symbol} 失败: {e}")
                # 继续下一只，不中断

        # 检查是否全部完成
        final_completed = self._kline_repo.get_completed_symbols()
        if len(final_completed) >= len(all_symbols):
            self._kline_repo.set_init_status("init_completed")
            self._kline_repo.update_sync_date(self.INIT_END)
            logger.info("初始化全部完成!")
        else:
            failed_count = len(all_symbols) - len(final_completed)
            logger.warning(f"初始化完成，但有 {failed_count} 只股票失败")

    def _sync_single_stock(self, symbol: str, start: date, end: date) -> int:
        """
        同步单只股票K线

        Returns
        -------
        int
            保存的记录数
        """
        total_count = 0

        # get_kline 返回迭代器（分批）
        for df in self._client.get_kline([symbol], start, end, adjust="post"):
            if df.empty:
                continue

            # 确保有 pre_close 列
            if "pre_close" not in df.columns:
                df["pre_close"] = 0.0

            count = self._kline_repo.save_kline(df)
            total_count += count

        return total_count

    def incremental_sync(self) -> None:
        """
        增量更新

        仅在初始化完成后可用。
        从上次同步日期更新到今天。
        """
        if not self._kline_repo.is_init_completed():
            logger.error("初始化未完成，无法增量更新。请先运行 init_sync()")
            return

        last_date = self._kline_repo.get_last_sync_date()
        today = date.today()

        if last_date and last_date >= today:
            logger.info(f"数据已是最新 ({last_date})，无需更新")
            return

        # 从上次同步日期的下一天开始
        start = last_date + timedelta(days=1) if last_date else self.INIT_END

        logger.info(f"增量更新: {start} -> {today}")

        # 获取所有目标股票
        symbols = self.get_target_symbols()
        if not symbols:
            logger.error("股票池为空")
            return

        # 分批下载
        total_count = 0
        for df in self._client.get_kline(symbols, start, today, adjust="post"):
            if df.empty:
                continue
            if "pre_close" not in df.columns:
                df["pre_close"] = 0.0
            count = self._kline_repo.save_kline(df)
            total_count += count

        # 更新同步日期
        self._kline_repo.update_sync_date(today)
        logger.info(f"增量更新完成，保存 {total_count} 条记录")


def create_kline_sync_service() -> KlineSyncService:
    """创建K线同步服务（使用默认配置）"""
    config = load_config()
    client = JuejinClient(token=config.platform.juejin_token)
    kline_repo = KlineRepository(config.database.daily_kline)
    stock_query = StockQuery()
    return KlineSyncService(client, kline_repo, stock_query)
