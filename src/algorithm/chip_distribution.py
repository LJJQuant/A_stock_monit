# -*- coding: utf-8 -*-
"""
筹码分布计算算法

基于K线数据计算筹码分布、获利比例、集中度等指标。
"""

import math
from dataclasses import dataclass
from typing import List


@dataclass
class ChipResult:
    """筹码计算结果"""
    benefit_part: float       # 获利比例
    avg_cost: float           # 平均成本
    concentration_90: float   # 90%筹码集中度
    concentration_70: float   # 70%筹码集中度
    price_range_90: tuple     # 90%筹码价格范围 (low, high)
    price_range_70: tuple     # 70%筹码价格范围 (low, high)


def calculate_chip(
    kline: List[List],
    index: int = -1,
    accuracy_factor: int = 150,
    range_val: int = None,
) -> ChipResult:
    """
    计算筹码分布

    Parameters
    ----------
    kline : List[List]
        K线数据，每行格式: [time, open, close, high, low, volume, amount, amplitude, turnover_rate]
    index : int
        计算到哪根K线，默认-1（最后一根）
    accuracy_factor : int
        精度因子，默认150
    range_val : int, optional
        计算范围（往前多少根K线），默认全部

    Returns
    -------
    ChipResult
        筹码计算结果
    """
    if index < 0:
        index = len(kline) + index

    # 1. 确定计算范围
    start = 0
    if range_val:
        start = max(0, index - range_val + 1)
    calc_data = kline[start:index + 1]

    if len(calc_data) == 0:
        raise ValueError('K线数据为空')

    # 2. 计算价格范围
    max_price = calc_data[0][3]  # high
    min_price = calc_data[0][4]  # low
    for row in calc_data[1:]:
        max_price = max(max_price, row[3])
        min_price = min(min_price, row[4])

    # 3. 计算精度
    accuracy = max(0.01, (max_price - min_price) / (accuracy_factor - 1))

    # 4. 初始化筹码分布数组
    chips = [0.0] * accuracy_factor

    # 5. 遍历K线计算筹码分布
    for row in calc_data:
        open_p, close, high, low = row[1], row[2], row[3], row[4]
        turnover_rate = min(1, row[8] / 100) if len(row) > 8 else 0

        # 平均价格
        avg = (open_p + close + high + low) / 4

        # 价格索引
        h_idx = math.floor((high - min_price) / accuracy)
        l_idx = math.ceil((low - min_price) / accuracy)

        # G点坐标
        if high == low:
            g_point = [accuracy_factor - 1, math.floor((avg - min_price) / accuracy)]
        else:
            g_point = [2 / (high - low), math.floor((avg - min_price) / accuracy)]

        # 衰减历史筹码
        for n in range(len(chips)):
            chips[n] *= (1 - turnover_rate)

        # 三角分布计算
        if high == low:
            # 一字板：矩形分布
            if 0 <= g_point[1] < len(chips):
                chips[g_point[1]] += g_point[0] * turnover_rate / 2
        else:
            # 正常K线：三角分布
            for j in range(l_idx, h_idx + 1):
                if j >= len(chips) or j < 0:
                    continue
                cur_price = min_price + accuracy * j
                if cur_price <= avg:
                    if abs(avg - low) < 1e-8:
                        chips[j] += g_point[0] * turnover_rate
                    else:
                        chips[j] += (cur_price - low) / (avg - low) * g_point[0] * turnover_rate
                else:
                    if abs(high - avg) < 1e-8:
                        chips[j] += g_point[0] * turnover_rate
                    else:
                        chips[j] += (high - cur_price) / (high - avg) * g_point[0] * turnover_rate

    # 6. 计算总筹码
    total = sum(float(f"{c:.12g}") for c in chips)
    if total == 0:
        raise ValueError('筹码总量为0')

    # 7. 当前价格
    current_price = kline[index][2]

    # 8. 辅助函数：根据筹码量获取价格
    def get_cost_by_chip(chip_amount):
        s = 0.0
        for i in range(accuracy_factor):
            val = float(f"{chips[i]:.12g}")
            if s + val > chip_amount:
                return min_price + i * accuracy
            s += val
        return min_price + (accuracy_factor - 1) * accuracy

    # 9. 计算获利比例
    below = 0.0
    for i in range(accuracy_factor):
        val = float(f"{chips[i]:.12g}")
        if current_price >= min_price + i * accuracy:
            below += val
    benefit_part = below / total

    # 10. 计算百分比筹码
    def compute_percent(percent):
        ps = [(1 - percent) / 2, (1 + percent) / 2]
        pr = [get_cost_by_chip(total * ps[0]), get_cost_by_chip(total * ps[1])]
        if pr[0] + pr[1] == 0:
            concentration = 0
        else:
            concentration = (pr[1] - pr[0]) / (pr[0] + pr[1])
        return (round(pr[0], 2), round(pr[1], 2)), round(concentration, 6)

    range_90, conc_90 = compute_percent(0.9)
    range_70, conc_70 = compute_percent(0.7)

    # 11. 平均成本
    avg_cost = get_cost_by_chip(total * 0.5)

    return ChipResult(
        benefit_part=round(benefit_part, 6),
        avg_cost=round(avg_cost, 2),
        concentration_90=conc_90,
        concentration_70=conc_70,
        price_range_90=range_90,
        price_range_70=range_70,
    )
