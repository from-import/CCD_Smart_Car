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
# 主板上 C9 是蜂鸣器
BEEP = Pin('C9', Pin.OUT, pull=Pin.PULL_UP_47K, value=False)
# 开发板上的 C19 是拨码开关
end_switch = Pin('C19', Pin.IN, pull=Pin.PULL_UP_47K, value=True)
end_state = end_switch.value()

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 初始化部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

"""
CCD 初始化，调用案例：
# ccd_data1, ccd_data2 = read_ccd_data(ccd)
# print(ccd_data1)
# print(ccd_data2)
"""

from Get_CCD import read_ccd_data, find_road_edges, threshold_determination

# 调用 TSL1401 模块获取 CCD 实例
# 参数是采集周期 调用多少次 capture/read 更新一次数据
# 默认参数为 1 调整这个参数相当于调整曝光时间倍数
# 这里填了 10 代表 10 次 capture/read 调用才会更新一次数据
ccd = TSL1401(1)
# 调整 CCD 的采样精度为 12bit
ccd.set_resolution(TSL1401.RES_12BIT)

# 实例化 WIRELESS_UART 模块 参数是波特率
wireless = WIRELESS_UART(460800)
# 测试无线正常
wireless.send_str("Hello World.\r\n")
time.sleep_ms(500)

"""
电机 Motor 初始化,示例调用:

control_motor(motor_l, motor_r)  # 传入左右电机控制对象
"""
from Motor_Origin import control_motor, Record_Distance

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

# 初始化舵机执行
duty_servo = int(duty_angle(101.0))
# 学习板上舵机接口为 C20
# 调用 machine 库的 PWM 类实例化一个 PWM 输出对象
pwm_servo = PWM("C20", 300, duty_u16=duty_servo)

"""
Screen 初始化
init_Screen()
"""
from Screen import init_Screen, display_strings

lcd = init_Screen()

"""
Key 初始化
"""
from Key_Data import Key_data

# 实例化 KEY_HANDLER 模块 参数是按键扫描周期
key = KEY_HANDLER(10)

"""
flag 初始化
"""
from Elements_CCD import Element_flag, detect_intersection, detect_intersection2, out_detect_intersection

"""
imu 初始化
"""
# 调用 IMU660RA 模块获取 IMU660RA 实例
imu = IMU660RA()

# 定时器数据建立
ticker_flag = False
# 时间延长标志（使用方法见encoder例程）
ticker_count = 0

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 调参部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
# 初始化 ccdSuper 和 angle
ccdSuper_short = ccdSuper_long = ccdSuper = 0
angle = 0
flag = 0
Statu = 0
mid_line_short = mid_line_long = 0
last_flag = 0
ahead = 1
ccdThresholdDetermination = 0
checkCrossing = 0
T1 = T2 = 0
Yaw = 0
""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 定时器内容编写
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


# 定义一个回调函数（定时运行程序可以写在里面）
def time_pit_handler(time):
    global ticker_flag, ccdSuper_short, angle, Statu, flag
    ticker_flag = True  # 否则它会新建一个局部变量
    """用户自己的软件代码"""
    # encoder
    control_encoder(encoder_l, encoder_r)
    # 电机运行程序
    control_motor(motor_l, motor_r, ccdSuper, Statu, flag)
    # 舵机运行程序
    angle = set_servo_angle(pwm_servo, ccdSuper, flag)


# 选定1号定时器
pit1 = ticker(1)

# 关联采集接口 最少一个 最多八个
# 编码器关联,ccd关联
pit1.capture_list(encoder_l, encoder_r, ccd, key, imu)
# 关联 Python 回调函数
pit1.callback(time_pit_handler)
# 启动 ticker 实例 参数是触发周期 单位是毫秒
pit1.start(10)

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 主函数部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

while True:
    if (ticker_flag):
        # 初始确定CCD1和CCD2的阈值
        if Statu == 1 and ccdThresholdDetermination == 0:
            ccdThresholdDetermination = 1
            T1 = T2 = 0
            for _ in range(0, 3):
                originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
                originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
                T1 += threshold_determination(originalCcdData1)
                T2 += threshold_determination(originalCcdData2)
            T1 = T1 / 3.0
            T2 = T2 / 3.0

        """基本数据采集部分"""
        originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
        originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
        ccd_data2, ccd_data1 = read_ccd_data(originalCcdData1, originalCcdData2, T1, T2)

        # 读取数据
        key_1, key_2, key_3, Statu = Key_data(key)
        # 提取边线和中线
        left_edge_short, right_edge_short, mid_line_short = find_road_edges(ccd_data1, flag, 1)
        left_edge_long, right_edge_long, mid_line_long = find_road_edges(ccd_data2, flag, 2)
        ccdSuper_short = mid_line_short - 64
        ccdSuper_long = mid_line_long - 64

        # ccd_long和ccd_short的应用转换条件
        # 车辆转入急弯时切换镜头，同时存在元素情况时也切换镜头
        if (abs(ccdSuper) > 15 or flag != 0):
            ccdSuper = ccdSuper_short
        else:
            ccdSuper = ccdSuper_long

        if not Statu:
            ccdSuper = 0

        # 特殊元素处理，注意，元素处理只用ccd1（ccd_short）
        # 因为元素的特征总是ccd2先得到，所以我们使用ccd2为先决条件，当flag被提前进入时ccd2会自动退出
        # 长镜头识别十字，然后关断，只使用短镜头，知道短镜头识别到十字特征，十字路段结束
        if Statu:
            if not flag:
                flag = Element_flag(ccd_data2, left_edge_long, right_edge_long, ahead)
            # 十字是一种非常特殊的处理,只要读到一次就会记录一段路
            if detect_intersection(ccd_data1, ccd_data2):
                checkCrossing = checkCrossing + 1
                if checkCrossing == 3:
                    flag = 17788
            if detect_intersection2(ccd_data1, ccd_data2) and flag == 17788:
                flag = 7788

            if out_detect_intersection(ccd_data1, ccd_data2) and flag == 7788:
                flag = 0

            elif flag != 7788:
                flag = Element_flag(ccd_data1, left_edge_short, right_edge_short, ahead)
                # 当ahead为1时，程序会反复确认预入环条件，不符合会返回0
                if not flag and ahead == 1:
                    # 给了flag一个值，强迫巡线程序退出长镜头
                    flag = 2023
                    checkCrossing = 0
                # 如果短镜头也识别到了入环条件，此时ahead开关没有关断，flag会返回2023
                # 我们给flag赋予正确的值并关断ahead开关
                elif flag == 2023:
                    flag = 4
                    ahead = 0

        # Record_Distance 是一个距离积分函数，当1时会打开开关积分,0时会清空函数内的数值
        if flag == 7788:
            Record_dis = 1
        else:
            Record_dis = 0

        if flag == 7788 and Record_Distance(Record_dis) > 100:
            flag = 0

        # 元素结束，重新进入长摄像头循迹，打开ahead开关，保护Element_flag函数中的global数值
        if last_flag != 0 and flag == 0:
            ahead = 1

        last_flag = flag

        # 蜂鸣器简单调用
        # 预备阶段响铃
        if flag == 4:
            BEEP.value(True)
        elif flag == 50:
            BEEP.value(True)
        elif flag == 7788:
            BEEP.value(True)
        else:
            BEEP.value(False)

        # 通过 get 接口读取数据
        imu_data = imu.get()
        # 计算当前角速度并归一化
        current_rate = int(float(imu_data[5]) / 63.0)

        # 积分更新角度
        Yaw += current_rate * 0.04  # 假设 0.4 是时间间隔或增益

        # 无线打印ccd数据
        # wireless.send_ccd_image(WIRELESS_UART.ALL_CCD_BUFFER_INDEX)

        # 定时器关断标志
        ticker_flag = False

    # 屏幕显示(计划写一个菜单)
    display_strings(lcd, ["ccdSuper", "angle", "flag", "Yaw"], [ccdSuper, angle, flag, Yaw])
    # 通过 wave 接口显示数据波形 (x,y,width,high,data,data_max)
    # lcd.wave(0, 0, 128, 64, ccd_data1, max=200)
    # lcd.wave(0, 64, 128, 64, ccd_data2, max=200)

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()
















