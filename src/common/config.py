# -*- coding: utf-8 -*-
"""
配置读取器

从YAML文件加载配置到dataclass，提供类型安全的访问。
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PlatformConfig:
    """平台配置"""
    juejin_token: str
    dingtalk_webhook: str
    web_host: str
    web_port: int


@dataclass
class DatabaseConfig:
    """数据库配置"""
    daily_kline: Path
    stock_meta: Path
    realtime: Path
    backtest: Path

    def __post_init__(self) -> None:
        self.daily_kline = Path(self.daily_kline)
        self.stock_meta = Path(self.stock_meta)
        self.realtime = Path(self.realtime)
        self.backtest = Path(self.backtest)


@dataclass
class StockPoolConfig:
    """股票池配置"""
    markets: list[str]
    exclude_st: bool
    exclude_suspended: bool


@dataclass
class TradingHoursConfig:
    """交易时段配置"""
    morning_start: str
    morning_end: str
    afternoon_start: str
    afternoon_end: str


@dataclass
class TechnicalIndicatorsConfig:
    """技术指标参数"""
    kdj_n: int
    kdj_m1: int
    kdj_m2: int
    ma_periods: list[int]


@dataclass
class SpecialIndicatorsConfig:
    """特质指标参数"""
    chip_compare_yesterday: bool
    main_inflow_rate_min: float


@dataclass
class DailyDataConfig:
    """日常数据阈值"""
    turnover_rate_min: float
    turnover_rate_max: float
    turnover_ratio_min: float
    turnover_ratio_max: float
    turnover_ratio_threshold: float
    market_cap_min: float
    market_cap_max: float
    amount_min: float
    amount_max: float
    daily_gain_min: float
    daily_gain_max: float
    prev_days_gain_max: float
    prev_days_options: list[int]
    big_drop_threshold: float
    price_vwap_deviation_max: float


@dataclass
class ConditionsConfig:
    """预警条件配置"""
    kdj_j_threshold: float
    consecutive_j_lt_k_days: int
    consecutive_gain_lt_threshold_days: int
    consecutive_gain_threshold: float
    no_consecutive_yang_days: int
    big_drop_lookback_days: int
    upper_shadow_threshold: float
    upper_shadow_lookback_days: int
    price_high_lookback_days: int


@dataclass
class MetaConfig:
    """元信息"""
    generated_at: str
    version: str
    project: str


@dataclass
class AppConfig:
    """应用主配置"""
    platform: PlatformConfig
    database: DatabaseConfig
    stock_pool: StockPoolConfig
    trading_hours: TradingHoursConfig
    technical_indicators: TechnicalIndicatorsConfig
    special_indicators: SpecialIndicatorsConfig
    daily_data: DailyDataConfig
    conditions: ConditionsConfig
    meta: MetaConfig


def load_config(config_path: str | Path = "config/settings.yaml") -> AppConfig:
    """
    从YAML文件加载配置

    Parameters
    ----------
    config_path : str | Path
        配置文件路径

    Returns
    -------
    AppConfig
        应用配置对象

    Raises
    ------
    FileNotFoundError
        配置文件不存在
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    return AppConfig(
        platform=PlatformConfig(**data["platform"]),
        database=DatabaseConfig(**data["database"]),
        stock_pool=StockPoolConfig(**data["stock_pool"]),
        trading_hours=TradingHoursConfig(**data["trading_hours"]),
        technical_indicators=TechnicalIndicatorsConfig(**data["technical_indicators"]),
        special_indicators=SpecialIndicatorsConfig(**data["special_indicators"]),
        daily_data=DailyDataConfig(**data["daily_data"]),
        conditions=ConditionsConfig(**data["conditions"]),
        meta=MetaConfig(**data["meta"]),
    )
