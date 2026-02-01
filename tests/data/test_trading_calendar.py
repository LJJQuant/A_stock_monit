# -*- coding: utf-8 -*-
"""
交易日历仓库测试

运行方式:
    python -m tests.data.test_trading_calendar        # 常规测试
    python -m tests.data.test_trading_calendar init   # 初始化同步（清空后从2022年开始）
"""

from datetime import date, timedelta

from src.common.config import load_config
from src.data.source.juejin_client import JuejinClient
from src.data.repository.trading_calendar import TradingCalendarRepository


def test_query(repo: TradingCalendarRepository):
    """测试查询功能"""
    print("\n=== 测试查询功能 ===")

    today = date.today()

    # 日期范围
    min_date, max_date = repo.get_date_range("SHSE")
    print(f"  上交所日期范围: {min_date} ~ {max_date}")

    # 全部交易日
    all_days = repo.get_all_trading_days("SHSE")
    print(f"  上交所交易日总数: {len(all_days)} 天")

    # 判断今天
    is_trading = repo.is_trading_day("SHSE", today)
    print(f"  今天 {today} 是否交易日: {is_trading}")

    # 前后交易日
    prev_day = repo.get_prev_trading_day("SHSE", today)
    next_day = repo.get_next_trading_day("SHSE", today)
    print(f"  前一交易日: {prev_day}")
    print(f"  下一交易日: {next_day}")

    # 最近交易日
    days = repo.get_trading_days("SHSE", today - timedelta(days=10), today + timedelta(days=10))
    print(f"  前后10天的交易日: {days}")


def test_sync_status(repo: TradingCalendarRepository):
    """测试同步状态"""
    print("\n=== 同步状态 ===")

    last_sync = repo.get_last_sync_time()
    needs = repo.needs_sync(max_age_days=30)
    print(f"  上次同步: {last_sync}")
    print(f"  是否需要同步(30天): {needs}")


def init_sync():
    """初始化同步（清空后从2022年开始）"""
    print("=" * 50)
    print("初始化同步交易日历")
    print("=" * 50)

    config = load_config()
    client = JuejinClient(token=config.platform.juejin_token)
    repo = TradingCalendarRepository(config.database.stock_meta)

    # 清空
    repo.truncate()
    print("\n已清空交易日历表")

    today = date.today()
    start_date = date(2022, 1, 1)
    end_date = today + timedelta(days=180)

    for exchange in ["SHSE", "SZSE"]:
        print(f"\n同步 {exchange}: {start_date} ~ {end_date}")
        trading_days = client.get_trading_calendar(exchange, start_date, end_date)
        count = repo.save(trading_days)
        print(f"  保存 {count} 条")

    # 验证
    test_query(repo)

    print("\n" + "=" * 50)
    print("初始化完成!")
    print("=" * 50)


def main():
    """常规测试"""
    print("=" * 50)
    print("交易日历仓库测试")
    print("=" * 50)

    config = load_config()
    repo = TradingCalendarRepository(config.database.stock_meta)

    test_sync_status(repo)
    test_query(repo)

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_sync()
    else:
        main()
