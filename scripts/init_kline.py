# -*- coding: utf-8 -*-
"""
K线数据初始化

在 Spyder 中直接运行对应的函数即可：
    show_status()   # 查看状态
    reset()         # 重置进度
    init()          # 开始初始化
    retry_failed()  # 补充初始化失败的股票
"""

from datetime import date

from loguru import logger

from src.common.config import load_config
from src.data.repository.kline import KlineRepository
from src.data.query.stock_query import StockQuery
from src.data.source.juejin_client import JuejinClient


def show_status():
    """查看当前状态"""
    config = load_config()
    kline_repo = KlineRepository(config.database.daily_kline)
    stock_query = StockQuery()

    print("=" * 50)
    print("K线初始化状态")
    print("=" * 50)

    # 股票池状态
    main_count = len(stock_query.get_symbols("main"))
    gem_count = len(stock_query.get_symbols("gem"))
    total_target = main_count + gem_count
    print(f"\n目标股票: {total_target} 只 (主板 {main_count}, 创业板 {gem_count})")

    # 初始化状态
    is_completed = kline_repo.is_init_completed()
    completed_count = kline_repo.get_symbol_count()
    print(f"已完成股票: {completed_count} 只")
    print(f"初始化状态: {'已完成' if is_completed else '未完成'}")

    # K线数据
    kline_count = kline_repo.count()
    symbol_count = kline_repo.count_symbols()
    print(f"\nK线记录数: {kline_count:,}")
    print(f"有数据股票: {symbol_count} 只")

    # 失败的股票
    all_symbols = set(stock_query.get_symbols("main") + stock_query.get_symbols("gem"))
    completed = kline_repo.get_completed_symbols()
    failed = all_symbols - completed
    if failed:
        print(f"\n失败股票: {len(failed)} 只")

    # 进度
    if total_target > 0:
        progress = completed_count / total_target * 100
        print(f"\n进度: {progress:.1f}%")

    print("=" * 50)


def reset():
    """重置进度（重新开始初始化）"""
    config = load_config()
    kline_repo = KlineRepository(config.database.daily_kline)

    print("重置初始化进度...")
    kline_repo.clear_sync_status()
    kline_repo.set_init_status("init_reset")
    print("已重置！可以重新运行 init()")


def init():
    """执行初始化（支持断点续传）"""
    from src.data.service.kline_sync import create_kline_sync_service

    # 检查股票池
    stock_query = StockQuery()
    pool_count = len(stock_query.get_symbols())
    if pool_count == 0:
        print("错误: 股票池为空！请先同步股票池")
        return

    logger.info("开始K线初始化...")
    service = create_kline_sync_service()
    service.init_sync()


def retry_failed():
    """补充初始化失败的股票"""
    config = load_config()
    kline_repo = KlineRepository(config.database.daily_kline)
    stock_query = StockQuery()
    client = JuejinClient(token=config.platform.juejin_token)

    # 获取失败的股票
    all_symbols = set(stock_query.get_symbols("main") + stock_query.get_symbols("gem"))
    completed = kline_repo.get_completed_symbols()
    failed = sorted(all_symbols - completed)

    if not failed:
        print("没有失败的股票，无需补充")
        return

    print(f"发现 {len(failed)} 只失败股票，开始补充初始化...")

    # 初始化日期范围
    start = date(2023, 1, 1)
    end = date(2026, 1, 1)

    success_count = 0
    for i, symbol in enumerate(failed):
        logger.info(f"[{i+1}/{len(failed)}] {symbol} 开始...")

        try:
            total = 0
            for df in client.get_kline([symbol], start, end, adjust="post"):
                if df.empty:
                    continue
                if "pre_close" not in df.columns:
                    df["pre_close"] = 0.0
                total += kline_repo.save_kline(df)

            kline_repo.mark_symbol_completed(symbol, end)
            logger.info(f"[{i+1}/{len(failed)}] {symbol} 完成，{total} 条记录")
            success_count += 1
        except Exception as e:
            logger.error(f"[{i+1}/{len(failed)}] {symbol} 失败: {e}")

    print(f"\n补充完成: 成功 {success_count}, 失败 {len(failed) - success_count}")


# ======================
# 在 Spyder 里直接调用：
# ======================
# show_status()   # 查看状态
# reset()         # 重置
# init()          # 开始初始化
# retry_failed()  # 补充失败的股票
