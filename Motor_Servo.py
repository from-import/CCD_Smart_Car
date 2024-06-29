from machine import *
import gc
import time


# 定义一个角度与占空比换算的函数
def duty_angle(angle):
    # 使用 300Hz 的舵机控制频率
    # pwm_servo_hz = 300
    return int(65535.0 / (1000.0 / 300) * (0.5 + angle / 90.0))


def set_servo_angle(pwm_servo, offset):
    """
    控制舵机的转动角度。

    参数:
    pwm_servo (PWM): 舵机实例。
    offset: 偏差值，由Get_CCD计算返回。
    """
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 偏差计算对应角度
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    # 转变为三次曲线
    if (offset > 0):
        nature = 1
    else:
        nature = 0
    a = 0.02
    b = 0.05
    c = 0.9
    offset = a * pow(abs(offset), 3) + b * pow(offset, 2) + c * abs(offset)
    if nature == 1:
        offset = -offset
        offset = offset * 16 / (a * pow(15, 3) + b * pow(15, 2) + c * pow(15, 1))
    else:
        offset = offset * 13 / (a * pow(15, 3) + b * pow(15, 2) + c * pow(15, 1))
    # 图像可接受误差（无限大时为64）15（max0ffset）——》(nature = 1,16;else,13)

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 舵机对应的任务
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    # （中值：101，左max值：117，右max值88）
    angle = 101
    angle = angle + offset

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 限幅保护
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    if angle > 117:
        angle = 117
    elif angle < 88:
        angle = 88

    # 获取舵机中值角度对应占空比
    duty_servo = duty_angle(angle)
    # 更新舵机PWM
    pwm_servo.duty_u16(duty_servo)

    gc.collect()
    return angle

# 案例
# set_servo_angle(90)
