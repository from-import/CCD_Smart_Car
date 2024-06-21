# 本方法可以将CCD的值存储到数组中

from machine import *
from seekfree import TSL1401


def read_ccd_data(ccd):
    """
    读取 CCD 数据。

    参数:
    ccd (TSL1401): 已初始化的 CCD 实例。

    返回:
    tuple: 包含 CCD 数据1 和 CCD 数据2。
    """
    ccd_data1 = ccd.get(0)
    ccd_data2 = ccd.get(1)
    return ccd_data1, ccd_data2


# 调用函数案例
# ccd_data1, ccd_data2 = read_ccd_data(ccd)
# print(ccd_data1)
# print(ccd_data2)
