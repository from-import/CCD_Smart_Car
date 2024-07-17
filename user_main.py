from machine import *
from smartcar import *
from seekfree import *
from display import *
import gc
import time
import os
import io

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

from Get_CCD import read_ccd_data, find_road_edges, threshold_determination, white

# 调用 TSL1401 模块获取 CCD 实例
# 参数是采集周期 调用多少次 capture/read 更新一次数据
# 默认参数为 1 调整这个参数相当于调整曝光时间倍数
# 这里填了 10 代表 10 次 capture/read 调用才会更新一次数据
ccd = TSL1401(1)
# 调整 CCD 的采样精度为 12bit
ccd.set_resolution(TSL1401.RES_12BIT)

# 实例化 WIRELESS_UART 模块 参数是波特率
wireless = WIRELESS_UART(460800)

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
speedSet = 48
last10Middle1 = last10Middle2 = [0] * 5
trueValue1 = trueValue2 = 0
lastCcdSuper = 0
history1 = [[0] * 128 for _ in range(10)]
history2 = [[0] * 128 for _ in range(10)]
user_data1 = []
user_data2 = []
crossSuper = 0
averageMedLine1 = averageMedLine2 = 64
ccd_data1 = ccd_data2 = originalCcdData1 = originalCcdData2 = [0] * 128
crossFlag = 0
width1 = width2 = 0
searchMidline2 = searchMidline1 = 0
searchFlag1 = searchFlag2 = 0
longNumber = 0
"""仿照国赛代码的变量"""
ccd_diff1 = ccd_diff2 = [0] * 128
max_peak1 = max_peak2 = 0
left_last_find1 = left_last_find2 = 0
right_last_find1 = right_last_find2 = last_left = last_right = 0
rising_edge_cnt = falling_edge_cnt = [0] * 5
rising_edge = falling_edge = 0
left_last_find = right_last_find = 0
left = right = 64
road_type = 0
threshold = 150
normalCcdSuper = 0
number = 0
tiaoBianCount1 = tiaoBianCount2 = 0
left_edge_short = right_edge_short = left_edge_long = right_edge_long = 0
isCircle = 0
TrueRuntime = 0
leftOrRight = "left"
goCircle = 0
stoptime = 0
chance = 0
""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 定时器内容编写
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


# 计算跳变点数
def count_transitions(ccdData, interval=3, yuzhi=15):
    tiaobian = 0
    last_tiaobian = 0
    this_tiaobian = 0

    for i in range(20, 100):
        if abs(ccdData[i] - ccdData[i + interval]) > yuzhi:
            this_tiaobian = i
            if this_tiaobian != last_tiaobian + 1:
                tiaobian += 1
            last_tiaobian = this_tiaobian

    return tiaobian


def write_ccd_in_txt(many_ccd_data, txtname, mode="w+"):
    # 函数作用：将包含很多 ccd_data 的一个列表完全写入 txtname.txt
    os.chdir("/flash")
    userFile = io.open(f"{txtname}.txt", f"{mode}")
    userFile.seek(0, 0)
    for ccd_data in many_ccd_data:
        userFile.write(f"\n[")
        for item in ccd_data:
            if item == len(ccd_data) - 1:
                userFile.write("%d" % item)
            else:
                userFile.write("%d," % item)
        userFile.write(f"],")
    userFile.flush()  # 将缓冲区数据写入到文件 清空缓冲区 相当于保存指令
    userFile.close()  # 最后将文件关闭即可


# 定义一个回调函数（定时运行程序可以写在里面）
def time_pit_handler(time):
    global ticker_flag, ccdSuper_short, angle, Statu, flag, speedSet, Yaw
    ticker_flag = True  # 否则它会新建一个局部变量
    """用户自己的软件代码"""
    # encoder
    control_encoder(encoder_l, encoder_r)
    # 电机运行程序
    control_motor(motor_l, motor_r, ccdSuper, Statu, flag, speedSet)
    # 舵机运行程序
    angle = set_servo_angle(pwm_servo, ccdSuper, flag, ccd_data1)
    # 陀螺仪
    imu_data = imu.get()  # 通过 get 接口读取数据
    current_rate = int(float(imu_data[5]) / 151)  # 计算当前角速度并归一化
    Yaw += current_rate * 0.1  # 积分更新角度, 假设 0.4 是时间间隔或增益
    if flag == 4:
        Yaw = 0


def filter_ccd_data(ccd_data):
    # 过滤掉所有大于1000的值
    filtered_data = [value if value <= 1000 else 0 for value in ccd_data]

    # 剔除突出的点
    smoothed_data = filtered_data[:]
    for i in range(1, len(filtered_data) - 1):
        if abs(filtered_data[i] - filtered_data[i - 1]) > 500 and abs(filtered_data[i] - filtered_data[i + 1]) > 500:
            smoothed_data[i] = (filtered_data[i - 1] + filtered_data[i + 1]) // 2

    return smoothed_data


# 选定1号定时器
pit1 = ticker(1)  # 关联采集接口 最少一个 最多八个
# 编码器关联,ccd关联
pit1.capture_list(encoder_l, encoder_r, ccd, key, imu)
# 关联 Python 回调函数
pit1.callback(time_pit_handler)
# 启动 ticker 实例 参数是触发周期 单位是毫秒
pit1.start(10)

from Tool import search, normal

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 主函数部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

while True:
    if ticker_flag:
        runTimes += 1
        if runTimes % 50 == 0:
            TrueRuntime += 1
            lcd.clear(0x0000)
            gc.collect()
            runTimes = 0
        if Statu == 1 and ccdThresholdDetermination == 0:
            # 初始确定CCD1和CCD2的阈值
            ccdThresholdDetermination = 1
            T1 = T2 = 0
            for _ in range(0, 100):
                originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
                originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
                T1 += threshold_determination(originalCcdData1)
                T2 += threshold_determination(originalCcdData2)
            T1 = 0.9 * (T1 / 100.0)
            T2 = 0.9 * (T2 / 100.0)

        if not Statu:
            ccdSuper = 0

        # 特殊元素处理，注意，元素处理只用ccd1（ccd_short）
        # 存在标记2023空悬，作用只在于退出长镜头循迹
        # 因为元素的特征总是ccd2先得到，所以我们使用ccd2为先决条件，当flag被提前进入时ccd2会自动退出
        # 长镜头识别十字，然后关断，只使用短镜头，知道短镜头识别到十字特征，十字路段结束
        if Statu:
            """国赛C语言改写的数据采集部分"""
            originalCcdData1 = ccd.get(0)
            originalCcdData2 = ccd.get(1)
            filteredCcdData1 = filter_ccd_data(originalCcdData1)  # 对originalCcdData进行滤波
            filteredCcdData2 = filter_ccd_data(originalCcdData2)
            trueValue1 = sum(filteredCcdData1)  # 计算ccd_data所有值的求和
            trueValue2 = sum(filteredCcdData2)

            max_peak1 = max_peak2 = 0
            for i in range(3, 128):  # 求出最大的差分值
                ccd_diff1[i] = originalCcdData1[i] - originalCcdData1[i - 3]
                if abs(ccd_diff1[i]) > max_peak1:
                    max_peak1 = abs(ccd_diff1[i])
            for i in range(3, 128):  # 求出最大的差分值
                ccd_diff2[i] = originalCcdData2[i] - originalCcdData2[i - 3]
                if abs(ccd_diff2[i]) > max_peak2:
                    max_peak2 = abs(ccd_diff2[i])

            left1, right1, searchMidline1, searchFlag1, rising_edge_cnt, falling_edge_cnt, rising_edge, falling_edge, ccd_diff = (
                search(originalCcdData1))

            last_left1, last_right1, left_last_find1, right_last_find1, reference_width1, road_type1 = (
                normal(originalCcdData1, left_last_find, right_last_find, rising_edge_cnt, falling_edge_cnt,
                       rising_edge, falling_edge, road_type, last_left, last_right, ccd_diff, threshold))

            normalMiddle1 = (last_left1 + last_right1) * 0.5
            normalCcdSuper = (64 - normalMiddle1 + 1)

            """原始数据采集部分"""
            key_1, key_2, key_3, Statu = Key_data(key)  # 读取按键数据
            ccd_data = read_ccd_data(originalCcdData1, originalCcdData2, T1, T2, crossFlag)  # 获取二值化后的ccd_data
            ccd_data1 = ccd_data[0]  # 近端ccd
            ccd_data2 = ccd_data[1]  # 远端ccd
            width1 = sum(1 for value in ccd_data1 if value == 1)
            width2 = sum(1 for value in ccd_data2 if value == 1)
            history1[1:] = history1[:-1]
            history1[0] = ccd_data1  # history1 存储了最近10次的ccd_data1值
            history2[1:] = history2[:-1]
            history2[0] = ccd_data2  # history2 存储了最近10次的ccd_data2值
            searchCcdSuper1 = searchMidline1 - 64
            last10Middle1 = [searchMidline1] + last10Middle1[:-1]  # 这个数组会存储最近十次的中线位置，并保证更新
            # 这个mid_line_long 的计算方法是，目前中线占10%权重，历史中线占90%权重，最后+n补充，目前n=0
            averageMedLine1 = 0.05 * searchMidline1 + 0.95 * sum(last10Middle1) / 10 + 0
            averageMedLineCcdSuper1 = averageMedLine1 - 64
            averageMedLineCcdSuper2 = averageMedLine2 - 64

            # 凡是区间太大的都切了
            if crossFlag == 17788 or crossFlag == 27788 or crossFlag == 57788:
                if width1 > 45:
                    ccd_data1_other = white(ccd_data1)
                else:
                    ccd_data1_other = ccd_data1

                if width2 > 50:
                    ccd_data2_other = white(ccd_data2)
                else:
                    ccd_data2_other = ccd_data2
            else:
                ccd_data1_other = ccd_data1
                ccd_data2_other = ccd_data2

            # 提取CCD1和CCD2切掉边缘后的边线和中线
            left_edge_short, right_edge_short, mid_line_short = find_road_edges(ccd_data1_other, flag, 1)
            left_edge_long, right_edge_long, mid_line_long = find_road_edges(ccd_data2_other, flag, 2)
            ccdSuper_short = mid_line_short - 64
            ccdSuper_long = mid_line_long - 64

            ccdSuper_short = 0.9 * ccdSuper_short + 0.1 * ccdSuper_long
            ccdSuper = ccdSuper_long  # 正常情况下采用CCD2循迹
            if abs(ccdSuper_long - ccdSuper_short) > 7 or flag != 0:
                ccdSuper = ccdSuper_short  # 车辆转入急弯时切换镜头，同时存在元素情况时也切换镜头
            """原始部分采集部分结束"""

            """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            十字路口识别部分
            此处调用了Get_CCD中的Search函数，通过寻找差分来实现边界搜寻
            最终找到十字的跳变特征，然后将crossFlag设置值
            注意，如果CCD1和CCD2能保持直线特征，则crossFlag会自行消除为0
            +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

            # Step0 直线计数
            if width1 < 50 and width2 < 50 and abs(averageMedLine1 - averageMedLine1) < 5:
                longNumber += 1
            else:
                longNumber = 0

            if longNumber == 50:
                tiaoBianCount2 = 0
                crossFlag = 0

            # Step1 当CCD1识别到直道,但是CCD2识别到全白
            if width2 > 80 and width1 < 50 and ccd_data2[30] == ccd_data2[40] == ccd_data2[50] ==ccd_data2[60] ==ccd_data2[70] ==ccd_data2[80] ==ccd_data2[90] ==1:
                crossFlag = 17788
                ccdSuper = ccdSuper_short

            # Step2 当CCD1 和 CCD2 均为全白
            if crossFlag == 17788:
                if width1 > 60 and width2 > 70:
                    crossFlag = 27788
                    ccdSuper = 0
                    time.sleep(0.3)
                    crossFlag = 37788

            # Step3 当CCD2识别到直道,但是CCD1识别到全白
            if crossFlag == 27788:
                if width1 > 80 and width2 < 60:
                    crossFlag = 37788
                    ccdSuper = ccdSuper_long
                    Yaw = 0

            # Step4 CCD1 和 CCD2 均判断为直道特征,此时进入十字圆环
            if ((crossFlag == 27788) and abs(mid_line_short - mid_line_long) < 10
                    and searchFlag1 == 0 and searchFlag2 == 0 and width1 < 50):
                crossFlag = 47788
                Yaw = 0

            # Step5 退出十字圆环
            if crossFlag == 47788 and Yaw >= 260:
                crossFlag = 0
                time.sleep(0.3)
                Yaw = 0

            if crossFlag == 17788:
                ccdSuper = ccdSuper_short

            if crossFlag == 27788:
                ccdSuper = min(ccdSuper_short, ccdSuper_long, key=abs)

            if crossFlag == 37788:
                ccdSuper = ccdSuper_short

            if crossFlag == 47788:
                ccdSuper = ccdSuper_short




            """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            圆环识别部分
            +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

            if flag != 0:
                crossFlag = 0
            # flag = Element_flag(ccd_data1, left_edge_short, right_edge_short, ahead, Yaw, ccd_data2)

            from Elements_CCD import is_circle2, Go_circle_now2, Wait_to_outCircle

            if chance > 0:
                if isCircle == 0:
                    isCircle, leftOrRight = is_circle2(width1, width2, left_edge_short, right_edge_short, left_edge_long,
                                                       right_edge_long)
                    if isCircle and flag != 4 and flag != 40 and flag != 5 and flag != 50 and flag != 501:
                        TrueRuntime = 0  # 第一次检测到isCircle，将计时装置归零
                        flag = 4
                        Yaw = 0

                if TrueRuntime >= 5:
                    # 连续500次都没有进入入环
                    isCircle = 0
                    flag = 0

                # 预入环模式
                if isCircle:
                    goCircle = Go_circle_now2(width1, width2, leftOrRight, left_edge_short, right_edge_short,
                                              left_edge_long, right_edge_long)
                if goCircle and flag == 4:
                    flag = 40

                if abs(Yaw) >= 40 and (flag == 40):
                    flag = 5

                if abs(Yaw) >= 230 and (flag == 5):
                    flag = 501

                if abs(Yaw) >= 330 and flag == 501:
                    flag = 50
                    TrueRuntime = 0

                if flag == 50 and TrueRuntime >= 2:
                    chance = chance - 1
                    flag = 0

                last_flag = flag
                if flag != last_flag:
                    realLastFlag = flag  # realLastFlag存储上一次与当前flag不同时候的flag


            """
            斑马线停车
            停车flag为10


            if abs(ccdSuper) <= 10:
                number1 = count_transitions(originalCcdData1)
                number2 = count_transitions(originalCcdData2)
                if number2 >= 5 and width1 < 60:
                    flag = 10
            """

            if width1 == 0 and width2 == 0:
                stoptime += 1
                if stoptime == 50:
                    flag = 10
            else:
                stoptime = 0

            # 蜂鸣器简单调用
            # 预备阶段响铃

            if flag == 4:
                BEEP.value(True)
            else:
                BEEP.value(False)



        debugMode = 0  # Debug模式，如果启用需要在这里设置为1，启用后每100次While的执行就会打印一次数据
        if debugMode:
            if runTimes % 100 == 0:
                print(f"ccd_data1: {ccd_data1[54:74]}")
                print(f"ccd_data2: {ccd_data2[54:74]}")
                print(f"flag: {flag}")
                print(f"mid_line_short: {mid_line_short}")
                print(f"mid_line_long: {mid_line_long}")
                print(f"realLastFlag： {realLastFlag}")

        lastCcdSuper = ccdSuper  # 上一次的误差
        gc.collect()
        ticker_flag = False  # 定时器关断标志

    """屏幕显示部分"""
    key_1, key_2, key_3, Statu = Key_data(key)
    if key_1:
        if displayCheck == 5:
            displayCheck = 0
        else:
            print("key1")
            displayCheck += 1
            if menu == 3:
                print("正在添加CCD数据，请勿操作")
                originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
                originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
                user_data1.append(originalCcdData1)
                user_data2.append(originalCcdData2)
                print("CCD数据添加完成，可以继续操作")

    if key_2:
        print("key2")
        if displayCheck != 0:
            displayCheck -= 1

    if key_3:
        print("key3")
        if menu == 3:
            print("正在将存储到的数据写入user_data1.txt 和 user_data2.txt")
            os.chdir("/flash")
            user_file = io.open("user_data1.txt", "w+")
            # 将指针移动到文件头 0 偏移的位置 这个函数参照 Python 的 File 模块
            user_file.seek(0, 0)
            i = 0
            user_file.write(f"ccd_data1:\n")
            for ccd_data1 in user_data1:

                user_file.write(f"\n[")
                for item in ccd_data1:
                    if item == len(ccd_data1) - 1:
                        user_file.write("%d" % item)
                    else:
                        user_file.write("%d," % item)
                user_file.write(f"],")

            user_file.flush()  # 将缓冲区数据写入到文件 清空缓冲区 相当于保存指令
            user_file.close()  # 最后将文件关闭即可

            user_file = io.open("user_data2.txt", "w+")
            # 将指针移动到文件头 0 偏移的位置 这个函数参照 Python 的 File 模块
            user_file.seek(0, 0)
            i = 0
            user_file.write(f"ccd_data2:\n")
            for ccd_data2 in user_data2:

                user_file.write(f"\n[")
                for item in ccd_data2:
                    if item == len(ccd_data2) - 1:
                        user_file.write("%d" % item)
                    else:
                        user_file.write("%d," % item)
                user_file.write(f"],")

            user_file.flush()  # 将缓冲区数据写入到文件 清空缓冲区 相当于保存指令
            user_file.close()  # 最后将文件关闭即可

        lcd.clear(0x0000)
        if displayCheck == 1 and menu == 0:
            print("跳转到速度设定菜单了")
            menu = 1
            displayCheck = 0

        if displayCheck == 2 and menu == 0:
            print("跳转到元素展示菜单1了")
            menu = 2
            displayCheck = 0

        if displayCheck == 3 and menu == 0:
            print("跳转到数据采集菜单了")
            menu = 3
            displayCheck = 999

        if displayCheck == 4 and menu == 0:
            print("跳转到元素展示菜单2了")
            menu = 4
            displayCheck = 999

        if displayCheck == 5 and menu == 0:
            print("跳转到元素展示菜单2了")
            menu = 5
            displayCheck = 999

        if displayCheck == 1 and menu == 1:
            print("速度设置为60了")
            speedSet = 60
            menu = 2
        if displayCheck == 2 and menu == 1:
            print("速度设置为80了")
            speedSet = 80
            menu = 2
        if displayCheck == 3 and menu == 1:
            print("速度设置为90了")
            speedSet = 90
            menu = 2

        lcd.clear(0x0000)

    """屏幕显示部分"""
    """初级菜单(1级)"""
    if displayCheck == 0 and menu == 0:
        display_strings(lcd, ["flag ", "Choose Speed ", "Elements ", "Data Save", "Elements2", "Circle"],
                        [flag, 0, 0, 0, 0, 0])

    if displayCheck == 1 and menu == 0:
        display_strings(lcd, ["flag ", "Choose Speed ", "Elements ", "Data Save", "Elements2", "Circle"],
                        [flag, 1, 0, 0, 0, 0])  # menu = 1

    if displayCheck == 2 and menu == 0:
        display_strings(lcd, ["flag ", "Choose Speed ", "Elements ", "Data Save", "Elements2", "Circle"],
                        [flag, 0, 1, 0, 0, 0])  # menu = 2

    if displayCheck == 3 and menu == 0:
        display_strings(lcd, ["flag ", "Choose Speed ", "Elements ", "Data Save", "Elements2", "Circle"],
                        [flag, 0, 0, 1, 0, 0])  # menu = 3

    if displayCheck == 4 and menu == 0:
        display_strings(lcd, ["flag ", "Choose Speed ", "Elements ", "Data Save", "Elements2", "Circle"],
                        [flag, 0, 0, 0, 1, 0])  # menu = 4

    if displayCheck == 5 and menu == 0:
        display_strings(lcd, ["flag ", "Choose Speed ", "Elements ", "Data Save", "Elements2", "Circle"],
                        [flag, 0, 0, 0, 0, 1])  # menu = 5

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
        display_strings(lcd,
                        ["ccdSuper1", "ccdSuper2", "ccdSuper", "angle", "flag", "Yaw", "crossFlag", "crossSuper",
                         "mid_line_short", "mid_line_long", "runTimes"],

                        [ccdSuper_short, ccdSuper_long, ccdSuper, angle, flag, Yaw, crossFlag, crossSuper,
                         mid_line_short, mid_line_long, runTimes])

    """数据采集菜单(2级)"""
    if menu == 3:
        display_strings(lcd,
                        ["Press confirm", "CCD1: ", "CCD2: "],
                        [0, len(user_data1), len(user_data2)])

    """数据展示菜单(2级)"""
    if menu == 4:
        smallCcd = ''.join(map(str, ccd_data1[::12]))
        bigCcd = ''.join(map(str, ccd_data2[::12]))
        display_strings(lcd,
                        ["flag", "crossFlag", "searchFlag", "searchFlag2", "ccd1", "ccd2", "width1", "width2", "T1",
                         "T2",
                         "searchMidline1", "normalCcdSuper", "number"],
                        [flag, crossFlag, searchFlag1, searchFlag2, smallCcd, bigCcd, width1, width2, T1, T2,
                         searchMidline1, normalCcdSuper, number])

    """数据展示菜单(2级)"""
    if menu == 5:
        display_strings(lcd,
                        ["width1", "width2", "left1", "right1", "left2", "right2", "isCircle"],
                        [width1, width2, left_edge_short, right_edge_short, left_edge_long, right_edge_long, isCircle]
                        )

    """ 屏幕显示部分结束"""
    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()



