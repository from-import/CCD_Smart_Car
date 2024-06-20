# 示例程序运行效果为每 50ms(0.05s) 改变一次 C20 引脚输出的占空比
# 对应拓展学习板供电并接接入舵机后 舵机将会以 10s 为周期来回摆动
# 每次改变舵机动作方向时 C4 LED 灯的亮灭状态改变一次

# 请务必注意！！！禁止安装舵机摆臂连接前轮测试！！！
# 请务必注意！！！禁止安装舵机摆臂连接前轮测试！！！
# 请务必注意！！！禁止安装舵机摆臂连接前轮测试！！！

# 这是为了避免没有调整过舵机中值先装舵机 导致舵机角度与摆臂限幅冲突
# 错误的安装步骤存在舵机堵转的风险 舵机堵转会导致舵机损坏

# 从 machine 库包含所有内容
from machine import *

# 包含 gc 与 time 类
import gc
import time

# 核心板上 C4 是 LED
# 调用 machine 库的 Pin 类实例化一个引脚对象
# 配置参数为 引脚名称 引脚方向 模式配置 默认电平
# 详细内容参考 RT1021-MicroPython固件接口说明.pdf
led1 = Pin('C4', Pin.OUT, pull=Pin.PULL_UP_47K, value=True)

# 使用 300Hz 的舵机控制频率
pwm_servo_hz = 300


# 定义一个角度与占空比换算的函数 传入参数为 PWM 的频率和目标角度
# 计算公式为 (duty_max / (1000ms / freq_Hz)) * (0.5 + angle / 90.0)
# duty_max / (1000ms / freq_Hz) 得到每毫秒对应的占空比数值
# (0.5 + angle / 90.0) 得到角度对应的毫秒数 舵机是 0-180 对应 0.5ms-2.5ms
def duty_angle(freq, angle):
    return (65535.0 / (1000.0 / freq) * (0.5 + angle / 90.0))


# 初始角度 90 度 也就是舵机中值角度
angle = 90.0
# 舵机动作方向
dir = 1
# 获取舵机中值角度对应占空比
# int(x) 接口用于将 x 转换为整数数值
# 不少接口仅支持整数数值输入 否则会报错
duty = int(duty_angle(pwm_servo_hz, angle))
# 学习板上舵机接口为 C20
# 调用 machine 库的 PWM 类实例化一个 PWM 输出对象
# 配置参数为 引脚名称 PWM 频率 初始占空比
pwm_servo = PWM("C20", pwm_servo_hz, duty_u16=duty)

while True:
    time.sleep_ms(1000)
    # 往复计算舵机角度
    if dir:
        angle = angle + 0.1
        if angle >= 95.0:
            dir = 0
            led1.toggle()
    else:
        angle = angle - 0.1
        if angle <= 85.0:
            dir = 1
            led1.toggle()
    # 获取舵机角度对应占空比
    duty = int(duty_angle(pwm_servo_hz, angle))
    # 设置更新 PWM 输出后可以看到舵机动作
    pwm_servo.duty_u16(duty)

    gc.collect()
