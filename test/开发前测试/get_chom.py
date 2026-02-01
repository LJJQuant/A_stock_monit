# -*- coding: utf-8 -*-
# @Time     : 2026/1/27
# @File     : demo.py

from typing import List, Dict, Any
import requests
import math

def gen_eastmoney_code(rawcode: str) -> str:
    if rawcode[0] == '5':
        return f'1.{rawcode}'
    if rawcode[0] == '6':
        return f'1.{rawcode}'
    return f'0.{rawcode}'


def generate_cm_result(kdata: List[List], index: int, accuracy_factor: int = 150, range_val: int = None) -> Dict[
    str, Any]:
    """
    Args:
        kdata: K线数据 [time,open,close,high,low,volume,amount,amplitude,turnoverRate]
        index: 当前选中的K线索引
        accuracy_factor: 精度因子，默认150
        range_val: 默认为全部
    Returns:
        cm_result字典对象
    """

    # 1. 确定计算范围
    start = 0
    if range_val:
        start = max(0, index - range_val + 1)

    calc_kdata = kdata[start:index + 1]
    if len(calc_kdata) == 0:
        raise ValueError('invalid index')

    # 2. 计算最高价和最低价
    maxprice = 0
    minprice = 0
    for i, elements in enumerate(calc_kdata):
        high = elements[3]  # 最高价索引为3
        low = elements[4]  # 最低价索引为4

        if i == 0:
            maxprice = high
            minprice = low
        else:
            maxprice = max(maxprice, high)
            minprice = min(minprice, low)

    # 3. 计算精度
    factor = accuracy_factor
    accuracy = max(0.01, (maxprice - minprice) / (factor - 1))

    # 4. 生成价格区间
    yrange = []
    for i in range(factor):
        price = minprice + accuracy * i
        yrange.append(round(price, 2))

    # 5. 初始化筹码分布数组
    def create_number_array(count):
        return [0.0] * count

    xdata = create_number_array(factor)

    # 6. 核心计算：遍历K线进行筹码分布计算
    for i, eles in enumerate(calc_kdata):
        # 解析K线数据
        open_price = eles[1]
        close = eles[2]
        high = eles[3]
        low = eles[4]
        hsl = eles[8] if len(eles) > 8 else 0
        turnover_rate = min(1, hsl / 100)

        # 平均价格
        avg = (open_price + close + high + low) / 4

        # 价格索引
        H_index = math.floor((high - minprice) / accuracy)
        L_index = math.ceil((low - minprice) / accuracy)

        # G点坐标计算（关键参数）
        if high == low:
            # 一字板情况
            G_point = [factor - 1, math.floor((avg - minprice) / accuracy)]
        else:
            G_point = [2 / (high - low), math.floor((avg - minprice) / accuracy)]

        # 衰减处理（重要步骤）- 对历史筹码进行衰减
        for n in range(len(xdata)):
            xdata[n] *= (1 - turnover_rate)

        # 三角分布计算
        if high == low:
            # 一字板：矩形分布
            if 0 <= G_point[1] < len(xdata):
                xdata[G_point[1]] += G_point[0] * turnover_rate / 2
        else:
            # 正常K线：三角分布
            for j in range(L_index, H_index + 1):
                if j >= len(xdata) or j < 0:
                    continue

                curprice = minprice + accuracy * j
                if curprice <= avg:
                    # 上半三角
                    if abs(avg - low) < 1e-8:
                        xdata[j] += G_point[0] * turnover_rate
                    else:
                        xdata[j] += (curprice - low) / (avg - low) * G_point[0] * turnover_rate
                else:
                    # 下半三角
                    if abs(high - avg) < 1e-8:
                        xdata[j] += G_point[0] * turnover_rate
                    else:
                        xdata[j] += (high - curprice) / (high - avg) * G_point[0] * turnover_rate

    # 7. 计算总筹码量（使用高精度）
    total_chips = 0.0
    for i in range(factor):
        x_val_str = f"{xdata[i]:.12g}"
        x_val = float(x_val_str)
        total_chips += x_val

    # 8. 获取当前价格
    current_price = kdata[index][2]  # 收盘价

    # 9. 内部函数：根据筹码量获取价格
    def get_cost_by_chip(chip_amount):
        sum_chips = 0.0
        for i in range(factor):
            # 使用与上面相同的精度处理
            x_val_str = f"{xdata[i]:.12g}"
            x_val = float(x_val_str)
            if sum_chips + x_val > chip_amount:
                return minprice + i * accuracy
            sum_chips += x_val
        return minprice + (factor - 1) * accuracy

    # 10. 计算获利比例
    def get_benefit_part(price):
        below = 0.0
        for i in range(factor):
            x_val_str = f"{xdata[i]:.12g}"
            x_val = float(x_val_str)
            if price >= minprice + i * accuracy:
                below += x_val
        return below / total_chips if total_chips != 0 else 0

    # 11. 计算百分比筹码
    def compute_percent_chips(percent):
        if percent > 1 or percent < 0:
            raise ValueError('argument "percent" out of range')

        ps = [(1 - percent) / 2, (1 + percent) / 2]
        pr = [
            get_cost_by_chip(total_chips * ps[0]),
            get_cost_by_chip(total_chips * ps[1])
        ]

        if pr[0] + pr[1] == 0:
            concentration = 0
        else:
            concentration = (pr[1] - pr[0]) / (pr[0] + pr[1])

        return {
            'priceRange': [round(pr[0], 2), round(pr[1], 2)],
            'concentration': round(concentration, 6)
        }

    # 12. 计算平均成本
    avg_cost = get_cost_by_chip(total_chips * 0.5)

    # 13. 构建CYQData对象
    class CYQData:
        def __init__(self, x, y, benefit_part, avg_cost, percent_chips):
            self.x = x
            self.y = y
            self.benefitPart = benefit_part
            self.avgCost = avg_cost
            self.percentChips = percent_chips

    # 创建结果对象
    result = CYQData(
        x=xdata,
        y=yrange,
        benefit_part=round(get_benefit_part(current_price), 6),
        avg_cost=round(avg_cost, 2),
        percent_chips={
            '90': compute_percent_chips(0.9),
            '70': compute_percent_chips(0.7)
        }
    )

    # 转换为字典格式返回
    cm_result = {
        'x': result.x,
        'y': result.y,
        'benefitPart': result.benefitPart,
        'avgCost': result.avgCost,
        'percentChips': result.percentChips
    }

    return cm_result


def get_data():
    code = '605058'  # 股票代码
    secid = gen_eastmoney_code(code)
    ut = 'fa5fd1943c7b386f172d6893dbfba10b'  # 不用管
    klt = '101'        # 日k='101',周k='102'，月k='103'，5分钟='5'，15分钟='15'，30分钟='30'，60分钟='60'
    fqt = '1'
    end = '20260130'    # 数据结束日期
    lmt = '210'         # 获取数据的条数
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&ut={ut}&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt={klt}&fqt={fqt}&end={end}&lmt={lmt}'
    res = requests.get(url,headers=headers).json()
    # 创建模拟K线数据
    # 格式: [time,open,close,high,low,volume,amount,amplitude,turnoverRate]
    savelist = []
    for kn in range(0,len(res['data']['klines'])):
        kdata = []
        for i in res['data']['klines'][0:kn+1]:
            l = i.split(',')
            l = [l[0]] + [float(i1) for i1 in l[1:8]] + [float(l[10])]
            kdata.append(l)
        cm_result = generate_cm_result(kdata, index=len(kdata)-1, accuracy_factor=150, range_val=None)

        riqi = kdata[-1][0]
        hlbl = f"{cm_result['benefitPart'] * 100:.2f}%"
        pjcb = f"{cm_result['avgCost']:.2f}"
        # print('日期:', riqi)
        # print('获利比例:', hlbl)
        # print('平均成本:', pjcb)
        savestr = f'日期:{riqi}\n获利比例:{hlbl}\n平均成本:{pjcb}\n'
        for percent, data in cm_result['percentChips'].items():
            jgqj = f"{data['priceRange'][0]:.2f}-{data['priceRange'][1]:.2f}"
            jzd = f"{data['concentration'] * 100:.2f}%"
            # print(f"{percent}%成本:",jgqj,'集中度:',jzd)
            savestr += f'{percent}%成本:{jgqj}集中度:{jzd}\n'
        savestr += '-'*100
        print(savestr)
        savelist.append(savestr)
    # with open(f'{code}-日k.txt','w',encoding='utf-8')as f:
    #     f.write('\n'.join(savelist))



if __name__ == "__main__":
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer': 'http://quote.eastmoney.com/center/gridlist.html',
        'Connection':'close'
    }
    get_data()