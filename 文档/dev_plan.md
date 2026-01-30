# A股量化预警系统开发计划

## 一、项目概述

### 1.1 项目目标
构建一套 **A股主板+创业板** 的量化预警系统，支持：
- **实时预警**：盘中实时监控，满足条件即推送飞书 + Web展示
- **历史回测**：基于30分钟K线验证策略有效性

### 1.2 策略范围
- 股票池：主板（沪深） + 创业板，约4500只
- 预警条件：20个技术/资金/形态条件（详见 `stra.md`）
- 涨跌停规则：主板10%，创业板20%

### 1.3 数据来源
| 数据类型 | 来源 | 用途 |
|----------|------|------|
| 历史日线 | 掘金量化 | 实时预警基础数据 |
| 实时行情 | 掘金量化（推送） | 盘中实时计算 |
| 30分钟K线 | 掘金量化 | 回测 + 尾盘指标 |
| 筹码集中度 | 爬虫（同花顺） | 条件18 |
| 主力净流入 | 爬虫（同花顺） | 条件19 |

---

## 二、技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | 类型注解、性能优化 |
| 数据库 | DuckDB | 列式存储、向量化查询 |
| 数据处理 | Pandas + NumPy | 向量化计算 |
| 行情接口 | 掘金量化SDK | 历史下载 + 实时推送 |
| 爬虫 | httpx + parsel | 异步爬取 |
| Web框架 | FastAPI | 预警API + Web界面后端 |
| 推送 | 飞书机器人 | Webhook推送 |
| 配置管理 | dataclass + YAML | 类型安全的配置 |

---

## 三、系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          数据源层                                │
├──────────────────────────┬──────────────────────────────────────┤
│      掘金量化 SDK        │              爬虫模块                 │
│  • 历史日线/30分钟下载   │  • 筹码集中度（T+1落库）              │
│  • 实时Tick推送          │  • 主力净流入（T+1落库）              │
└───────────┬──────────────┴──────────────┬───────────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据存储层                                │
├─────────────────────────────┬───────────────────────────────────┤
│     realtime.duckdb         │        backtest.duckdb            │
│  • daily_kline（日线）      │  • kline_30min（30分钟线）         │
│  • chip_concentration       │                                   │
│  • capital_flow             │                                   │
│  • stock_pool（股票池）     │                                   │
└───────────┬─────────────────┴───────────────┬───────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        计算引擎层                                │
│  ┌─────────────────────┐      ┌─────────────────────────────┐   │
│  │   indicators.py     │      │      conditions.py          │   │
│  │  • KDJ计算          │ ──▶  │  • 20个条件向量化判断       │   │
│  │  • MA5/20/60        │      │  • 支持realtime/backtest    │   │
│  │  • VWAP             │      │    两种模式                 │   │
│  └─────────────────────┘      └─────────────────────────────┘   │
└───────────┬─────────────────────────────────┬───────────────────┘
            │                                  │
            ▼                                  ▼
┌───────────────────────────┐    ┌────────────────────────────────┐
│      实时预警引擎          │    │         回测引擎               │
│  • 订阅实时行情            │    │  • 按日期范围回测              │
│  • 条件触发检测            │    │  • 统计命中率/收益             │
│  • 飞书推送 + Web API      │    │  • 生成回测报告                │
└───────────────────────────┘    └────────────────────────────────┘
```

---

## 四、目录结构

```
A_stock_monit/
├── src/
│   ├── common/                     # 公共模块
│   │   ├── __init__.py
│   │   ├── config.py               # 配置管理（dataclass + YAML）
│   │   ├── models.py               # 数据模型（TypedDict/dataclass）
│   │   ├── db.py                   # DuckDB连接管理
│   │   ├── indicators.py           # 技术指标计算
│   │   └── constants.py            # 常量定义
│   │
│   ├── realtime/                   # 实时预警模块
│   │   ├── __init__.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── juejin_client.py    # 掘金SDK封装
│   │   │   ├── daily_repo.py       # 日线数据仓库
│   │   │   └── crawler/
│   │   │       ├── __init__.py
│   │   │       ├── base.py         # 爬虫基类
│   │   │       ├── chip.py         # 筹码集中度爬虫
│   │   │       └── capital.py      # 主力资金爬虫
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── conditions.py       # 20个预警条件
│   │   │   ├── signal_engine.py    # 信号计算引擎
│   │   │   └── monitor.py          # 实时监控主循环
│   │   └── alert/
│   │       ├── __init__.py
│   │       ├── feishu.py           # 飞书推送
│   │       └── api.py              # FastAPI接口
│   │
│   ├── backtest/                   # 回测模块
│   │   ├── __init__.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   └── kline_30min_repo.py # 30分钟K线仓库
│   │   └── engine/
│   │       ├── __init__.py
│   │       ├── backtest_engine.py  # 回测引擎
│   │       └── statistics.py       # 统计分析
│   │
│   └── web/                        # Web界面（Phase 5）
│       └── ...
│
├── data/
│   ├── realtime.duckdb             # 实时预警数据库
│   └── backtest.duckdb             # 回测数据库
│
├── config/
│   ├── settings.yaml               # 主配置文件
│   └── settings.example.yaml       # 配置示例
│
├── scripts/
│   ├── init_db.py                  # 初始化数据库
│   ├── download_history.py         # 下载历史数据
│   └── run_crawler.py              # 运行爬虫
│
├── tests/
│   ├── test_indicators.py
│   ├── test_conditions.py
│   └── ...
│
├── 文档/
│   ├── stra.md                     # 策略文档
│   └── dev_plan.md                 # 开发计划
│
├── CLAUDE.md                       # AI协作规范
├── requirements.txt
└── pyproject.toml
```

---

## 五、数据库设计

### 5.1 realtime.duckdb

#### 表：stock_pool（股票池）
```sql
CREATE TABLE stock_pool (
    symbol VARCHAR PRIMARY KEY,      -- 股票代码 如 '000001.SZ'
    name VARCHAR,                    -- 股票名称
    market VARCHAR,                  -- 'main'主板 / 'gem'创业板
    list_date DATE,                  -- 上市日期
    is_active BOOLEAN DEFAULT TRUE   -- 是否活跃（非ST、非停牌）
);
```

#### 表：daily_kline（日线数据）
```sql
CREATE TABLE daily_kline (
    symbol VARCHAR,
    trade_date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,                   -- 成交量（股）
    amount DOUBLE,                   -- 成交额（元）
    turnover_rate DOUBLE,            -- 换手率 %
    circulating_market_cap DOUBLE,   -- 流通市值（元）
    PRIMARY KEY (symbol, trade_date)
);
```

#### 表：chip_concentration（筹码集中度）
```sql
CREATE TABLE chip_concentration (
    symbol VARCHAR,
    trade_date DATE,
    concentration DOUBLE,            -- 筹码集中度
    profit_ratio DOUBLE,             -- 获利比例（条件8，后续用）
    updated_at TIMESTAMP,
    PRIMARY KEY (symbol, trade_date)
);
```

#### 表：capital_flow（主力资金）
```sql
CREATE TABLE capital_flow (
    symbol VARCHAR,
    trade_date DATE,
    main_net_inflow DOUBLE,          -- 主力净流入（元）
    main_net_inflow_rate DOUBLE,     -- 主力净流入占比 %（条件19）
    updated_at TIMESTAMP,
    PRIMARY KEY (symbol, trade_date)
);
```

### 5.2 backtest.duckdb

#### 表：kline_30min（30分钟K线）
```sql
CREATE TABLE kline_30min (
    symbol VARCHAR,
    datetime TIMESTAMP,              -- K线时间 如 2024-01-02 10:00:00
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    amount DOUBLE,                   -- 成交额（条件20核心字段）
    PRIMARY KEY (symbol, datetime)
);
```

---

## 六、分阶段开发计划

### Phase 1：基础设施搭建

**目标**：完成项目骨架、配置管理、数据库初始化

#### 任务清单
| 编号 | 任务 | 产出 |
|------|------|------|
| 1.1 | 创建项目目录结构 | 目录 + `__init__.py` |
| 1.2 | 配置管理模块 | `config.py` + `settings.yaml` |
| 1.3 | 数据模型定义 | `models.py`（KLine, Stock等） |
| 1.4 | DuckDB连接管理 | `db.py` |
| 1.5 | 数据库初始化脚本 | `scripts/init_db.py` |
| 1.6 | 常量定义 | `constants.py`（交易时段等） |

#### 关键代码设计

**config.py 示例结构**
```python
@dataclass
class JuejinConfig:
    token: str
    account_id: str

@dataclass
class DatabaseConfig:
    realtime_path: Path
    backtest_path: Path

@dataclass
class AlertConfig:
    feishu_webhook: str

@dataclass
class AppConfig:
    juejin: JuejinConfig
    database: DatabaseConfig
    alert: AlertConfig
```

---

### Phase 2：数据层开发

**目标**：完成掘金SDK对接、历史数据下载、股票池管理

#### 任务清单
| 编号 | 任务 | 产出 |
|------|------|------|
| 2.1 | 掘金SDK封装 | `juejin_client.py` |
| 2.2 | 股票池获取（主板+创业板筛选） | 股票池初始化逻辑 |
| 2.3 | 日线数据下载 | `download_history.py` |
| 2.4 | 日线数据仓库 | `daily_repo.py`（CRUD操作） |
| 2.5 | 30分钟K线下载 | 扩展下载脚本 |
| 2.6 | 30分钟数据仓库 | `kline_30min_repo.py` |

#### 接口设计

**JuejinClient**
```python
class JuejinClient:
    def get_stock_pool(self, market: list[str]) -> list[Stock]: ...
    def get_daily_kline(self, symbols: list[str], start: date, end: date) -> pd.DataFrame: ...
    def get_kline_30min(self, symbols: list[str], start: date, end: date) -> pd.DataFrame: ...
    def subscribe_realtime(self, symbols: list[str], callback: Callable): ...
```

**DailyRepo**
```python
class DailyRepo:
    def upsert_batch(self, df: pd.DataFrame) -> int: ...
    def get_recent_n_days(self, symbols: list[str], n: int) -> pd.DataFrame: ...
    def get_by_date_range(self, symbols: list[str], start: date, end: date) -> pd.DataFrame: ...
```

---

### Phase 3：指标与条件计算

**目标**：实现技术指标计算、20个预警条件的向量化实现

#### 任务清单
| 编号 | 任务 | 产出 |
|------|------|------|
| 3.1 | KDJ指标计算 | `indicators.py` |
| 3.2 | MA均线计算 | `indicators.py` |
| 3.3 | VWAP计算 | `indicators.py` |
| 3.4 | 条件1-2（KDJ相关） | `conditions.py` |
| 3.5 | 条件3-5（换手率相关） | `conditions.py` |
| 3.6 | 条件6-7（市值/成交额） | `conditions.py` |
| 3.7 | 条件9-10（涨幅相关） | `conditions.py` |
| 3.8 | 条件11-13（价格/均线） | `conditions.py` |
| 3.9 | 条件14-17（K线形态） | `conditions.py` |
| 3.10 | 条件20（尾盘30分钟） | `conditions.py` |
| 3.11 | 信号引擎整合 | `signal_engine.py` |

#### 条件实现规范

每个条件实现为独立函数，返回布尔Series：
```python
def check_kdj_j_condition(df: pd.DataFrame) -> pd.Series:
    """
    条件1: KDJ J值 < 98 且 今日J > 昨日J

    Parameters
    ----------
    df : pd.DataFrame
        包含 j_value 列的DataFrame，index为symbol

    Returns
    -------
    pd.Series[bool]
        每只股票是否满足条件
    """
    ...
```

#### 信号引擎设计
```python
class SignalEngine:
    def __init__(self, config: ConditionConfig):
        self.config = config

    def calculate(
        self,
        daily_data: pd.DataFrame,
        current_price: pd.Series,
        mode: Literal["realtime", "backtest"]
    ) -> pd.DataFrame:
        """
        计算所有条件，返回每只股票每个条件的满足情况

        Returns
        -------
        pd.DataFrame
            columns: [symbol, cond_1, cond_2, ..., cond_20, all_passed]
        """
        ...
```

---

### Phase 4：爬虫模块

**目标**：实现筹码集中度、主力资金的爬取与落库

#### 任务清单
| 编号 | 任务 | 产出 |
|------|------|------|
| 4.1 | 爬虫基类设计 | `crawler/base.py` |
| 4.2 | 筹码集中度爬虫 | `crawler/chip.py` |
| 4.3 | 主力资金爬虫 | `crawler/capital.py` |
| 4.4 | 爬虫调度脚本 | `scripts/run_crawler.py` |
| 4.5 | 条件18-19实现 | 更新 `conditions.py` |

#### 爬虫设计
```python
class BaseCrawler(ABC):
    def __init__(self, config: CrawlerConfig):
        self.client = httpx.AsyncClient(...)
        self.retry_times = 3

    @abstractmethod
    async def fetch(self, symbol: str) -> dict: ...

    async def fetch_batch(self, symbols: list[str]) -> pd.DataFrame:
        """带重试和限速的批量爬取"""
        ...
```

---

### Phase 5：实时预警引擎

**目标**：实现盘中实时监控、条件触发、飞书推送

#### 任务清单
| 编号 | 任务 | 产出 |
|------|------|------|
| 5.1 | 实时监控主循环 | `monitor.py` |
| 5.2 | 飞书推送模块 | `alert/feishu.py` |
| 5.3 | FastAPI接口 | `alert/api.py` |
| 5.4 | 尾盘30分钟实时累计 | 更新监控逻辑 |
| 5.5 | 预警去重（同一股票不重复推送） | 状态管理 |

#### 监控引擎设计
```python
class RealtimeMonitor:
    def __init__(
        self,
        juejin_client: JuejinClient,
        signal_engine: SignalEngine,
        alerter: FeishuAlerter
    ):
        ...

    async def start(self):
        """启动实时监控"""
        # 1. 加载历史数据到内存
        # 2. 订阅实时行情
        # 3. 每次行情更新时计算条件
        # 4. 满足条件则推送
        ...

    def on_tick(self, tick: TickData):
        """行情回调"""
        ...
```

---

### Phase 6：回测引擎

**目标**：基于历史数据验证策略效果

#### 任务清单
| 编号 | 任务 | 产出 |
|------|------|------|
| 6.1 | 回测引擎核心 | `backtest_engine.py` |
| 6.2 | 统计指标计算 | `statistics.py` |
| 6.3 | 回测报告生成 | 输出格式设计 |

#### 回测引擎设计
```python
class BacktestEngine:
    def __init__(
        self,
        daily_repo: DailyRepo,
        kline_30min_repo: Kline30minRepo,
        signal_engine: SignalEngine
    ):
        ...

    def run(
        self,
        start_date: date,
        end_date: date,
        symbols: list[str] | None = None
    ) -> BacktestResult:
        """
        执行回测

        Returns
        -------
        BacktestResult
            包含每日命中股票、统计指标等
        """
        ...
```

---

### Phase 7：Web界面

**目标**：提供预警展示、历史查询的Web界面

#### 任务清单
| 编号 | 任务 | 产出 |
|------|------|------|
| 7.1 | 前端技术选型 | Vue/React + 图表库 |
| 7.2 | 实时预警展示页 | 当日预警列表 |
| 7.3 | 历史预警查询 | 按日期/股票查询 |
| 7.4 | 回测结果展示 | 统计图表 |

---

## 七、20个条件实现细节

| 条件 | 描述 | 数据依赖 | 计算要点 |
|------|------|----------|----------|
| 1 | J < 98 且 今日J > 昨日J | 日线OHLC | KDJ计算，shift(1)比较 |
| 2 | 连续3天 J < K | 日线OHLC | rolling(3).all() |
| 3 | 今日换手率/昨日换手率 ∈ [1.28, 12] | 日线换手率 | 向量除法 |
| 4 | 当日换手率 ∈ [3.28%, 25.8%] | 日线换手率 | 区间判断 |
| 5 | 隔日换手率 > 昨日 或 > 2.5 | 日线换手率 | 满足其一 |
| 6 | 流通市值 ∈ [16亿, 500亿] | 日线流通市值 | 区间判断 |
| 7 | 成交额 ∈ [1.68亿, 36.68亿] | 日线成交额 | 区间判断 |
| 8 | 获利筹码 > 78% | 爬虫 | **后续实现** |
| 9 | 前6或7天涨幅 < 11% | 日线收盘价 | (close / close.shift(6or7) - 1) |
| 10 | 当日涨幅 ∈ [4%, 9.5%] | 实时/收盘价 | 当日涨幅计算 |
| 11 | 当前价/均价 < 4% | 实时价 + VWAP | VWAP = amount / volume |
| 12 | 当前价 = 10日最高 | 实时价 + 历史high | rolling(10).max() |
| 13 | 价格>MA60, MA5>MA20, MA5>MA60 | 日线收盘价 | 三条均线计算 |
| 14 | 连续5日涨幅均 < 9.5% | 日线收盘价 | rolling判断 |
| 15 | 不能出现4连阳 | 日线OHLC | close > open 连续判断 |
| 16 | 10日内无大跌 > -8% | 日线OC | (close/open - 1) > -8% |
| 17 | 前2日无 > 4%上影阳线 | 日线OHLC | 上影线计算 |
| 18 | 筹码集中度 > 昨日 | 爬虫 | shift(1)比较 |
| 19 | 当日增仓比例 > 6% | 爬虫 | 直接判断 |
| 20 | 尾盘30分钟满足其一 | 30分钟成交额 | 14:00-14:30 vs 14:30-15:00 |

### 条件20详细逻辑

```
设 A = 14:00-14:30 成交额
设 B = 14:30-15:00 成交额
倍数 = B / A

满足以下任一：
- 倍数 >= 1.0 且 B >= 2000万
- 倍数 >= 0.7 且 B >= 8000万
- 倍数 >= 0.8 且 B >= 6.6亿
- 倍数 >= 0.9 且 B >= 4000万
```

---

## 八、配置文件示例

### settings.yaml
```yaml
juejin:
  token: "your_token_here"
  account_id: "your_account_id"

database:
  realtime_path: "./data/realtime.duckdb"
  backtest_path: "./data/backtest.duckdb"

stock_pool:
  markets: ["main", "gem"]  # 主板 + 创业板
  exclude_st: true
  exclude_suspended: true

alert:
  feishu_webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"

trading_hours:
  morning_start: "09:30"
  morning_end: "11:30"
  afternoon_start: "13:00"
  afternoon_end: "15:00"

conditions:
  # 各条件阈值（可调参）
  kdj_j_threshold: 98
  turnover_rate_min: 3.28
  turnover_rate_max: 25.8
  market_cap_min: 1600000000   # 16亿
  market_cap_max: 50000000000  # 500亿
  # ... 其他参数
```

---

## 九、开发优先级

```
Phase 1 (基础设施)
    │
    ▼
Phase 2 (数据层) ─────────┐
    │                     │
    ▼                     ▼
Phase 3 (指标/条件)    Phase 4 (爬虫)
    │                     │
    └──────────┬──────────┘
               │
               ▼
         Phase 5 (实时预警)
               │
               ▼
         Phase 6 (回测)
               │
               ▼
         Phase 7 (Web界面)
```

**建议执行顺序**：
1. Phase 1 → 2 → 3 先跑通核心流程（不含爬虫条件）
2. Phase 4 并行开发爬虫
3. Phase 5 实现实时预警
4. Phase 6 回测验证
5. Phase 7 Web界面收尾

---

## 十、风险与注意事项

1. **掘金接口限制**：注意API调用频率，批量下载需控制并发
2. **爬虫反爬**：同花顺可能有反爬机制，需要代理池或降速
3. **数据一致性**：确保日线和30分钟数据的时间对齐
4. **内存管理**：全市场批量计算时注意内存占用
5. **时区处理**：统一使用北京时间，避免时区混乱
