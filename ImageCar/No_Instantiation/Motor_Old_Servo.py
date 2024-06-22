from machine import *
import gc
import time


# 定义一个角度与占空比换算的函数
def duty_angle(freq, angle):
    return int(65535.0 / (1000.0 / freq) * (0.5 + angle / 90.0))


def set_servo_angle(led1, pwm_servo, pwm_servo_hz, angle=101):
    """
    设置舵机的角度。

    参数:
    led1 (Pin): LED 引脚实例。
    pwm_servo (PWM): PWM 引脚实例。
    pwm_servo_hz (int): PWM 频率。
    angle (int): 目标角度，范围在 0 到 180 度之间。
    函数的初始赋值是101，为目前的舵机中值
    """
    if not 0 <= angle <= 180:
        raise ValueError("Angle must be between 0 and 180 degrees.")

    # 获取舵机中值角度对应占空比
    duty = duty_angle(pwm_servo_hz, angle)

    # 设置更新 PWM 输出后可以看到舵机动作
    pwm_servo.duty_u16(duty)

    # 切换 LED 状态
    led1.toggle()

    gc.collect()


# 案例
# set_servo_angle(90)

