from machine import *
from smartcar import *
from seekfree import *
from display import *
import gc
import time
from Find_Barrier import find_barrier

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
from Get_CCD import *
from CCD_Tool import *
from Find_Circle import *

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
from seekfree import KEY_HANDLER

key = KEY_HANDLER(10)  # 实例化 KEY_HANDLER 模块 参数是按键扫描周期

"""
flag 初始化
"""

ticker_flag = False  # 定时器数据建立
ticker_count = 0  # 时间延长标志（使用方法见encoder例程）

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 调参部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
# 初始化 ccdSuper 和 angle
ccdSuper = angle = key_4 = Key_1 = Key_2 = flag = Statu = isCircleNow = mid_line = 0
left_edge = right_edge = isCircleNow = leftOrRight = goCircle = findCircleTimes = 0
""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 定时器内容编写
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


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


pit1 = ticker(1)  # 选定1号定时器:关联采集接口,最少一个,最多八个
pit1.capture_list(encoder_l, encoder_r, ccd, key)  # 编码器关联,ccd关联
pit1.callback(time_pit_handler)  # 关联 Python 回调函数
pit1.start(10)  # 启动 ticker 实例 参数是触发周期 单位是毫秒

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 主函数部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

ccdAllData = []
while True:
    if ticker_flag:
        key_data = key.get()  # 获取按键数据
        key_1, key_2, key_3, key_4 = key_data  # 解包按键数据

        if key_data[0]:
            # 当1被按下，打印当前ccd_data，并存储到列表
            print(f"ccd_data1: {ccd_data1}")
            ccdAllData.append(ccd_data1)
            key.clear(1)

        if key_data[1]:
            # 当2被按下，打印之前全部存储的ccd_data
            print("ccdAllData : \n")
            print(ccdAllData)
            key.clear(2)

        if key_data[2]:
            # 暂时无用处
            print("key3 = {:>6d}.".format(key_data[2]))
            key.clear(3)

        if key_data[3]:
            # 按下后不执行key.clear(4)，电机启动，可一直保持key_4 == 1
            key_4 = 1  # 按键按下后将 key_4 设置为 1

        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        Tips: 基本数据采集部分
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        ccd_data1, ccd_data2 = read_ccd_data(ccd)  # 读取CCD值，存储到数组
        left_edge, right_edge, mid_line = find_road_edges(ccd_data1, mid_line)  # 计算左右边界与中线
        ccdSuper = 64 - mid_line  # 误差值
        lastWidth = roadWidth  # 上一次的道路宽度，用于判断避障和环中点
        roadWidth = abs(left_edge - right_edge)  # 这一次的道路宽度

        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        Tips: 环岛部分
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        isCircleNow, leftOrRight = is_circle(ccd_data1)  # isCircleNow为是否检测到环，leftOrRight为左环还是右环

        if (isCircleNow == True) and (goCircle == False):
            # 当goCircle 不为True时，进行入环检测，如果goCircle已经变成True，代表在之前已经检测到环
            # 防止二次判环将goCircle的标志位刷掉，后续赛道存在多个环可以更改此处逻辑
            findCircleTimes += 1  # 连续n次ccd的数据都判断为入环，才设置为入环标志，防止误判，目前n为2

            if findCircleTimes == 2:
                checkCircle = 1  # 判断到了入环标志，将checkCircle置1，代表进入入环状态
                findCircleTimes = 0

        if checkCircle:
            filled_mid_line = fill_line(ccd_data1, leftOrRight, checkCircle)  # 确定补线后的中线
            ccdSuper = 64 - filled_mid_line  # 补线状态下的误差值,覆盖之前的ccdSuper,防止被前半段圆环误判左转

            # 在入环标志checkCircle==True时，如果检测到环中点，将goCircle置为True
            goCircle = Go_circle_now(ccd_data1, lastWidth)
            if goCircle:
                if leftOrRight == "left":
                    set_servo_angle(pwm_servo, 95)  # 左打角
                    checkCircle = 0  # 此时置0，退出补线逻辑
                    """蜂鸣器响"""
                if leftOrRight == "right":
                    set_servo_angle(pwm_servo, 110)  # 右打角
                    checkCircle = 0  #此时置0，退出补线逻辑
                    """蜂鸣器响"""

        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        Tips: 避障部分
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        barrierNow, barrierLocation = find_barrier(ccd_data1,lastWidth)
        if barrierNow:
            if barrierLocation == "left":
                set_servo_angle(pwm_servo, 106)  # 障碍物在左侧,右打角
            if barrierLocation == "right":
                set_servo_angle(pwm_servo, 97)  # 障碍物在右侧,左打角



        # print("enc ={:>6d}, {:>6d}\r\n".format(encoder_l.get(), encoder_r.get())) # 打印编码器数据
        # wireless.send_ccd_image(WIRELESS_UART.ALL_CCD_BUFFER_INDEX)  # 无线打印ccd数据


        # 定时器关断标志
        ticker_flag = False

    # 屏幕显示
    lcd.str24(0, 24 * 0, "offset={:>.2f}.".format(ccdSuper), 0xFFFF)
    lcd.str24(0, 24 * 1, "angle={:>.2f}.".format(angle), 0xFFFF)
    lcd.str24(0, 24 * 2, "mid_line={:>.2f}.".format(mid_line), 0xFFFF)
    lcd.str24(0, 24 * 3, "goCircle={:>.2f}.".format(goCircle), 0xFFFF)
    lcd.str24(0, 24 * 4, "isCircleNow={:>.2f}.".format(isCircleNow), 0xFFFF)
    lcd.str24(0, 24 * 5, "roadWidth={:>.2f}.".format(roadWidth), 0xFFFF)
    # lcd.str24(0, 24*6, "roadWidth={:>.2f}.".format(roadWidth), 0xFFFF)

    # 通过 wave 接口显示数据波形 (x,y,width,high,data,data_max)
    # lcd.wave(0, 0, 128, 64, ccd_data1, max=200)
    # lcd.wave(0, 64, 128, 64, ccd_data2, max=200)

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()
