# -*- coding: utf-8 -*-
"""
配置生成器测试

测试内容：
1. Schema 完整性验证
2. 配置生成功能
3. YAML 文件保存
4. 覆盖默认值功能
"""

import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

# 把项目根目录加入 path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config_schema import (
    CONFIG_SCHEMA,
    SECTION_NAMES,
    PLATFORM_SCHEMA,
    DATABASE_SCHEMA,
    TECHNICAL_INDICATORS_SCHEMA,
)
from src.common.config_generator import (
    build_config_section,
    generate_config,
    save_config,
)


# ============================================================
# 测试用例
# ============================================================

def test_schema_completeness():
    """测试 Schema 完整性"""
    print("[TEST] Schema 完整性验证")
    print()

    try:
        # 检查所有分区都有中文名称
        print("  [分区名称检查]")
        all_have_names = True
        for section_key in CONFIG_SCHEMA.keys():
            name = SECTION_NAMES.get(section_key)
            status = "[OK]" if name else "[FAIL]"
            print(f"      {section_key:25} -> {name or '缺少名称'} {status}")
            if not name:
                all_have_names = False

        print()

        # 检查每个配置项都有默认值和注释
        print("  [配置项格式检查]")
        format_ok = True
        for section_key, section_schema in CONFIG_SCHEMA.items():
            for key, value in section_schema.items():
                if not isinstance(value, tuple) or len(value) != 2:
                    print(f"      {section_key}.{key}: 格式错误，应为 (默认值, 注释) [FAIL]")
                    format_ok = False

        if format_ok:
            print("      所有配置项格式正确 (默认值, 注释) [OK]")

        print()

        # 统计
        total_keys = sum(len(s) for s in CONFIG_SCHEMA.values())
        print(f"  [统计信息]")
        print(f"      分区数量: {len(CONFIG_SCHEMA)}")
        print(f"      配置项总数: {total_keys}")

        print()
        if all_have_names and format_ok:
            print("  [PASS] Schema 完整性验证通过")
            return True
        else:
            print("  [FAIL] Schema 存在问题")
            return False

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_build_config_section():
    """测试单个配置块生成"""
    print("[TEST] 单个配置块生成")
    print()

    try:
        # 使用 PLATFORM_SCHEMA 测试
        print("  [测试 PLATFORM_SCHEMA 平台配置]")
        section = build_config_section(PLATFORM_SCHEMA)

        # 检查所有 key 都存在
        for key in PLATFORM_SCHEMA.keys():
            if key in section:
                default_val, _ = PLATFORM_SCHEMA[key]
                actual_val = section[key]
                status = "[OK]" if actual_val == default_val else "[FAIL]"
                print(f"      {key}: {str(actual_val)[:30]}... {status}")
            else:
                print(f"      {key}: 缺失 [FAIL]")
                return False

        print()

        # 测试覆盖功能
        print("  [测试覆盖默认值功能]")
        overrides = {'web_port': 9999, 'web_host': '0.0.0.0'}
        section_with_override = build_config_section(PLATFORM_SCHEMA, overrides)

        if section_with_override['web_port'] == 9999:
            print(f"      web_port 覆盖为 9999 [OK]")
        else:
            print(f"      web_port 覆盖失败 [FAIL]")
            return False

        if section_with_override['web_host'] == '0.0.0.0':
            print(f"      web_host 覆盖为 0.0.0.0 [OK]")
        else:
            print(f"      web_host 覆盖失败 [FAIL]")
            return False

        print()
        print("  [PASS] 配置块生成正确")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_full_config():
    """测试完整配置生成"""
    print("[TEST] 完整配置生成")
    print()

    try:
        config = generate_config()

        print("  [检查所有分区是否生成]")
        all_sections_ok = True
        for section_key in CONFIG_SCHEMA.keys():
            if section_key in config:
                count = len(config[section_key])
                print(f"      {section_key:25} -> {count} 个配置项 [OK]")
            else:
                print(f"      {section_key:25} -> 缺失 [FAIL]")
                all_sections_ok = False

        print()

        # 检查 meta.generated_at 是否自动填充
        print("  [检查自动填充字段]")
        if config['meta']['generated_at']:
            print(f"      meta.generated_at (生成时间): {config['meta']['generated_at']} [OK]")
        else:
            print(f"      meta.generated_at (生成时间): 未填充 [FAIL]")
            all_sections_ok = False

        print()
        if all_sections_ok:
            print("  [PASS] 完整配置生成正确")
            return True
        else:
            print("  [FAIL] 配置生成存在问题")
            return False

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_config():
    """测试配置文件保存"""
    print("[TEST] 配置文件保存")
    print()

    try:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_settings.yaml"

            # 生成并保存
            config = generate_config()
            save_config(config, output_path)

            print(f"  [保存路径] {output_path}")

            # 检查文件是否存在
            if output_path.exists():
                print(f"      文件创建成功 [OK]")
            else:
                print(f"      文件创建失败 [FAIL]")
                return False

            # 检查文件大小
            size = output_path.stat().st_size
            print(f"      文件大小: {size} 字节 [OK]")

            # 检查文件内容
            content = output_path.read_text(encoding='utf-8')

            # 检查是否有分区注释
            print()
            print("  [检查文件内容]")

            checks = [
                ('# A', '文件头注释'),
                ('platform:', 'platform 平台配置分区'),
                ('database:', 'database 数据库配置分区'),
                ('technical_indicators:', 'technical_indicators 技术指标分区'),
                ('juejin_token:', 'juejin_token 掘金Token字段'),
                ('kdj_n:', 'kdj_n KDJ周期字段'),
            ]

            all_checks_pass = True
            for pattern, desc in checks:
                if pattern in content:
                    print(f"      {desc}: 存在 [OK]")
                else:
                    print(f"      {desc}: 缺失 [FAIL]")
                    all_checks_pass = False

            print()
            if all_checks_pass:
                print("  [PASS] 配置文件保存正确")
                return True
            else:
                print("  [FAIL] 配置文件内容有问题")
                return False

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_with_overrides():
    """测试带覆盖值的配置生成"""
    print("[TEST] 带覆盖值的配置生成")
    print()

    try:
        overrides = {
            'platform': {
                'web_port': 8888,
            },
            'technical_indicators': {
                'kdj_n': 14,
                'ma_periods': [5, 10, 30],
            },
        }

        config = generate_config(overrides)

        print("  [检查覆盖结果]")

        # 检查 web_port
        if config['platform']['web_port'] == 8888:
            print(f"      platform.web_port (Web端口): 8888 [OK]")
        else:
            print(f"      platform.web_port (Web端口): {config['platform']['web_port']} [FAIL]")
            return False

        # 检查 kdj_n
        if config['technical_indicators']['kdj_n'] == 14:
            print(f"      technical_indicators.kdj_n (KDJ周期): 14 [OK]")
        else:
            print(f"      technical_indicators.kdj_n (KDJ周期): {config['technical_indicators']['kdj_n']} [FAIL]")
            return False

        # 检查 ma_periods
        if config['technical_indicators']['ma_periods'] == [5, 10, 30]:
            print(f"      technical_indicators.ma_periods (均线周期): [5, 10, 30] [OK]")
        else:
            print(f"      technical_indicators.ma_periods (均线周期): {config['technical_indicators']['ma_periods']} [FAIL]")
            return False

        # 检查未覆盖的值保持默认
        default_kdj_m1, _ = TECHNICAL_INDICATORS_SCHEMA['kdj_m1']
        if config['technical_indicators']['kdj_m1'] == default_kdj_m1:
            print(f"      technical_indicators.kdj_m1 (KDJ M1周期): {default_kdj_m1} (默认值保持) [OK]")
        else:
            print(f"      technical_indicators.kdj_m1 (KDJ M1周期): 默认值被意外修改 [FAIL]")
            return False

        print()
        print("  [PASS] 覆盖值功能正确")
        return True

    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("配置生成器测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    results = []

    results.append(test_schema_completeness())
    print()
    print("-" * 60)
    print()

    results.append(test_build_config_section())
    print()
    print("-" * 60)
    print()

    results.append(test_generate_full_config())
    print()
    print("-" * 60)
    print()

    results.append(test_save_config())
    print()
    print("-" * 60)
    print()

    results.append(test_generate_with_overrides())

    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
