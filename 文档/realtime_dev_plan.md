# A股预警系统 - 实时开发计划

> **当前阶段**: Phase 2 数据层
> **当前任务**: 2.1 类型定义 + 异常

---

## Phase 1: 基础设施 ✅

| 步骤 | 任务 | 产出 | 状态 |
|------|------|------|------|
| 1.1 | 目录结构 + 依赖 | 目录 + requirements.txt | ✅ 完成 |
| 1.2 | 配置管理 | config_schema.py + config_generator.py + config.py + settings.yaml | ✅ 完成 |
| 1.3 | 常量定义 | constants.py | ✅ 完成 |
| 1.4 | 数据库管理 | db.py + 4个duckdb文件创建 | ✅ 完成 |

**产出文件**:
- `src/common/config_schema.py` - 配置Schema定义
- `src/common/config_generator.py` - 配置生成器
- `src/common/config.py` - 配置读取器
- `src/common/constants.py` - 常量定义
- `src/common/db.py` - 数据库连接管理
- `config/settings.yaml` - 配置文件
- `data/duckdb/*.duckdb` - 4个数据库文件

---

## Phase 2: 数据层 (进行中)

### 目录结构

```
src/data/                          # 数据层
├── __init__.py
├── types.py                       # 类型定义（StockInfo, TradingDay等）
│
├── source/                        # 数据源适配层
│   ├── __init__.py
│   ├── juejin_client.py           # 掘金SDK封装
│   └── exceptions.py              # 异常定义
│
├── repository/                    # 数据仓库层（DuckDB读写）
│   ├── __init__.py
│   ├── base.py                    # 基础仓库类
│   ├── trading_calendar.py        # 交易日历仓库
│   ├── stock_pool.py              # 股票池仓库
│   └── kline.py                   # K线数据仓库
│
└── service/                       # 数据服务层
    ├── __init__.py
    ├── sync_service.py            # 数据同步服务（增量更新）
    └── data_reader.py             # 高性能数据读取器
```

### 实现步骤

| 步骤 | 任务 | 产出文件 | 状态 |
|------|------|----------|------|
| 2.1 | 类型定义 + 异常 | `types.py`, `source/exceptions.py` | - |
| 2.2 | 掘金客户端封装 | `source/juejin_client.py` | - |
| 2.3 | 交易日历仓库 | `repository/trading_calendar.py` | - |
| 2.4 | 股票池仓库 | `repository/stock_pool.py` | - |
| 2.5 | K线仓库 | `repository/kline.py` | - |
| 2.6 | 同步服务 | `service/sync_service.py` | - |
| 2.7 | 数据读取器 | `service/data_reader.py` | - |
| 2.8 | 测试 + 配置更新 | `tests/data/`, 配置schema | - |

### 核心设计

#### 2.1 类型定义

```python
@dataclass(frozen=True, slots=True)
class StockInfo:
    """股票信息（不可变）"""
    symbol: str       # SHSE.600000
    code: str         # 600000
    exchange: str     # SHSE / SZSE
    name: str         # 证券名称
    board: str        # main / gem
    is_st: bool
    is_suspended: bool

@dataclass(frozen=True, slots=True)
class TradingDay:
    """交易日信息"""
    date: date
    is_trading_day: bool
    prev_trading_day: date | None
    next_trading_day: date | None
```

#### 2.2 掘金客户端

功能：
- 懒加载认证（首次调用时 `set_token()`）
- 指数退避重试（失败自动重试3次）
- 分批请求（每批200只股票，避免超时）
- 统一异常处理

```python
class JuejinClient:
    def get_stock_pool(boards: list[str]) -> list[StockInfo]
    def get_trading_calendar(exchange, start_year, end_year) -> list[TradingDay]
    def get_kline(symbols, start_date, end_date, adjust='post') -> Iterator[DataFrame]
```

#### 2.3 数据表结构

**交易日历表** (`stock_meta.duckdb`)
```sql
CREATE TABLE trading_calendar (
    exchange VARCHAR,
    date DATE,
    is_trading_day BOOLEAN,
    prev_trading_day DATE,
    next_trading_day DATE,
    PRIMARY KEY (exchange, date)
);
```

**股票池表** (`stock_meta.duckdb`)
```sql
CREATE TABLE stock_pool (
    symbol VARCHAR PRIMARY KEY,
    code VARCHAR,
    exchange VARCHAR,
    name VARCHAR,
    board VARCHAR,           -- main / gem
    is_st BOOLEAN,
    is_suspended BOOLEAN,
    updated_at TIMESTAMP
);
```

**K线表** (`daily_kline.duckdb`)
```sql
CREATE TABLE daily_kline (
    symbol VARCHAR,
    date DATE,
    open DOUBLE,             -- 后复权价
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    amount DOUBLE,
    adj_factor DOUBLE,       -- 复权因子
    PRIMARY KEY (symbol, date)
);
CREATE INDEX idx_kline_date ON daily_kline(date);
```

#### 2.4 增量更新策略

```
1. 同步交易日历
   └─ 检查本地是否缺失当年数据，缺则下载

2. 同步股票池
   └─ 每日更新（ST/停牌状态可能变化）

3. 同步K线（增量）
   a. 查询每只股票本地最新日期
   b. 计算缺失的交易日（与交易日历对比）
   c. 只下载缺失日期的数据
   d. 批量写入 DuckDB

4. 并发优化
   └─ 线程池并发下载（默认4线程）
```

#### 2.5 数据读取器

功能：
- 懒加载：只在需要时从DuckDB读取
- LRU缓存：热点数据内存缓存（可选）
- 列式读取：只读取需要的列，减少IO

```python
class DataReader:
    def get_kline(symbols, start_date, end_date, columns, use_cache) -> DataFrame
    def get_stock_pool(use_cache) -> list[StockInfo]
    def get_trading_days(start_date, end_date) -> list[date]
    def clear_cache()
```

### 配置扩展

需要在 `config_schema.py` 添加：

```python
DATA_SYNC_SCHEMA = {
    'juejin_token': ('', '掘金量化Token'),
    'sync_start_year': (2020, '历史数据起始年份'),
    'sync_max_workers': (4, '同步并发线程数'),
    'cache_enabled': (True, '是否启用内存缓存'),
    'cache_max_size': (100, '缓存最大条目数'),
    'cache_ttl_seconds': (3600, '缓存过期时间(秒)'),
}
```

---

## 后续阶段概览

| Phase | 模块 | 状态 |
|-------|------|------|
| 1 | 基础设施 | ✅ 完成 |
| 2 | 数据层 | 进行中 |
| 3 | 指标计算 | - |
| 4 | 爬虫（筹码/资金流） | 部分完成 |
| 5 | 预警引擎 | - |
| 6 | 回测 | - |
| 7 | Web界面 | - |
