from machine import *
from seekfree import MOTOR_CONTROLLER
import gc
import time


def control_motor(duty, motor_side):
    """
    控制指定的电机，并根据占空比值改变电机转速和方向。

    参数:
    duty (int): 电机的占空比值，范围为 ±10000。正数表示正转，负数表示反转。
    motor_side (str): 指定控制的电机，可以是 'left' 或 'right'。
    """
    # 限制 duty 在 -10000 到 10000 之间
    if duty > 10000:
        duty = 10000
    elif duty < -10000:
        duty = -10000

    if motor_side not in ['left', 'right']:
        raise ValueError("Motor side must be 'left' or 'right'.")

    # 核心板上 C4 是 LED
    led1 = Pin('C4', Pin.OUT, pull=Pin.PULL_UP_47K, value=True)

    # 实例化 MOTOR_CONTROLLER 电机驱动模块
    motor_l = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C25_DIR_C27, 13000, duty=0, invert=True)
    motor_r = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C24_DIR_C26, 13000, duty=0, invert=False)

    # 设置 LED 状态，根据电机转速方向
    led1.value(duty < 0)

    # 控制指定的电机
    if motor_side == 'left':
        motor_l.duty(duty)
    elif motor_side == 'right':
        motor_r.duty(duty)

    gc.collect()


"""
# 示例调用

control_motor(2500, 'left')  # 控制左电机，以占空比 2500 运行
time.sleep(2)  # 运行 2 秒
control_motor(-2500, 'right')  # 控制右电机，以占空比 -2500 运行


"""
