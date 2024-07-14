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
from Elements_CCD import Element_flag, detect_intersection, on_detect_intersection, out_detect_intersection

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
flag = realLastFlag = 0
Statu = 0
mid_line_short = mid_line_long = 0
last_flag = 0
ahead = 1
ccdThresholdDetermination = 0
T1 = T2 = 500
Yaw = 0
num = 0
runTimes = 0
displayCheck = menu = 0
speedSet = 40
last10Middle1 = last10Middle2 = [0] * 10
trueValue1 = trueValue2 = 0
lastCcdSuper = 0
history1 = [[0] * 128 for _ in range(10)]
history2 = [[0] * 128 for _ in range(10)]
""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 定时器内容编写
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


# 定义一个回调函数（定时运行程序可以写在里面）
def time_pit_handler(time):
    global ticker_flag, ccdSuper_short, angle, Statu, flag, speedSet
    ticker_flag = True  # 否则它会新建一个局部变量
    """用户自己的软件代码"""
    # encoder
    control_encoder(encoder_l, encoder_r)
    # 电机运行程序
    control_motor(motor_l, motor_r, ccdSuper, Statu, flag, speedSet)
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
        runTimes += 1
        # 初始确定CCD1和CCD2的阈值
        if Statu == 1 and ccdThresholdDetermination == 0:
            ccdThresholdDetermination = 1
            T1 = T2 = 0
            for _ in range(0, 10):
                originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
                originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
                T1 += threshold_determination(originalCcdData1)
                T2 += threshold_determination(originalCcdData2)
            T1 = T1 / 10.0
            T2 = T2 / 10.0

        if not Statu:
            ccdSuper = 0

        # 特殊元素处理，注意，元素处理只用ccd1（ccd_short）
        # 存在标记2023空悬，作用只在于退出长镜头循迹
        # 因为元素的特征总是ccd2先得到，所以我们使用ccd2为先决条件，当flag被提前进入时ccd2会自动退出
        # 长镜头识别十字，然后关断，只使用短镜头，知道短镜头识别到十字特征，十字路段结束
        if Statu:
            """基本数据采集部分"""
            originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
            originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
            trueValue1 = sum(originalCcdData1)  # 计算ccd_data1 所有值的求和
            trueValue2 = sum(originalCcdData2)  # 计算ccd_data2 所有值的求和
            ccd_data = read_ccd_data(originalCcdData1, originalCcdData2, T1, T2)  # 获取二值化后的ccd_data
            ccd_data1 = ccd_data[0]  # 近端ccd
            ccd_data2 = ccd_data[1]  # 远端ccd
            history1[1:] = history1[:-1]  # history1 存储了最近十次的ccd_data1值
            history1[0] = ccd_data1
            history2[1:] = history2[:-1]  # history2 存储了最近十次的ccd_data2值
            history2[0] = ccd_data2
            last10Middle1 = [mid_line_long] + last10Middle1[:-1]  # 这个数组会存储最近十次的中线位置，并保证更新
            last10Middle1 = [mid_line_long] + last10Middle1[:-1]  # 这个数组会存储最近十次的中线位置，并保证更新
            key_1, key_2, key_3, Statu = Key_data(key)  # 读取按键数据
            # 提取边线和中线
            left_edge_short, right_edge_short, mid_line_short = find_road_edges(ccd_data1, flag, 1)
            left_edge_long, right_edge_long, mid_line_long = find_road_edges(ccd_data2, flag, 2)



            # 这个mid_line_long 的计算方法是，目前中线占10%权重，历史中线占90%权重，最后+n补充，目前n=0
            mid_line_long = 0.1 * mid_line_long + 0.9 * sum(last10Middle) / 10 + 0
            ccdSuper_short = mid_line_short - 64
            ccdSuper_long = mid_line_long - 64
            # ccd_long和ccd_short的应用转换条件
            # 车辆转入急弯时切换镜头，同时存在元素情况时也切换镜头
            if abs(ccdSuper) > 15 or flag != 0:
                ccdSuper = ccdSuper_short
            else:
                ccdSuper = ccdSuper_long

            """十字路口判别"""
            if trueValue1 < 60000 and trueValue2 > 75000:
                flag = 17788
                ccdSuper = ccdSuper_short
            if flag == 17788:
                if trueValue1 > 70000 and trueValue2 > 70000:
                    flag = 27788
                    ccdSuper = lastCcdSuper
            if flag == 27788 and trueValue1 < 70000 and trueValue2 < 70000:
                flag = 0
            if trueValue1 < 60000 and trueValue2 < 60000:
                # 如果长时间保持直线的逻辑
                num += 1
                if num > 200:
                    flag = 0
            else:
                num = 0
            lastCcdSuper = ccdSuper  # 上一次的误差

        # 蜂鸣器简单调用
        # 预备阶段响铃
        if flag == 50:
            BEEP.value(True)
        else:
            BEEP.value(False)
        """if flag == 4:
            BEEP.value(True)
        elif flag == 501:
            BEEP.value(True)
        elif flag == 7788:
            BEEP.value(True)
        else:
            BEEP.value(False)"""

        imu_data = imu.get()  # 通过 get 接口读取数据
        current_rate = int(float(imu_data[5]) / 55.5)  # 计算当前角速度并归一化
        Yaw += current_rate * 0.04  # 积分更新角度, 假设 0.4 是时间间隔或增益
        if flag == 4:
            Yaw = 0

        # wireless.send_ccd_image(WIRELESS_UART.ALL_CCD_BUFFER_INDEX)  # 无线打印ccd数据

        debugMode = 0  # Debug模式，如果启用需要在这里设置为1，启用后每100次While的执行就会打印一次数据
        if debugMode:
            if runTimes % 100 == 0:
                print(f"ccd_data1: {ccd_data1[54:74]}")
                print(f"ccd_data2: {ccd_data2[54:74]}")
                print(f"flag: {flag}")
                print(f"mid_line_short: {mid_line_short}")
                print(f"mid_line_long: {mid_line_long}")
                print(f"realLastFlag： {realLastFlag}")

        ticker_flag = False  # 定时器关断标志

    """屏幕显示部分"""
    key_1, key_2, key_3, Statu = Key_data(key)

    if key_1:
        print("key1")
        displayCheck += 1

    if key_2:
        print("key2")
        displayCheck -= 1

    if key_3:
        print("key3")
        lcd.clear(0x0000)
        if displayCheck == 1 and menu == 0:
            print("跳转到速度设定菜单了")
            menu = 1
            displayCheck = 0

        if displayCheck == 2 and menu == 0:
            print("跳转到元素展示菜单了")
            menu = 2
            displayCheck = 0

        if displayCheck == 1 and menu == 1:
            speedSet = 60
            menu = 2
            print("速度设置为60了")

        if displayCheck == 2 and menu == 1:
            speedSet = 80
            menu = 2
            print("速度设置为80了")

        if displayCheck == 3 and menu == 1:
            speedSet = 90
            menu = 2
            print("速度设置为90了")
        lcd.clear(0x0000)

    """初级菜单(1级)"""
    if displayCheck == 0 and menu == 0:
        display_strings(lcd, ["Menu1 ", "Choose Speed ", "Show Elements "], [1, 0, 0])

    if displayCheck == 1 and menu == 0:
        display_strings(lcd, ["Menu1 ", "Choose Speed ", "Show Elements "], [0, 1, 0])  # menu = 1

    if displayCheck == 2 and menu == 0:
        display_strings(lcd, ["Menu1 ", "Choose Speed ", "Show Elements "], [0, 0, 1])  # menu = 2

    """速度设定菜单(2级)"""
    if displayCheck == 0 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [1, 0, 0, 0])

    if displayCheck == 1 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [0, 1, 0, 0])

    if displayCheck == 2 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [0, 0, 1, 0])

    if displayCheck == 3 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [0, 0, 0, 1])

    """数据展示菜单(2级)"""
    if menu == 2:
        display_strings(lcd, ["ccdSuper", "angle", "flag", "Yaw", "trueValue1", "trueValue2"],
                        [ccdSuper, angle, flag, Yaw, int(trueValue1), int(trueValue2)])

    # 通过 wave 接口显示数据波形 (x,y,width,high,data,data_max)
    # lcd.wave(0, 0, 128, 64, ccd_data1, max=200)
    # lcd.wave(0, 64, 128, 64, ccd_data2, max=200)

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()








