from machine import *
from seekfree import BLDC_CONTROLLER
import gc
import time


def bldc_control(bldc1, bldc2, led1, key1, high_level_us=1100, dir=1):
    """
    控制无刷电机（BLDC）加减速转动。按下 D23 按键启动或暂停。

    参数:
    bldc1 (BLDC_CONTROLLER): 已初始化的 BLDC 控制器实例1。
    bldc2 (BLDC_CONTROLLER): 已初始化的 BLDC 控制器实例2。
    led1 (Pin): 已初始化的 LED 引脚实例。
    key1 (Pin): 已初始化的按键引脚实例。
    high_level_us (int): 初始高电平时间，默认为 1100。
    dir (int): 动作方向，默认为 1。
    """
    # 需要按一次按键启动
    print("Wait for KEY-D23 to be pressed.\r\n")
    while True:
        time.sleep_ms(100)
        led1.toggle()
        if 0 == key1.value():
            print("BLDC Controller test running.\r\n")
            print("Press KEY-D23 to suspend the program.\r\n")
            time.sleep_ms(300)
            break

    while True:
        time.sleep_ms(100)
        led1.toggle()
        # 往复计算 BLDC 电调速度
        if dir:
            high_level_us += 5
            if high_level_us >= 1250:
                dir = 0
        else:
            high_level_us -= 5
            if high_level_us <= 1100:
                dir = 1

        # 设置更新高电平时间输出
        bldc1.highlevel_us(high_level_us)
        bldc2.highlevel_us(high_level_us)

        if 0 == key1.value():
            print("Suspend.\r\n")
            print("Wait for KEY-D23 to be pressed.\r\n")
            bldc1.highlevel_us(1000)
            bldc2.highlevel_us(1000)
            time.sleep_ms(300)
            while True:
                if 0 == key1.value():
                    print("BLDC Controller test running.\r\n")
                    print("Press KEY-D23 to suspend the program.\r\n")
                    high_level_us = 1100
                    dir = 1
                    time.sleep_ms(300)
                    break

        gc.collect()


"""
# 示例调用
bldc_control(bldc1, bldc2, led1, key1)

"""
