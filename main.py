from typing import Any

from machine import *
from smartcar import *
from seekfree import *
from display import *
import gc
import time

"""
prompt
因为在每次调用函数都初始化会对性能有影响，我决定把函数里的初始化移动到主函数中执行，
在调用函数的时候直接传入主函数中创建的实例，接下来我要发送给你代码，
请你分别给出在主函数中初始化实例的代码和修改后的函数代码（不再在函数内初始化，而是在函数的输入参数中传入实例）
"""

"""
SMGG.Tips:
main主要进行初始化，后面的算法处理单独封装，以达到可读，参数调整方便的效果
"""
# 核心板上 C4 是 LED
led1 = Pin('C4', Pin.OUT, pull=Pin.PULL_UP_47K, value=True)
# 开发板上的 C19 是拨码开关
end_switch = Pin('C19', Pin.IN, pull=Pin.PULL_UP_47K, value=True)
end_state = end_switch.value()

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 初始化部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

"""
CCD 初始化
调用 TSL1401 模块获取 CCD 实例,参数是采集周期 调用多少次 capture/read 更新一次数据
默认参数为 1 调整这个参数相当于调整曝光时间倍数,这里填了 10 代表 10 次 capture/read 调用才会更新一次数据

调用案例：
# ccd_data1, ccd_data2 = read_ccd_data(ccd)
# print(ccd_data1)
# print(ccd_data2)
"""
from Get_CCD import read_ccd_data, process_ccd_data, map_error_to_servo_angle
from CCD_Tool import *

ccd = TSL1401(1)  # 调用 TSL1401 模块获取 CCD 实例,参数是采集周期 调用多少次 capture/read 更新一次数据
ccd.set_resolution(TSL1401.RES_12BIT)  # 调整 CCD 的采样精度为 12bit
wireless = WIRELESS_UART(460800)  # 实例化 WIRELESS_UART 模块 参数是波特率
wireless.send_str("Hello World.\r\n")  # 测试无线正常
time.sleep_ms(500)

"""
电机 Motor 初始化,示例调用:

control_motor(motor_l, motor_r)  # 传入左右电机控制对象
"""
from Motor_Origin import control_motor

motor_l = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C25_DIR_C27, 13000, duty=0, invert=False)
motor_r = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C24_DIR_C26, 13000, duty=0, invert=True)

"""
Encoder 初始化
control_encoder(encoder_l, encoder_r)
"""
from Motor_Origin import control_encoder

encoder_l = encoder("D0", "D1", False)
encoder_r = encoder("D2", "D3", True)

"""
舵机 Motor_Servo 初始化，示例调用：
set_servo_angle(pwm_servo)
"""
from Motor_Servo import set_servo_angle, duty_angle

duty_servo = int(duty_angle(101.0))  # 初始化舵机打角 学习板上舵机接口为 C20
pwm_servo = PWM("C20", 300, duty_u16=duty_servo)  # 调用 machine 库的 PWM 类实例化一个 PWM 输出对象

"""
Screen 初始化
init_Screen()
"""
from Screen import init_Screen

lcd = init_Screen()

"""
Key 初始化
"""
from Key_Data import Key_data

key = KEY_HANDLER(10)  # 实例化 KEY_HANDLER 模块 参数是按键扫描周期

"""
flag 初始化
"""
from Elements_CCD import Element_flag, CCD_Error, detect_intersection, detect_roundabout

ticker_flag = False  # 定时器数据建立
ticker_count = 0  # 时间延长标志（使用方法见encoder例程）

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 调参部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
# 初始化 ccdSuper 和 angle
ccdSuper = angle = key_4 = Key_1 = Key_2 = flag = Statu = mid_line = 0

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 定时器内容编写
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
pit1 = ticker(1)  # 选定1号定时器:关联采集接口,最少一个,最多八个
pit1.capture_list(encoder_l, encoder_r, ccd, key)  # 编码器关联,ccd关联
pit1.callback(time_pit_handler)  # 关联 Python 回调函数
pit1.start(10)  # 启动 ticker 实例 参数是触发周期 单位是毫秒


# 定义一个回调函数（定时运行程序可以写在里面）
def time_pit_handler(time):
    global ticker_flag, ccdSuper, angle, key_4, Statu
    ticker_flag = True  # 否则它会新建一个局部变量

    # encoder
    control_encoder(encoder_l, encoder_r)
    # 电机运行程序
    control_motor(motor_l, motor_r, key_4, ccdSuper, Statu)
    # 舵机运行程序
    angle = set_servo_angle(pwm_servo, ccdSuper)


""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 主函数部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

ccdAllData = []
while True:
    if ticker_flag:
        key_1, key_2, key_3, key_4 = Key_data(key)  # 读取数据
        ccd_data1, ccd_data2 = read_ccd_data(ccd)  # 读取CCD值，存储到数组
        Statu = Element_flag(ccd_data1)  # flag

        left_edge, right_edge, mid_line = find_road_edges(ccd_data1, mid_line)
        ccdSuper = 64 - mid_line

        if key_1 == 1:
            print(f"ccd_data1: {ccd_data1}")
            ccdAllData.append(ccd_data1)
            key_1 = 0

        if key_2 == 1:
            print(ccdAllData)

        # print("enc ={:>6d}, {:>6d}\r\n".format(encoder_l.get(), encoder_r.get()))
        # wireless.send_ccd_image(WIRELESS_UART.ALL_CCD_BUFFER_INDEX)  # 无线打印ccd数据

        # 定时器关断标志
        ticker_flag = False

    # 屏幕显示
    lcd.str24(0, 24*0, "offset={:>.2f}.".format(ccdSuper), 0xFFFF)
    lcd.str24(0, 24*1, "angle={:>.2f}.".format(angle), 0xFFFF)
    lcd.str24(0, 24*2, "mid={:>.2f}.".format(mid_line), 0xFFFF)
    lcd.str24(0, 24*3, "flag={:>.2f}.".format(flag), 0xFFFF)
    lcd.str24(0, 24*4, "flag={:>.2f}.".format(flag), 0xFFFF)
    lcd.str24(0, 24*5, "flag={:>.2f}.".format(flag), 0xFFFF)
    lcd.str24(0, 24*6, "flag={:>.2f}.".format(flag), 0xFFFF)



    # 通过 wave 接口显示数据波形 (x,y,width,high,data,data_max)
    # lcd.wave(0, 0, 128, 64, ccd_data1, max=200)
    # lcd.wave(0, 64, 128, 64, ccd_data2, max=200)

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()
