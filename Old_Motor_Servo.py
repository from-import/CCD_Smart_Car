from machine import *
import gc
import time


#error_pre_last = 0
#error_pre = 0

# 定义一个角度与占空比换算的函数
def duty_angle(angle):
    # 使用 300Hz 的舵机控制频率
    # pwm_servo_hz = 300
    return int(65535.0 / (1000.0 / 300) * (0.5 + angle / 90.0))


# 通过 offset 计算 angle
def calculate_angle(offset):
    if offset > 0:
        nature = 1
    else:
        nature = 0

    a = 10.6015
    offset = abs(offset)
    if 0 <= offset < 5:
        offset = 1.6015 * offset
    elif 5 <= offset < 10:
        offset = 5.1015 * offset - 19.1986
    elif offset >= 10:
        offset = a * offset - 85.1935

    if nature == 1:
        offset = -offset
        offset = offset * 13 / (a * 17 - 85.1935)
    else:
        offset = offset * 11 / (a * 17 - 85.1935)

    angle = 101
    angle = angle + offset

    # 限幅保护
    if angle > 112:
        angle = 112
    elif angle < 88:
        angle = 88

    return angle


"""
set_servo_angle：控制舵机的转动角度。
Tips: 偏差计算对应角度(左负右正)

参数:
pwm_servo (PWM): 舵机实例。
offset: 偏差值，由Get_CCD计算返回。
flag：特殊标志位
"""

# （中值：101，左max值：112，右max值88）
middleAngel = 101
leftAngel = 112
rightAngel = 88


def set_servo_angle(pwm_servo, offset, flag):
    angle = calculate_angle(offset)

    if flag == "stop":
        angle = 101

    if flag == "isCircle":
        angle = 101  # 入环标志位，保持直线行驶

    if flag == "onCrossing":
        angle = 101

    if flag == "goLeftCircle":
        angle = 112

    if flag == "goRightCircle":
        angle = 88

    if flag == "outLeftCircle":
        angle = 112

    if flag == "outRightCircle":
        angle = 88

    duty_servo = duty_angle(angle)  # 获取舵机中值角度对应占空比
    pwm_servo.duty_u16(duty_servo)  # 更新舵机PWM
    gc.collect()
    return angle


