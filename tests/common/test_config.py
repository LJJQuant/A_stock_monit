# -*- coding: utf-8 -*-
"""
配置读取器测试

测试内容：
1. 配置文件加载
2. Dataclass 类型验证
3. 各分区访问
4. 路径转换
5. 异常处理
"""

import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

# 把项目根目录加入 path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import (
    load_config,
    AppConfig,
    PlatformConfig,
    DatabaseConfig,
    TechnicalIndicatorsConfig,
    DailyDataConfig,
    ConditionsConfig,
)
from src.common.config_generator import generate_config, save_config


# ============================================================
# 测试用例
# ============================================================

def test_load_config_success():
    """测试配置加载成功"""
    print("[TEST] 配置加载测试")
    print()

    try:
        # 使用项目真实配置文件
        config_path = PROJECT_ROOT / "config" / "settings.yaml"

        if not config_path.exists():
            print(f"  [SKIP] 配置文件不存在: {config_path}")
            print("  请先运行 config_generator.py 生成配置文件")
            return False

        print(f"  [配置路径] {config_path}")
        print()

        cfg = load_config(config_path)

        print("  [检查返回类型]")
        if isinstance(cfg, AppConfig):
            print(f"      返回类型: AppConfig (应用配置) [OK]")
        else:
            print(f"      返回类型: {type(cfg)} (类型错误) [FAIL]")
            return False

        print()
        print("  [PASS] 配置加载成功")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_sections():
    """测试各配置分区访问"""
    print("[TEST] 各配置分区访问测试")
    print()

    try:
        config_path = PROJECT_ROOT / "config" / "settings.yaml"
        cfg = load_config(config_path)

        print("  [检查各分区类型]")

        checks = [
            ('platform', PlatformConfig, '平台配置'),
            ('database', DatabaseConfig, '数据库配置'),
            ('technical_indicators', TechnicalIndicatorsConfig, '技术指标配置'),
            ('daily_data', DailyDataConfig, '日常数据配置'),
            ('conditions', ConditionsConfig, '预警条件配置'),
        ]

        all_ok = True
        for attr_name, expected_type, cn_name in checks:
            attr = getattr(cfg, attr_name, None)
            if isinstance(attr, expected_type):
                print(f"      cfg.{attr_name} ({cn_name}): {expected_type.__name__} [OK]")
            else:
                print(f"      cfg.{attr_name} ({cn_name}): 类型错误 [FAIL]")
                all_ok = False

        print()
        if all_ok:
            print("  [PASS] 所有分区类型正确")
            return True
        else:
            print("  [FAIL] 分区类型有误")
            return False

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_platform_config():
    """测试平台配置"""
    print("[TEST] 平台配置测试")
    print()

    try:
        config_path = PROJECT_ROOT / "config" / "settings.yaml"
        cfg = load_config(config_path)

        print("  [平台配置项]")

        # 检查 token
        if cfg.platform.juejin_token:
            token_preview = cfg.platform.juejin_token[:10] + "..."
            print(f"      juejin_token (掘金Token): {token_preview} [OK]")
        else:
            print(f"      juejin_token (掘金Token): 为空 [FAIL]")
            return False

        # 检查 webhook
        if cfg.platform.dingtalk_webhook:
            webhook_preview = cfg.platform.dingtalk_webhook[:40] + "..."
            print(f"      dingtalk_webhook (钉钉Webhook): {webhook_preview} [OK]")
        else:
            print(f"      dingtalk_webhook (钉钉Webhook): 为空 [FAIL]")
            return False

        # 检查 web 配置
        print(f"      web_host (Web地址): {cfg.platform.web_host} [OK]")
        print(f"      web_port (Web端口): {cfg.platform.web_port} [OK]")

        print()
        print("  [PASS] 平台配置正确")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_config_path():
    """测试数据库配置路径转换"""
    print("[TEST] 数据库路径转换测试")
    print()

    try:
        config_path = PROJECT_ROOT / "config" / "settings.yaml"
        cfg = load_config(config_path)

        print("  [检查路径类型是否为 Path 对象]")

        paths = [
            ('daily_kline', cfg.database.daily_kline, '历史日K线数据库'),
            ('stock_meta', cfg.database.stock_meta, '股票元信息数据库'),
            ('realtime', cfg.database.realtime, '实时数据库'),
            ('backtest', cfg.database.backtest, '回测数据库'),
        ]

        all_ok = True
        for name, path, cn_name in paths:
            if isinstance(path, Path):
                print(f"      database.{name} ({cn_name}): Path 类型 [OK]")
            else:
                print(f"      database.{name} ({cn_name}): {type(path)} 类型错误 [FAIL]")
                all_ok = False

        print()

        print("  [路径值]")
        for name, path, cn_name in paths:
            print(f"      database.{name} ({cn_name}): {path}")

        print()
        if all_ok:
            print("  [PASS] 路径转换正确")
            return True
        else:
            print("  [FAIL] 路径转换有误")
            return False

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_technical_indicators():
    """测试技术指标配置"""
    print("[TEST] 技术指标配置测试")
    print()

    try:
        config_path = PROJECT_ROOT / "config" / "settings.yaml"
        cfg = load_config(config_path)

        ti = cfg.technical_indicators

        print("  [技术指标参数值]")
        print(f"      kdj_n (KDJ N周期): {ti.kdj_n}")
        print(f"      kdj_m1 (KDJ M1周期): {ti.kdj_m1}")
        print(f"      kdj_m2 (KDJ M2周期): {ti.kdj_m2}")
        print(f"      ma_periods (均线周期列表): {ti.ma_periods}")

        print()

        # 验证类型
        print("  [类型验证]")

        if isinstance(ti.kdj_n, int):
            print(f"      kdj_n (KDJ N周期): int 类型 [OK]")
        else:
            print(f"      kdj_n (KDJ N周期): {type(ti.kdj_n)} 类型错误 [FAIL]")
            return False

        if isinstance(ti.ma_periods, list):
            print(f"      ma_periods (均线周期列表): list 类型 [OK]")
        else:
            print(f"      ma_periods (均线周期列表): {type(ti.ma_periods)} 类型错误 [FAIL]")
            return False

        print()
        print("  [PASS] 技术指标配置正确")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_daily_data_thresholds():
    """测试日常数据阈值"""
    print("[TEST] 日常数据阈值测试")
    print()

    try:
        config_path = PROJECT_ROOT / "config" / "settings.yaml"
        cfg = load_config(config_path)

        dd = cfg.daily_data

        print("  [日常数据阈值]")
        print(f"      turnover_rate (换手率): [{dd.turnover_rate_min}, {dd.turnover_rate_max}] %")
        print(f"      turnover_ratio (换手率倍数): [{dd.turnover_ratio_min}, {dd.turnover_ratio_max}]")
        print(f"      market_cap (流通市值): [{dd.market_cap_min/1e8:.1f}亿, {dd.market_cap_max/1e8:.1f}亿]")
        print(f"      amount (成交额): [{dd.amount_min/1e8:.2f}亿, {dd.amount_max/1e8:.2f}亿]")
        print(f"      daily_gain (当日涨幅): [{dd.daily_gain_min*100:.1f}%, {dd.daily_gain_max*100:.1f}%]")

        print()

        # 验证合理性
        print("  [合理性验证]")

        checks = [
            (dd.turnover_rate_min < dd.turnover_rate_max, '换手率 min < max'),
            (dd.market_cap_min < dd.market_cap_max, '流通市值 min < max'),
            (dd.amount_min < dd.amount_max, '成交额 min < max'),
            (dd.daily_gain_min < dd.daily_gain_max, '涨幅 min < max'),
            (dd.market_cap_min > 0, '流通市值 > 0'),
        ]

        all_ok = True
        for condition, desc in checks:
            status = "[OK]" if condition else "[FAIL]"
            print(f"      {desc}: {status}")
            if not condition:
                all_ok = False

        print()
        if all_ok:
            print("  [PASS] 日常数据阈值合理")
            return True
        else:
            print("  [FAIL] 阈值配置有误")
            return False

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_not_found():
    """测试配置文件不存在的异常处理"""
    print("[TEST] 文件不存在异常测试")
    print()

    try:
        non_existent_path = "/non/existent/path/settings.yaml"

        try:
            load_config(non_existent_path)
            print("  [FAIL] 应该抛出 FileNotFoundError 异常")
            return False
        except FileNotFoundError as e:
            print(f"  [捕获异常] FileNotFoundError: {e}")
            print()
            print("  [PASS] 异常处理正确")
            return True

    except Exception as e:
        print(f"  [FAIL] 意外异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("配置读取器测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    results = []

    results.append(test_load_config_success())
    print()
    print("-" * 60)
    print()

    results.append(test_config_sections())
    print()
    print("-" * 60)
    print()

    results.append(test_platform_config())
    print()
    print("-" * 60)
    print()

    results.append(test_database_config_path())
    print()
    print("-" * 60)
    print()

    results.append(test_technical_indicators())
    print()
    print("-" * 60)
    print()

    results.append(test_daily_data_thresholds())
    print()
    print("-" * 60)
    print()

    results.append(test_file_not_found())

    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
