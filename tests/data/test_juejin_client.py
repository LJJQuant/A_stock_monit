# -*- coding: utf-8 -*-
"""
掘金客户端集成测试

运行方式: python -m tests.data.test_juejin_client
"""

from datetime import date, timedelta

from src.common.config import load_config
from src.data.source.juejin_client import JuejinClient
from src.utils.symbol_utils import to_juejin_symbol, from_juejin_symbol


def test_symbol_convert():
    """测试代码转换"""
    print("\n=== 测试代码转换 ===")

    # 纯数字 -> 掘金格式
    cases = [
        ("600000", "SHSE.600000"),  # 上海主板
        ("000001", "SZSE.000001"),  # 深圳主板
        ("300750", "SZSE.300750"),  # 创业板
        ("688001", "SHSE.688001"),  # 科创板
    ]

    for code, expected in cases:
        result = to_juejin_symbol(code)
        status = "✓" if result == expected else "✗"
        print(f"  {status} to_juejin_symbol('{code}') = '{result}' (期望: {expected})")

    # 掘金格式 -> 纯数字
    for expected, symbol in cases:
        result = from_juejin_symbol(symbol)
        status = "✓" if result == expected else "✗"
        print(f"  {status} from_juejin_symbol('{symbol}') = '{result}' (期望: {expected})")


def test_stock_pool(client: JuejinClient):
    """测试获取股票池"""
    print("\n=== 测试获取股票池 ===")

    stocks = client.get_stock_pool(["main"])
    print(f"  主板股票数量: {len(stocks)}")

    if stocks:
        # 显示前5只
        print("  前5只股票:")
        for s in stocks[:5]:
            print(f"    {s.symbol} {s.name} ST={s.is_st} 停牌={s.is_suspended}")

        # 统计ST数量
        st_count = sum(1 for s in stocks if s.is_st)
        suspended_count = sum(1 for s in stocks if s.is_suspended)
        print(f"  ST股票: {st_count}, 停牌股票: {suspended_count}")


def test_trading_calendar(client: JuejinClient):
    """测试获取交易日历"""
    print("\n=== 测试获取交易日历 ===")

    # 获取最近30天
    end = date.today()
    start = end - timedelta(days=30)

    calendar = client.get_trading_calendar("SHSE", start, end)
    trading_days = [d for d in calendar if d.is_trading_day]

    print(f"  日期范围: {start} ~ {end}")
    print(f"  总天数: {len(calendar)}, 交易日: {len(trading_days)}")

    if trading_days:
        last = trading_days[-1]
        print(f"  最近交易日: {last.date}, 前一交易日: {last.prev_trading_day}")


def test_kline(client: JuejinClient):
    """测试获取K线"""
    print("\n=== 测试获取K线 ===")

    # 用纯数字代码，转换为掘金格式
    codes = ["600000", "000001", "300750"]
    symbols = [to_juejin_symbol(c) for c in codes]
    print(f"  测试股票: {codes} -> {symbols}")

    end = date.today()
    start = end - timedelta(days=30)

    total_rows = 0
    for df in client.get_kline(symbols, start, end):
        total_rows += len(df)
        print(f"  批次获取: {len(df)} 行")

        if not df.empty:
            print(f"  列名: {list(df.columns)}")
            print(f"  样例数据:\n{df.head(3).to_string()}")

    print(f"  总计: {total_rows} 行K线数据")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("掘金客户端集成测试")
    print("=" * 50)

    # 1. 测试代码转换（不需要API）
    test_symbol_convert()

    # 2. 加载配置，创建客户端
    try:
        config = load_config()
        token = config.platform.juejin_token
        print(f"\n已加载Token: {token[:10]}...")
    except Exception as e:
        print(f"\n配置加载失败: {e}")
        print("请确保 config/settings.yaml 存在且包含 juejin_token")
        return

    client = JuejinClient(token=token)

    # 3. 测试API功能
    try:
        test_stock_pool(client)
        test_trading_calendar(client)
        test_kline(client)
        print("\n" + "=" * 50)
        print("全部测试通过!")
        print("=" * 50)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
