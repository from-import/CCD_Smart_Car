
# 本示例程序演示如何使用 seekfree 库的 MOTOR_CONTROLLER 类接口
# 使用 RT1021-MicroPython 核心板搭配 DRV8701/HIP4082 双驱模块进行测试

# 示例程序运行效果为电机反复正反加减速转动
# C4 LED 会根据电机的正反转点亮或熄灭

# 从 machine 库包含所有内容
from machine import *

# 从 seekfree 库包含 MOTOR_CONTROLLER
from seekfree import MOTOR_CONTROLLER

# 包含 gc time 类
import gc
import time

# 核心板上 C4 是 LED
led1 = Pin('C4' , Pin.OUT, pull = Pin.PULL_UP_47K, value = True)

# 实例化 MOTOR_CONTROLLER 电机驱动模块 一共四个参数 两个必填两个可选 [mode,freq,duty,invert]
# mode - 工作模式 一共四种选项 [PWM_C24_DIR_C26,PWM_C25_DIR_C27,PWM_C24_PWM_C26,PWM_C25_PWM_C27]
#        实际对应 DRV8701 双驱双电机 以及 HIP4082 双驱双电机 请确保驱动正确且信号连接正确
# freq - PWM 频率
# duty - 可选参数 初始的占空比 默认为 0 范围 ±10000 正数正转 负数反转 正转反转方向取决于 invert
# invert - 可选参数 是否反向 默认为 0 可以通过这个参数调整电机方向极性
motor_l = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C25_DIR_C27, 13000, duty = 0, invert = True)
motor_r = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C24_DIR_C26, 13000, duty = 0, invert = True)

# 本例程默认使用 DRV8701 双驱模块搭配双电机 ！！！
# 本例程默认使用 DRV8701 双驱模块搭配双电机 ！！！
# 本例程默认使用 DRV8701 双驱模块搭配双电机 ！！！

motor_dir = 1
motor_duty = 0
motor_duty_max = 1000

while True:
    time.sleep_ms(100)
    
    if motor_dir:
        motor_duty = motor_duty + 50
        if motor_duty >= motor_duty_max:
            motor_dir = 0
    else:
        motor_duty = motor_duty - 50
        if motor_duty <= -motor_duty_max:
            motor_dir = 1
    
    led1.value(motor_duty < 0)
    # duty 接口更新占空比 范围 ±10000
    motor_l.duty(motor_duty)
    motor_r.duty(motor_duty)
    
    gc.collect()

