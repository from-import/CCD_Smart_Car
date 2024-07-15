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
last10Middle1 = last10Middle2 = [0] * 10
trueValue1 = trueValue2 = 0
lastCcdSuper = 0
history1 = [[0] * 128 for _ in range(50)]
history2 = [[0] * 128 for _ in range(50)]
user_data1 = []
user_data2 = []
crossSuper = 0
averageMedLine1 = averageMedLine2 = 64
ccd_data1 = ccd_data2 = originalCcdData1 = originalCcdData2 = [0] * 128
crossFlag = 0
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


""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 主函数部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

while True:
    if (ticker_flag):
        runTimes += 1
        if runTimes % 200 == 0:
            lcd.clear(0x0000)
            runTimes = 0
            # print("主函数已运行3000次，目前的赛道图片截取到 history1 and history2")
            # write_ccd_in_txt(history1, "history1")
            # write_ccd_in_txt(history2, "history2")

        if Statu == 1 and ccdThresholdDetermination == 0:
            # 初始确定CCD1和CCD2的阈值
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
            key_1, key_2, key_3, Statu = Key_data(key)  # 读取按键数据
            originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
            originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
            trueValue1 = sum(originalCcdData1)  # 计算ccd_data1 所有值的求和
            trueValue2 = sum(originalCcdData2)  # 计算ccd_data2 所有值的求和
            ccd_data = read_ccd_data(originalCcdData1, originalCcdData2, T1, T2, crossFlag)  # 获取二值化后的ccd_data

            ccd_data1 = ccd_data[0]  # 近端ccd
            ccd_data2 = ccd_data[1]  # 远端ccd
            history1[1:] = history1[:-1]
            history1[0] = ccd_data1  # history1 存储了最近100次的ccd_data1值
            history2[1:] = history2[:-1]
            history2[0] = ccd_data2  # history2 存储了最近100次的ccd_data2值
            left_edge_short, right_edge_short, mid_line_short = find_road_edges(ccd_data1, flag, 1)  # 提取CCD1的边线和中线
            left_edge_long, right_edge_long, mid_line_long = find_road_edges(ccd_data2, flag, 2)  # 提取CCD2的边线和中线
            last10Middle1 = [mid_line_short] + last10Middle1[:-1]  # 这个数组会存储最近十次的中线位置，并保证更新
            last10Middle2 = [mid_line_long] + last10Middle2[:-1]  # 这个数组会存储最近十次的中线位置，并保证更新
            # 这个mid_line_long 的计算方法是，目前中线占10%权重，历史中线占90%权重，最后+n补充，目前n=0
            averageMedLine1 = 0.01 * mid_line_short + 0.99 * sum(last10Middle1) / 10 + 0
            averageMedLine2 = 0.01 * mid_line_long + 0.99 * sum(last10Middle2) / 10 + 0
            ccdSuper_short = mid_line_short - 64
            ccdSuper_long = mid_line_long - 64

            ccdSuper = ccdSuper_long  # 正常情况下采用CCD2循迹
            if abs(ccdSuper_long - ccdSuper_short) > 5 or flag != 0:
                ccdSuper = ccdSuper_short  # 车辆转入急弯时切换镜头，同时存在元素情况时也切换镜头

            """十字路口判别"""
            # Step1 当CCD1识别到直道,但是CCD2识别到全白
            if trueValue1 < 60000 and trueValue2 > 70000 and abs(mid_line_short - 64) <= 10:
                crossFlag = 17788
                ccdSuper = ccdSuper_short

            # Step2 当CCD1 和 CCD2 均为全白
            if crossFlag == 17788:
                if trueValue1 > 70000 and trueValue2 > 70000:
                    crossFlag = 27788

            # Step3 当CCD2识别到直道,但是CCD1识别到全白
            if trueValue2 < 60000 and trueValue1 > 70000 and abs(mid_line_long - 64) <= 10:
                crossFlag = 37788
                ccdSuper = ccdSuper_long

            # Step4 CCD1 和 CCD2 均判断为直道特征
            if (crossFlag == 17788 or crossFlag == 27788 or crossFlag == 37788) and trueValue1 < 70000 and trueValue2 < 70000:
                crossFlag = 0

            if crossFlag == 17788:
                ccdSuper = ccdSuper_short

            if crossFlag == 27788:

                ccdSuper = -0.8 * ccdSuper_short

            if crossFlag == 37788:
                ccdSuper = ccdSuper_long

            # 如果长时间保持直线状态,更新flag为直线
            if trueValue1 < 60000 and trueValue2 < 60000 and abs(mid_line_short - mid_line_long) <= 10:
                num += 1
                if num > 10:
                    flag = 0
            else:
                num = 0




        # 蜂鸣器简单调用
        # 预备阶段响铃
        if flag == 50:
            BEEP.value(True)
        else:
            BEEP.value(False)

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

        lastCcdSuper = ccdSuper  # 上一次的误差
        ticker_flag = False  # 定时器关断标志











    """屏幕显示部分"""
    key_1, key_2, key_3, Statu = Key_data(key)
    if key_1:
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
            print("跳转到元素展示菜单了")
            menu = 2
            displayCheck = 0

        if displayCheck == 3 and menu == 0:
            print("跳转到数据采集菜单了")
            menu = 3
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

    """初级菜单(1级)"""
    if displayCheck == 0 and menu == 0:
        display_strings(lcd, ["Menu1 ", "Choose Speed ", "Show Elements ", "Data Save"], [1.11, 0, 0, 0])

    if displayCheck == 1 and menu == 0:
        display_strings(lcd, ["Menu1 ", "Choose Speed ", "Show Elements ", "Data Save"], [0, 1.11, 0, 0])  # menu = 1

    if displayCheck == 2 and menu == 0:
        display_strings(lcd, ["Menu1 ", "Choose Speed ", "Show Elements ", "Data Save"], [0, 0, 1.11, 0])  # menu = 2

    if displayCheck == 3 and menu == 0:
        display_strings(lcd, ["Menu1 ", "Choose Speed ", "Show Elements ", "Data Save"], [0, 0, 0, 1.11])  # menu = 3

    """速度设定菜单(2级)"""
    if displayCheck == 0 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [1.11, 0, 0, 0])

    if displayCheck == 1 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [0, 1.11, 0, 0])

    if displayCheck == 2 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [0, 0, 1.11, 0])

    if displayCheck == 3 and menu == 1:
        display_strings(lcd, ["Choose Speed", "60 ", "80", "90"], [0, 0, 0, 1.11])

    """数据展示菜单(2级)"""
    if menu == 2:
        display_strings(lcd, ["ccdSuper1","ccdSuper2", "ccdSuper", "angle", "flag", "Yaw", "trueValue1", "trueValue2","crossFlag","crossSuper"],
                        [ccdSuper_short,ccdSuper_long,ccdSuper, angle, flag, Yaw, int(trueValue1),
                         int(trueValue2),crossFlag,crossSuper])

    """数据采集菜单(2级)"""
    if menu == 3:
        display_strings(lcd, ["Press confirm", "CCD1: ", "CCD2: "],
                        [0, len(user_data1), len(user_data2)])

    # 通过 wave 接口显示数据波形 (x,y,width,high,data,data_max)
    # lcd.wave(0, 0, 128, 64, ccd_data1, max=200)
    # lcd.wave(0, 64, 128, 64, ccd_data2, max=200)

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()




