# -*- coding: utf-8 -*-
"""
数据库管理模块测试
"""

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import load_config
from src.common.db import DatabaseManager


def test_db_manager():
    """测试数据库管理器"""
    print("[TEST] 数据库管理器测试")
    print()

    try:
        # 加载配置
        config_path = PROJECT_ROOT / "config" / "settings.yaml"
        cfg = load_config(config_path)
        print(f"  [配置加载] {config_path} [OK]")

        # 创建管理器
        db_mgr = DatabaseManager(cfg)
        print(f"  [管理器创建] DatabaseManager [OK]")
        print()

        # 检查目录创建
        print("  [数据目录检查]")
        data_dir = cfg.database.daily_kline.parent
        if data_dir.exists():
            print(f"      {data_dir} (已创建) [OK]")
        else:
            print(f"      {data_dir} (未创建) [FAIL]")
            return False

        print()

        # 测试各数据库连接
        print("  [数据库连接测试]")
        db_names = [
            ("daily_kline", "日K线数据库"),
            ("stock_meta", "股票元信息数据库"),
            ("realtime", "实时数据库"),
            ("backtest", "回测数据库"),
        ]

        for db_name, cn_name in db_names:
            with db_mgr.get_connection(db_name) as conn:
                result = conn.execute("SELECT 1 + 1").fetchone()
                if result and result[0] == 2:
                    print(f"      {db_name} ({cn_name}): 连接成功 [OK]")
                else:
                    print(f"      {db_name} ({cn_name}): 连接失败 [FAIL]")
                    return False

        print()

        # 检查数据库文件
        print("  [数据库文件检查]")
        for db_name, cn_name in db_names:
            db_path = getattr(cfg.database, db_name)
            if db_path.exists():
                size = db_path.stat().st_size
                print(f"      {db_path.name} ({cn_name}): {size} bytes [OK]")
            else:
                print(f"      {db_path.name} ({cn_name}): 文件不存在 [FAIL]")
                return False

        print()
        print("  [PASS] 数据库管理器测试通过")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("数据库管理模块测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    result = test_db_manager()

    print()
    print("=" * 60)
    print(f"测试结果: {'通过' if result else '失败'}")
    print("=" * 60)
