# -*- coding: utf-8 -*-
"""
K线仓库测试

运行方式:
    python -m tests.data.test_kline
"""

from datetime import date

import pandas as pd

from src.common.config import load_config
from src.data.repository.kline import KlineRepository


def test_basic(repo: KlineRepository):
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")

    # 初始化状态
    is_completed = repo.is_init_completed()
    print(f"  初始化完成: {is_completed}")

    # 已完成股票数
    completed_count = repo.get_symbol_count()
    print(f"  已完成股票数: {completed_count}")

    # K线记录数
    kline_count = repo.count()
    print(f"  K线记录数: {kline_count}")

    # 有数据的股票数
    symbol_count = repo.count_symbols()
    print(f"  有数据股票数: {symbol_count}")


def test_save_and_query(repo: KlineRepository):
    """测试保存和查询"""
    print("\n=== 测试保存和查询 ===")

    # 构造测试数据
    test_data = pd.DataFrame([
        {
            "symbol": "SHSE.600000",
            "date": date(2024, 1, 2),
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000,
            "amount": 10200000.0,
            "pre_close": 9.9,
        },
        {
            "symbol": "SHSE.600000",
            "date": date(2024, 1, 3),
            "open": 10.2,
            "high": 10.8,
            "low": 10.1,
            "close": 10.6,
            "volume": 1200000,
            "amount": 12720000.0,
            "pre_close": 10.2,
        },
    ])

    # 保存
    count = repo.save_kline(test_data)
    print(f"  保存记录数: {count}")

    # 查询
    df = repo.get_kline("SHSE.600000", date(2024, 1, 1), date(2024, 1, 31))
    print(f"  查询到记录数: {len(df)}")
    if not df.empty:
        print(f"  数据:\n{df}")

    # 最新日期
    latest = repo.get_latest_date("SHSE.600000")
    print(f"  最新日期: {latest}")


def test_sync_status(repo: KlineRepository):
    """测试同步状态"""
    print("\n=== 测试同步状态 ===")

    # 标记完成
    repo.mark_symbol_completed("SHSE.600000", date(2026, 1, 1))
    repo.mark_symbol_completed("SZSE.000001", date(2026, 1, 1))

    # 获取已完成
    completed = repo.get_completed_symbols()
    print(f"  已完成股票: {completed}")

    # 设置初始化状态
    repo.set_init_status("init_in_progress")
    print(f"  初始化完成: {repo.is_init_completed()}")

    repo.set_init_status("init_completed")
    print(f"  初始化完成: {repo.is_init_completed()}")


def main():
    print("=" * 50)
    print("K线仓库测试")
    print("=" * 50)

    config = load_config()
    repo = KlineRepository(config.database.daily_kline)

    test_basic(repo)
    test_save_and_query(repo)
    test_sync_status(repo)

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
