# 本方法可以将CCD的值存储到数组中

from machine import *
from seekfree import TSL1401


def initialize_ccd(end_switch_pin='C19', capture_period=10, resolution=TSL1401.RES_12BIT):
    """
    初始化 CCD 并获取 CCD 数据。

    参数:
    end_switch_pin (str): 结束开关的引脚名称，默认为 'C19'。
    capture_period (int): 数据更新周期，调用多少次 capture/read 才更新一次数据，默认为 10。
    resolution (int): CCD 的采样精度，默认为 12bit。

    返回:
    tuple: 包含 CCD 数据1 和 CCD 数据2 的元组。
    """
    # 初始化拨码开关
    end_switch = Pin(end_switch_pin, Pin.IN, pull=Pin.PULL_UP_47K, value=True)
    end_state = end_switch.value()

    # 初始化 CCD 实例
    ccd = TSL1401(capture_period)
    ccd.set_resolution(resolution)

    # 获取 CCD 数据
    ccd_data1 = ccd.get(0)
    ccd_data2 = ccd.get(1)

    return ccd_data1, ccd_data2


# 调用函数案例
# ccd_data1, ccd_data2 = initialize_ccd()
# print(ccd_data1)
# print(ccd_data2)
