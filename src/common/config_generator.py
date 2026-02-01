# -*- coding: utf-8 -*-
"""
配置文件生成器

根据Schema生成带注释的YAML配置文件。
"""
from pathlib import Path
from datetime import datetime
from io import StringIO

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
except ImportError:
    print("错误: 缺少 ruamel.yaml 库，请安装: pip install ruamel.yaml")
    raise

from src.common.config_schema import CONFIG_SCHEMA, SECTION_NAMES


def build_config_section(schema: dict, overrides: dict = None) -> CommentedMap:
    """
    根据Schema生成单个配置块

    Parameters
    ----------
    schema : dict
        配置定义 {key: (default_value, comment)}
    overrides : dict, optional
        覆盖默认值 {key: value}

    Returns
    -------
    CommentedMap
        带注释的配置字典
    """
    section = CommentedMap()
    overrides = overrides or {}

    for key, (default_value, comment) in schema.items():
        section[key] = overrides.get(key, default_value)
        section.yaml_add_eol_comment(comment, key)

    return section


def generate_config(overrides: dict = None) -> CommentedMap:
    """
    生成完整配置

    Parameters
    ----------
    overrides : dict, optional
        覆盖默认值 {'section': {'key': value}}

    Returns
    -------
    CommentedMap
        完整配置字典
    """
    overrides = overrides or {}
    config = CommentedMap()

    # 自动填充生成时间
    if 'meta' not in overrides:
        overrides['meta'] = {}
    overrides['meta']['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 遍历Schema生成各配置块
    for section_name, section_schema in CONFIG_SCHEMA.items():
        section_overrides = overrides.get(section_name, {})
        config[section_name] = build_config_section(section_schema, section_overrides)

    return config


def save_config(config: CommentedMap, output_path: Path) -> None:
    """
    保存配置到YAML文件

    Parameters
    ----------
    config : CommentedMap
        配置字典
    output_path : Path
        输出文件路径
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=2, offset=0)

    with open(output_path, 'w', encoding='utf-8') as f:
        # 文件头
        f.write('# ' + '=' * 62 + '\n')
        f.write('# A股预警系统配置文件\n')
        f.write(f'# 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('# ' + '=' * 62 + '\n\n')

        # 写入各模块
        for section_key in CONFIG_SCHEMA.keys():
            f.write('# ' + '=' * 62 + '\n')
            f.write(f'# {SECTION_NAMES.get(section_key, section_key)}\n')
            f.write('# ' + '=' * 62 + '\n')

            temp_config = CommentedMap()
            temp_config[section_key] = config[section_key]

            string_stream = StringIO()
            yaml.dump(temp_config, string_stream)
            f.write(string_stream.getvalue() + '\n')


def main() -> None:
    """生成默认配置文件"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "config" / "settings.yaml"

    # 生成配置
    config = generate_config()

    # 保存文件
    save_config(config, output_path)

    print(f"[OK] 配置文件已生成: {output_path}")


if __name__ == "__main__":
    main()
