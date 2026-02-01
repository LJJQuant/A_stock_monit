# -*- coding: utf-8 -*-
"""
股票代码处理工具

各平台股票代码格式转换。

格式说明：
- 纯数字: 600000, 000001
- 掘金格式: SHSE.600000, SZSE.000001
- 东方财富: 1.600000, 0.000001
"""


def to_juejin_symbol(code: str) -> str:
    """
    转换为掘金格式

    Parameters
    ----------
    code : str
        股票代码，如 '000001' 或 '600000'

    Returns
    -------
    str
        掘金格式，如 'SZSE.000001' 或 'SHSE.600000'

    Examples
    --------
    >>> to_juejin_symbol('600000')
    'SHSE.600000'
    >>> to_juejin_symbol('000001')
    'SZSE.000001'
    >>> to_juejin_symbol('300750')
    'SZSE.300750'
    """
    # 去掉可能的前缀
    if '.' in code:
        raw = code.split('.')[-1]
    else:
        raw = code

    # 确保6位
    raw = raw.zfill(6)

    # 6开头是上海，其他是深圳
    if raw.startswith('6'):
        return f'SHSE.{raw}'
    return f'SZSE.{raw}'


def from_juejin_symbol(symbol: str) -> str:
    """
    从掘金格式提取纯数字代码

    Parameters
    ----------
    symbol : str
        掘金格式，如 'SHSE.600000' 或 'SZSE.000001'

    Returns
    -------
    str
        纯数字代码，如 '600000' 或 '000001'

    Examples
    --------
    >>> from_juejin_symbol('SHSE.600000')
    '600000'
    >>> from_juejin_symbol('SZSE.000001')
    '000001'
    """
    if '.' in symbol:
        return symbol.split('.')[-1]
    return symbol


def to_eastmoney_code(code: str) -> str:
    """
    转换为东方财富格式

    Parameters
    ----------
    code : str
        股票代码，如 '000001' 或 '600000'

    Returns
    -------
    str
        东方财富格式，如 '0.000001' 或 '1.600000'

    Examples
    --------
    >>> to_eastmoney_code('000001')
    '0.000001'
    >>> to_eastmoney_code('600000')
    '1.600000'
    """
    # 去掉可能的后缀
    raw = code.split('.')[0]

    # 5/6开头是上海，其他是深圳
    if raw[0] in ('5', '6'):
        return f'1.{raw}'
    return f'0.{raw}'
