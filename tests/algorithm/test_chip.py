# -*- coding: utf-8 -*-
"""
筹码分布模块测试
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.symbol_utils import to_eastmoney_code
from src.crawler.eastmoney_kline import get_kline
from src.algorithm.chip_distribution import calculate_chip


def test_symbol_utils():
    """测试股票代码转换"""
    print("[TEST] 股票代码转换")
    print()

    cases = [
        ('000001', '0.000001', '深圳主板'),
        ('600000', '1.600000', '上海主板'),
        ('300750', '0.300750', '创业板'),
        ('605058', '1.605058', '上海主板'),
    ]

    for code, expected, desc in cases:
        result = to_eastmoney_code(code)
        status = '[OK]' if result == expected else '[FAIL]'
        print(f"  {code} ({desc}) -> {result} {status}")

    print()
    return True


def test_crawler():
    """测试K线爬虫"""
    print("[TEST] 东方财富K线爬虫")
    print()

    try:
        code = '605058'
        kline = get_kline(code, klt='daily', limit=10, end_date='20260201')

        print(f"  股票代码: {code}")
        print(f"  获取条数: {len(kline)}")

        if len(kline) > 0:
            print(f"  最新K线: {kline[-1][0]} 收盘:{kline[-1][2]}")
            print("  [OK]")
        else:
            print("  [FAIL] 无数据")
            return False

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        return False

    print()
    return True


def test_chip_calculation():
    """测试筹码计算"""
    print("[TEST] 筹码分布计算")
    print()

    try:
        # 获取K线数据
        code = '605058'
        kline = get_kline(code, klt='daily', limit=210, end_date='20260201')
        print(f"  股票代码: {code}")
        print(f"  K线条数: {len(kline)}")

        # 计算筹码
        result = calculate_chip(kline)

        print(f"  获利比例: {result.benefit_part * 100:.2f}%")
        print(f"  平均成本: {result.avg_cost:.2f}")
        print(f"  90%集中度: {result.concentration_90 * 100:.2f}%")
        print(f"  90%价格范围: {result.price_range_90[0]:.2f} - {result.price_range_90[1]:.2f}")
        print("  [OK]")

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("筹码分布模块测试")
    print("=" * 60)
    print()

    results = []

    results.append(test_symbol_utils())
    print("-" * 60)

    results.append(test_crawler())
    print("-" * 60)

    results.append(test_chip_calculation())

    print("=" * 60)
    passed = sum(results)
    print(f"测试结果: {passed}/{len(results)} 通过")
    print("=" * 60)
