
# 本示例程序演示如何使用 seekfree 库的 TSL1401 类接口
# 使用 RT1021-MicroPython 核心板搭配对应拓展学习板与 TSL1401 IPS200 模块测试

# 示例程序运行效果是实时在 IPS200 屏幕上显示 CCD 的采集图像

# CCD 的曝光计算方式
# CCD 通过 TSL1401(x) 初始化构建对象时 传入的 x 代表需要进行几次触发才会更新一次数据
# Ticker 通过 start(y) 启动时 y 代表 Ticker 的周期
# 此时每 y 毫秒会触发一次 CCD 的更新
# 当触发次数大于等于 x 时 CCD 才会更新一次数据
# 因此 CCD 的曝光时间等于 y * x 本例程中就是 10ms * 10 = 100ms

# 从 machine 库包含所有内容
from machine import *

# 从 smartcar 库包含 ticker
from smartcar import ticker

# 包含 display 库
from display import *

# 从 seekfree 库包含 TSL1401
from seekfree import TSL1401

# 包含 gc 类
import gc

def display_loop(lcd, ccd, pit1, end_switch, end_state, time_pit_handler):
    ticker_flag = False
    runtime_count = 0

    while True:
        if ticker_flag:
            ccd_data1 = ccd.get(0)
            ccd_data2 = ccd.get(1)
            lcd.wave(0, 0, 128, 64, ccd_data1, max=255)
            lcd.wave(0, 64, 128, 64, ccd_data2, max=255)
            ticker_flag = False
            runtime_count += 1
            print("runtime_count = {:>6d}.".format(runtime_count))
        if end_switch.value() != end_state:
            pit1.stop()
            print("Ticker stop.")
            break
        gc.collect()

"""
调用案例
display_loop(lcd, ccd, pit1, end_switch, end_state, time_pit_handler)
"""