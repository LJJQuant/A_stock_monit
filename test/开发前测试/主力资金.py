# -*- coding: utf-8 -*-
"""
Created on Sat Jan 31 21:40:50 2026

@author: admin
"""

from __future__ import print_function, absolute_import
from gm.api import *

import time 

# 掘金终端需要打开，接口取数是通过网络请求的方式
# 设置token，可在用户-密钥管理里查看获取已有token ID
set_token('95ead097d57f944ee1415d5a040c578abf9f4dfc')

history_data = history(symbol='SHSE.000300', frequency='1d', start_time='2025-07-28', 
                        end_time='2026-01-30', fields='open, close, low, high, eob', 
                        adjust=ADJUST_PREV, df= True)

print( history_data)
 

df = stk_get_money_flow('SHSE.000002', trade_date=None)

# 查询行情快照
# while True:
    
#     t1 = time.time()
#     current_data = current(symbols='SZSE.000001')
#     t2 = time.time()
#     print(t2-t1)


# def init(context):
#     # 同时订阅600519的tick数据和分钟数据
#     subscribe(symbols='SHSE.600519', frequency='tick', count=2)
#     subscribe(symbols='SHSE.600519', frequency='60s', count=2)


# def on_tick(context,tick):
#     print('收到tick行情---', tick)


# def on_bar(context,bars):
#     print('收到bar行情---', bars)
#     data = context.data(symbol='SHSE.600519', frequency='60s', count=2)
#     print('bar数据滑窗---', data)
 