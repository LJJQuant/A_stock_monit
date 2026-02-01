# -*- coding: utf-8 -*-
"""
东方财富K线数据爬虫

获取历史K线数据。
"""

import httpx
from typing import List

from src.utils.symbol_utils import to_eastmoney_code


# 请求头
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Referer': 'http://quote.eastmoney.com/center/gridlist.html',
}

# K线类型映射
KLT_MAP = {
    'daily': '101',    # 日K
    'weekly': '102',   # 周K
    'monthly': '103',  # 月K
    '5min': '5',       # 5分钟
    '15min': '15',     # 15分钟
    '30min': '30',     # 30分钟
    '60min': '60',     # 60分钟
}


def get_kline(
    code: str,
    klt: str = 'daily',
    limit: int = 200,
    end_date: str = None,
) -> List[List]:
    """
    获取K线数据

    Parameters
    ----------
    code : str
        股票代码，如 '000001'
    klt : str
        K线类型: 'daily', 'weekly', 'monthly', '5min', '15min', '30min', '60min'
    limit : int
        获取条数，默认200
    end_date : str, optional
        结束日期，如 '20260129'，默认最新

    Returns
    -------
    List[List]
        K线数据，每行格式: [time, open, close, high, low, volume, amount, amplitude, turnover_rate]
    """
    secid = to_eastmoney_code(code)
    klt_code = KLT_MAP.get(klt, '101')

    params = {
        'secid': secid,
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': klt_code,
        'fqt': '1',  # 前复权
        'lmt': str(limit),
    }
    if end_date:
        params['end'] = end_date

    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'

    resp = httpx.get(url, params=params, headers=_HEADERS, timeout=10)
    data = resp.json()

    if not data.get('data') or not data['data'].get('klines'):
        return []

    # 解析K线数据
    result = []
    for line in data['data']['klines']:
        parts = line.split(',')
        # [time, open, close, high, low, volume, amount, amplitude, turnover_rate]
        row = [
            parts[0],                    # 时间
            float(parts[1]),             # 开盘价
            float(parts[2]),             # 收盘价
            float(parts[3]),             # 最高价
            float(parts[4]),             # 最低价
            float(parts[5]),             # 成交量
            float(parts[6]),             # 成交额
            float(parts[7]),             # 振幅
            float(parts[10]) if len(parts) > 10 else 0,  # 换手率
        ]
        result.append(row)

    return result
