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


def set_servo_angle(pwm_servo, offset,flag,ccd_data1):
    # global error_pre_last,error_pre
    """
    控制舵机的转动角度。
    参数:
    pwm_servo (PWM): 舵机实例。
    offset: 偏差值，由Get_CCD计算返回。
    """
    if (offset > 0):
        nature = 1
    else:
        nature = 0

    a = 0.02
    b = 0.06
    c = 4

    offset = a * pow(abs(offset), 3) + b * pow(offset, 2) + c * abs(offset)
    # 图像可接受误差（无限大时为64）23（max0ffset）——》(nature = 1,13;else,16)
    #注意，目前的三次函数认为5，10，17++为关键节点，17后打死
    if nature == 1:
        offset = -offset
        offset = offset * 14 / (a * pow(17, 3) + b * pow(17, 2) + c * pow(17, 1))
    else:
        offset = offset * 11 / (a * pow(17, 3) + b * pow(17, 2) + c * pow(17, 1))
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: PID调参(代码拷贝见7.4压缩包，此处为美观不展示)
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 舵机对应的任务
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    # （中值：101，左max值：112，右max值88）
    angle = 101
    angle = angle + offset

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 开环控制部分（Statu 总启动标志，0为停止）
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 限幅保护
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    if angle > 112:
        angle = 112
    elif angle < 87:
        angle = 87

    # 获取舵机中值角度对应占空比
    duty_servo = duty_angle(angle)
    # 更新舵机PWM
    pwm_servo.duty_u16(duty_servo)

    gc.collect()
    return angle



