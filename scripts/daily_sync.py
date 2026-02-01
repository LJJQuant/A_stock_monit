# -*- coding: utf-8 -*-
"""
日常数据同步脚本

每日收盘后运行（建议15:30），执行数据同步任务。

运行方式:
    python scripts/daily_sync.py

定时任务配置(Windows):
    schtasks /create /tn "A股数据同步" /tr "python E:\\Quantli\\A_stock_monit\\scripts\\daily_sync.py" /sc daily /st 15:30

定时任务配置(Linux crontab):
    30 15 * * 1-5 cd /path/to/A_stock_monit && python scripts/daily_sync.py
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from loguru import logger

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import load_config
from src.data.source.juejin_client import JuejinClient
from src.data.repository.trading_calendar import TradingCalendarRepository
from src.data.repository.stock_pool import StockPoolRepository


# ============================================================
# 日志配置
# ============================================================

def setup_logging() -> None:
    """配置 loguru 日志"""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"daily_sync_{date.today().strftime('%Y%m')}.log"

    # 移除默认 handler，重新配置
    logger.remove()

    # 控制台输出（彩色）
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
        colorize=True,
    )

    # 文件输出
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        encoding="utf-8",
        rotation="1 month",  # 每月轮转
    )


# ============================================================
# 同步任务
# ============================================================

def sync_trading_calendar(
    client: JuejinClient,
    repo: TradingCalendarRepository,
    force: bool = False,
) -> bool:
    """
    同步交易日历

    Parameters
    ----------
    client : JuejinClient
        掘金客户端
    repo : TradingCalendarRepository
        交易日历仓库
    force : bool
        是否强制同步（忽略时间检查）

    Returns
    -------
    bool
        是否执行了同步
    """
    # 检查是否需要同步（30天内同步过则跳过）
    if not force and not repo.needs_sync(max_age_days=30):
        last_sync = repo.get_last_sync_time()
        logger.info(f"交易日历无需同步，上次同步: {last_sync}")
        return False

    logger.info("开始同步交易日历...")

    # 同步范围：往前1年 + 往后半年
    today = date.today()
    start_date = date(today.year - 1, today.month, 1)
    end_date = today + timedelta(days=180)  # 往后半年

    # 上海交易所
    shse_days = client.get_trading_calendar("SHSE", start_date, end_date)
    shse_count = repo.save(shse_days)
    logger.info(f"上交所交易日历: {shse_count} 条")

    # 深圳交易所
    szse_days = client.get_trading_calendar("SZSE", start_date, end_date)
    szse_count = repo.save(szse_days)
    logger.info(f"深交所交易日历: {szse_count} 条")

    logger.success(f"交易日历同步完成，共 {shse_count + szse_count} 条")
    return True


def sync_stock_pool(
    client: JuejinClient,
    repo: StockPoolRepository,
    force: bool = False,
) -> bool:
    """
    同步股票池

    Parameters
    ----------
    client : JuejinClient
        掘金客户端
    repo : StockPoolRepository
        股票池仓库
    force : bool
        是否强制同步（忽略时间检查）

    Returns
    -------
    bool
        是否执行了同步
    """
    # 检查是否需要同步（23小时内同步过则跳过）
    if not force and not repo.needs_sync(max_age_hours=23):
        last_sync = repo.get_last_sync_time()
        logger.info(f"股票池无需同步，上次同步: {last_sync}")
        return False

    logger.info("开始同步股票池...")

    stocks = client.get_stock_pool()
    count = repo.save(stocks)

    # 统计
    st_count = sum(1 for s in stocks if s.is_st)
    suspended_count = sum(1 for s in stocks if s.is_suspended)

    logger.success(f"股票池同步完成: {count} 只 (ST: {st_count}, 停牌: {suspended_count})")
    return True


def run_daily_sync(force: bool = False) -> None:
    """
    执行日常同步

    Parameters
    ----------
    force : bool
        是否强制同步所有数据
    """
    start_time = datetime.now()
    logger.info("=" * 40)
    logger.info(f"日常数据同步开始")
    logger.info("=" * 40)

    try:
        # 加载配置
        config = load_config()
        client = JuejinClient(token=config.platform.juejin_token)

        # 1. 同步交易日历（30天更新一次）
        calendar_repo = TradingCalendarRepository(config.database.stock_meta)
        sync_trading_calendar(client, calendar_repo, force=force)

        # 2. 同步股票池（23小时更新一次）
        stock_pool_repo = StockPoolRepository(config.database.stock_meta)
        sync_stock_pool(client, stock_pool_repo, force=force)

        # TODO: 3. 同步K线数据

        elapsed = datetime.now() - start_time
        logger.info("=" * 40)
        logger.success(f"全部同步完成，耗时: {elapsed.total_seconds():.1f}秒")
        logger.info("=" * 40)

    except Exception as e:
        logger.error(f"同步失败: {e}")
        raise


# ============================================================
# 入口
# ============================================================

def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="日常数据同步")
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制同步（忽略时间检查）",
    )
    args = parser.parse_args()

    setup_logging()
    run_daily_sync(force=args.force)


if __name__ == "__main__":
    main()
