from machine import *
from seekfree import MOTOR_CONTROLLER
import gc
import time

def control_motor(duty, motor_side, motor_l, motor_r, led1):
    """
    控制指定的电机，并根据占空比值改变电机转速和方向。

    参数:
    duty (int): 电机的占空比值，范围为 ±10000。正数表示正转，负数表示反转。
    motor_side (str): 指定控制的电机，可以是 'left' 或 'right'。
    motor_l (MOTOR_CONTROLLER): 已初始化的左电机实例。
    motor_r (MOTOR_CONTROLLER): 已初始化的右电机实例。
    led1 (Pin): 已初始化的 LED 引脚实例。
    """
    # 限制 duty 在 -10000 到 10000 之间
    if duty > 10000:
        duty = 10000
    elif duty < -10000:
        duty = -10000

    if motor_side not in ['left', 'right']:
        raise ValueError("Motor side must be 'left' or 'right'.")

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
control_motor(2500, 'left', motor_l, motor_r, led1)  # 控制左电机，以占空比 2500 运行
time.sleep(2)  # 运行 2 秒
control_motor(-2500, 'right', motor_l, motor_r, led1)  # 控制右电机，以占空比 -2500 运行
"""
