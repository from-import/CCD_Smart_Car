from machine import *
from seekfree import BLDC_CONTROLLER
import gc
import time


def bldc_control():
    """
    初始化并控制无刷电机（BLDC）加减速转动。按下 D23 按键启动或暂停。
    """
    # 核心板上 C4 是 LED
    led1 = Pin('C4', Pin.OUT, pull=Pin.PULL_UP_47K, value=True)
    # 核心板上 D23 是按键
    key1 = Pin('D23', Pin.IN, pull=Pin.PULL_UP_47K, value=True)

    # 初始 1.1ms 高电平 确保能够起转
    high_level_us = 1100
    # 动作方向
    dir = 1

    # 学习板上 BLDC 电调接口为 B26/B27
    bldc1 = BLDC_CONTROLLER(BLDC_CONTROLLER.PWM_B26, freq=300, highlevel_us=1000)
    bldc2 = BLDC_CONTROLLER(BLDC_CONTROLLER.PWM_B27, freq=300, highlevel_us=1000)

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
bldc_control()

"""
