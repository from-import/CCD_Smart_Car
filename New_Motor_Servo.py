from machine import *
import gc
import time


# 定义一个角度与占空比换算的函数
def duty_angle(angle):
    # 使用 300Hz 的舵机控制频率
    # pwm_servo_hz = 300
    return int(65535.0 / (1000.0 / 300) * (0.5 + angle / 90.0))


"""
控制舵机的转动角度。
Tips: 偏差计算对应角度(左负右正)

参数:
pwm_servo (PWM): 舵机实例。
offset: 偏差值，由Get_CCD计算返回。
"""


def set_servo_angle(pwm_servo, offset, flag):
    # 常量定义
    ANGLE_MID = 101
    ANGLE_LEFT_MAX = 117
    ANGLE_RIGHT_MAX = 88
    MAX_OFFSET = 15
    SEGMENT_A = 11.6015
    SEGMENT_B1 = 1.6015
    SEGMENT_B2 = 5.1015
    SEGMENT_C1 = -19.1986
    SEGMENT_C2 = -85.1935
    SCALE_LEFT = 16
    SCALE_RIGHT = 13
    OFFSET_SCALE = SEGMENT_A * 17 + SEGMENT_C2

    def apply_segment_function(offset):
        if 0 <= offset < 5:
            return SEGMENT_B1 * offset
        elif 5 <= offset < 10:
            return SEGMENT_B2 * offset + SEGMENT_C1
        else:
            return SEGMENT_A * offset + SEGMENT_C2

    # 判断 offset 的正负性
    nature = 1 if offset > 0 else 0

    # 应用分段函数
    offset = abs(offset)
    offset = apply_segment_function(offset)

    # 调整 offset 的比例
    if nature == 1:
        offset = -offset * SCALE_RIGHT / OFFSET_SCALE
    else:
        offset = offset * SCALE_LEFT / OFFSET_SCALE

    # 计算舵机角度
    angle = ANGLE_MID + offset

    # 限幅保护
    if angle > ANGLE_LEFT_MAX:
        angle = ANGLE_LEFT_MAX
    elif angle < ANGLE_RIGHT_MAX:
        angle = ANGLE_RIGHT_MAX

    duty_servo = duty_angle(angle)  # 获取舵机中值角度对应占空比并更新舵机PWM

    if flag == "isCircle":
        pwm_servo.duty_u16(duty_angle(ANGLE_MID))  # 保持为中值
    else:
        pwm_servo.duty_u16(duty_servo)

    gc.collect()
    return angle


