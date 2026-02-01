# -*- coding: utf-8 -*-
"""
掘金量化文档爬虫

把 Python SDK 文档全部抓取保存到本地。
"""

import httpx
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import time
import urllib.parse
import re

# 文档基础URL
BASE_URL = "https://www.myquant.cn/docs2/sdk/python/"

# 按一级目录组织的页面列表
PAGES = [
    # 顶级页面
    ("快速开始.html", "快速开始"),
    ("策略程序架构.html", "策略程序架构"),
    ("变量约定.html", "变量约定"),
    ("数据结构.html", "数据结构"),

    # API介绍 子页面
    ("API介绍/基本函数.html", "API-基本函数"),
    ("API介绍/数据订阅.html", "API-数据订阅"),
    ("API介绍/数据事件.html", "API-数据事件"),
    ("API介绍/行情数据查询函数（免费）.html", "API-行情数据查询函数"),
    ("API介绍/通用数据函数（免费）.html", "API-通用数据函数"),
    ("API介绍/股票财务数据及基础数据函数（免费）.html", "API-股票财务数据及基础数据函数"),
    ("API介绍/期货基础数据函数（免费）.html", "API-期货基础数据函数"),
    ("API介绍/股票增值数据函数（付费）.html", "API-股票增值数据函数"),
    ("API介绍/期货增值数据函数（付费）.html", "API-期货增值数据函数"),
    ("API介绍/基金增值数据函数（付费）.html", "API-基金增值数据函数"),
    ("API介绍/可转债增值数据函数（付费）.html", "API-可转债增值数据函数"),
    ("API介绍/交易函数.html", "API-交易函数"),
    ("API介绍/交易查询函数.html", "API-交易查询函数"),
    ("API介绍/两融交易函数.html", "API-两融交易函数"),
    ("API介绍/算法交易函数.html", "API-算法交易函数"),
    ("API介绍/新股新债交易函数.html", "API-新股新债交易函数"),
    ("API介绍/基金交易函数.html", "API-基金交易函数"),
    ("API介绍/债券交易函数.html", "API-债券交易函数"),
    ("API介绍/交易事件.html", "API-交易事件"),
    ("API介绍/动态参数.html", "API-动态参数"),
    ("API介绍/标的池.html", "API-标的池"),
    ("API介绍/其他函数.html", "API-其他函数"),
    ("API介绍/其他事件.html", "API-其他事件"),

    # 其他顶级页面
    ("枚举常量.html", "枚举常量"),
    ("错误码.html", "错误码"),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def fetch_page(url: str) -> str:
    """获取页面内容"""
    resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def extract_content(html: str) -> str:
    """
    提取正文内容，保持代码块完整
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 找主要内容区域
    content = soup.find('div', class_='content') or soup.find('article') or soup.find('main')
    if not content:
        content = soup.find('body')

    if not content:
        return html

    # 处理代码块：把 <pre> 和 <code> 标签内容保持完整
    for code_tag in content.find_all(['pre', 'code']):
        # 获取代码文本，保留原始格式
        code_text = code_tag.get_text()
        # 用特殊标记替换，避免被拆散
        code_tag.replace_with(f"\n```\n{code_text}\n```\n")

    # 处理表格
    for table in content.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(' | '.join(cells))
        if rows:
            table_text = '\n'.join(rows)
            table.replace_with(f"\n{table_text}\n")

    # 提取文本
    text = content.get_text(separator='\n', strip=True)

    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def crawl_docs(output_dir: str = "文档/掘金SDK文档"):
    """爬取所有文档"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"输出目录: {output_path.absolute()}")
    print(f"共 {len(PAGES)} 个页面")
    print()

    all_content = []

    for i, (page_path, name) in enumerate(PAGES, 1):
        # URL编码中文路径
        encoded_path = urllib.parse.quote(page_path, safe='/')
        url = BASE_URL + encoded_path

        print(f"[{i}/{len(PAGES)}] 正在抓取: {name}...")

        try:
            html = fetch_page(url)
            content = extract_content(html)

            # 保存单个文件
            file_path = output_path / f"{name}.txt"
            file_path.write_text(content, encoding='utf-8')

            # 汇总
            all_content.append(f"\n{'='*60}\n# {name}\n{'='*60}\n\n{content}")

            print(f"    保存: {file_path.name} ({len(content)} 字符)")

        except Exception as e:
            print(f"    [失败] {e}")

        # 间隔
        time.sleep(0.5)

    # 保存汇总文件
    all_file = output_path / "_全部文档汇总.txt"
    all_file.write_text('\n'.join(all_content), encoding='utf-8')
    print()
    print(f"汇总文件: {all_file}")
    print("完成!")


if __name__ == "__main__":
    crawl_docs()
