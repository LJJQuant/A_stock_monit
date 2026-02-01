# -*- coding: utf-8 -*-
"""
股票池仓库测试

运行方式:
    python -m tests.data.test_stock_pool        # 常规测试
    python -m tests.data.test_stock_pool init   # 初始化同步
"""

from dataclasses import asdict

from src.common.config import load_config
from src.data.source.juejin_client import JuejinClient
from src.data.repository.stock_pool import StockPoolRepository


def test_query(repo: StockPoolRepository):
    """测试查询功能"""
    print("\n=== 测试查询功能 ===")

    # 全部股票
    all_stocks = repo.get_all()
    print(f"  全部股票: {len(all_stocks)} 只")

    # 按板块统计
    for board in ["main", "gem", "star", "bse"]:
        stocks = repo.get_by_board(board)
        print(f"  {board}: {len(stocks)} 只")

    # 可交易股票
    tradable = repo.get_tradable()
    print(f"  可交易(排除ST和停牌): {len(tradable)} 只")

    # ST和停牌统计
    st_count = len([s for s in all_stocks if s.is_st])
    suspended_count = len([s for s in all_stocks if s.is_suspended])
    print(f"  ST股票: {st_count} 只")
    print(f"  停牌股票: {suspended_count} 只")

    # 显示几只样例（打印全部字段）
    if all_stocks:
        print("\n  样例股票:")
        for s in all_stocks[:3]:
            print(f"    {asdict(s)}")


def init_sync():
    """初始化同步股票池"""
    print("=" * 50)
    print("初始化同步股票池")
    print("=" * 50)

    config = load_config()
    client = JuejinClient(token=config.platform.juejin_token)
    repo = StockPoolRepository(config.database.stock_meta)

    # 获取全部A股
    print("\n从掘金获取股票池...")
    stocks = client.get_stock_pool()
    print(f"  获取到 {len(stocks)} 只股票")

    # 保存
    count = repo.save(stocks)
    print(f"  保存 {count} 条记录")

    # 验证
    test_query(repo)

    print("\n" + "=" * 50)
    print("初始化完成!")
    print("=" * 50)


def main():
    """常规测试"""
    print("=" * 50)
    print("股票池仓库测试")
    print("=" * 50)

    config = load_config()
    repo = StockPoolRepository(config.database.stock_meta)

    count = repo.count()
    print(f"\n  数据库中股票数: {count}")

    if count > 0:
        test_query(repo)
    else:
        print("  数据库为空，请先运行 init 初始化")

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_sync()
    else:
        main()
