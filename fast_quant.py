# -*- coding:utf-8 -*-
# @文件名  :fast_quant.py
# @时间    :2022/9/17 15:02
# @作者    :jie
# @目的

""" 以最小的代码成本进行on_bar式回测
    只能做多
    下单以下一个交易日开盘价成交
"""

import pandas as pd
import time
import random
import numpy as np

df = pd.read_csv('index_daily.csv')
df = df.iloc[::-1]
# 可以选择开始日期
df = df.iloc[6500:]

data = df.iloc[0].to_dict()


class Quant:
    def __init__(self):
        self._asset = None
        self.now_data = None
        self.account = None
        self.data = None
        self.next_data = None

        self.position = {}
        # 初始资金
        self.total = 100000
        self.cash = 100000
        self.locked = 0
        self.account = {'code': 0, 'total': 0,
                        'last_price': 0, 'quantity': 0}
        self.time = 0
        self.log_asset = []
        self.log_index = []
        self.time_list = []
        self.plot = True

    @property
    def asset(self):
        return {'total': round(self.total, 2), 'free': round(self.cash, 2), 'locked': round(self.locked, 2),
                'datetime': self.time}

    def load_data(self, data: pd.DataFrame):
        self.data = data
        return self

    def run(self):
        for i in range(len(self.data) - 1):
            _now_data = self.data.iloc[i].to_dict()
            self.time = _now_data['trade_date']
            self.next_data = self.data.iloc[i + 1].to_dict()
            self.now_data = _now_data
            self.on_bar(_now_data)
            self.account = {'code': self.account['code'], 'total': self.next_data['open'] * self.account['quantity'],
                            'last_price': self.next_data['open'], 'quantity': self.account['quantity']}
            self.locked = self.account['total']
            self.total = self.cash + self.locked
            self.log_asset.append(self.total)
            self.log_index.append(_now_data['close'])
            self.time_list.append(self.time)

        if not self.plot:
            return

        ret_log_index = []
        ret_log_asset = []
        _ret_index = 1
        _ret_asset = 1
        self.time_list = self.time_list[1:]
        self.time_list = [str(self.time_list[i]) for i in range(len(self.time_list))]
        for i in range(1, len(self.log_index)):
            _ret_index = _ret_index * (1 + (self.log_index[i] - self.log_index[i - 1]) / self.log_index[i - 1])
            ret_log_index.append(_ret_index)
            _ret_asset = _ret_asset * (1 + (self.log_asset[i] - self.log_asset[i - 1]) / self.log_asset[i - 1])
            ret_log_asset.append(_ret_asset)
        from matplotlib import pyplot as plt
        import matplotlib.ticker as ticker

        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        plt.xlabel('时间')
        plt.ylabel('收益净值')
        plt.plot(self.time_list, ret_log_index, label='index')
        plt.plot(self.time_list, ret_log_asset, label='asset')

        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(int(len(self.time_list) / 6)))
        plt.legend()
        plt.show()

    def create_order(self, quantity, direction='buy', code='000001.SH'):
        quantity = int(abs(quantity))
        if direction == 'buy':
            if self.cash < quantity * self.now_data['open']:
                print(f'现金不足：{self.cash}')
                return
            if code not in self.position:
                self.position[code] = quantity
            else:
                self.position[code] += quantity
        else:

            if code not in self.position:
                raise ValueError('not position')
            if self.position[code] < quantity:
                raise ValueError('error quantity')
            self.position[code] -= quantity
            access_cash = quantity * self.next_data['open']
            self.cash += access_cash
        if self.position[code] < 0.0001:
            self.position[code] = 0
        self.account = {'code': code, 'total': self.next_data['open'] * self.position[code],
                        'last_price': self.next_data['open'], 'quantity': self.position[code]}
        if direction == 'buy':
            self.cash -= quantity * self.next_data['open']

        self.locked = self.account['total']
        self.total = self.cash + self.locked

    def on_bar(self, data):
        raise NotImplementedError


class Strategy(Quant):
    def __init__(self):
        super(Strategy, self).__init__()
        self.ret = 0
        self.close_list = []

    def on_bar(self, data):
        # print(data)
        if random.random() > 0.5:
            self.create_order(10, 'buy')
        else:

            if not self.position or self.position[data['ts_code']] <= 0:
                return
            self.create_order(10, 'sell')

        print(self.asset)


def main():
    print('begin date:', data['trade_date'])
    print('1s later begin backtest..')
    time.sleep(1)
    Strategy().load_data(df).run()


if __name__ == '__main__':
    main()
