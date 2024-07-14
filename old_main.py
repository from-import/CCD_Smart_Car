# 下面这一行当调试代码的时候取消掉注释，方便找语法错误所在
# from deleteME import IMU660RA, Pin, TSL1401, WIRELESS_UART, MOTOR_CONTROLLER, encoder, PWM, KEY_HANDLER, ticker
from machine import *
from smartcar import *
from seekfree import *
from display import *
import gc
import time
from CCD_Tool import *
from Find_Circle import *
from Old_Get_CCD import read_ccd_data, threshold_determination
from Old_Motor_Origin import control_motor, control_encoder
from Old_Motor_Servo import set_servo_angle, duty_angle
from Old_Screen import init_Screen

"""SMGG.Tips:
main主要进行初始化，后面的算法处理单独封装，以达到可读，参数调整方便的效果"""
# 核心板上 C4 是 LED
led1 = Pin('C4', Pin.OUT, pull=Pin.PULL_UP_47K, value=True)
# 开发板上的 C19 是拨码开关
end_switch = Pin('C19', Pin.IN, pull=Pin.PULL_UP_47K, value=True)
end_state = end_switch.value()
# 主板上 C9 是蜂鸣器
BEEP = Pin('C9', Pin.OUT, pull=Pin.PULL_UP_47K, value=False)

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 初始化部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

"""
CCD 初始化
调用 TSL1401 模块获取 CCD 实例,参数是采集周期 调用多少次 capture/read 更新一次数据
默认参数为 1 调整这个参数相当于调整曝光时间倍数,这里填了 10 代表 10 次 capture/read 调用才会更新一次数据
"""
ccd = TSL1401(1)  # 调用 TSL1401 模块获取 CCD 实例,参数是采集周期 调用多少次 capture/read 更新一次数据
ccd.set_resolution(TSL1401.RES_12BIT)  # 调整 CCD 的采样精度为 12bit
# wireless = WIRELESS_UART(460800)  # 实例化 WIRELESS_UART 模块 参数是波特率
# wireless.send_str("Hello World.\r\n")  # 测试无线正常
# time.sleep_ms(500)

"""
电机 Motor 初始化,示例调用:
control_motor(motor_l, motor_r)  # 传入左右电机控制对象
"""
motor_l = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C25_DIR_C27, 13000, duty=0, invert=False)
motor_r = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C24_DIR_C26, 13000, duty=0, invert=True)

"""
Encoder 初始化
control_encoder(encoder_l, encoder_r)
"""
encoder_l = encoder("D0", "D1", False)
encoder_r = encoder("D2", "D3", True)

"""
舵机 Motor_Servo 初始化，示例调用：
set_servo_angle(pwm_servo)
"""
duty_servo = int(duty_angle(101.0))  # 初始化舵机打角 学习板上舵机接口为 C20
pwm_servo = PWM("C20", 300, duty_u16=duty_servo)  # 调用 machine 库的 PWM 类实例化一个 PWM 输出对象

"""
Screen 初始化
init_Screen()
"""
lcd = init_Screen()

"""
Key 初始化
"""
key = KEY_HANDLER(10)  # 实例化 KEY_HANDLER 模块 参数是按键扫描周期

"""
flag 初始化
"""

ticker_flag = False  # 定时器数据建立
ticker_count = 0  # 时间延长标志（使用方法见encoder例程）

"""
imu 初始化
"""
# 调用 IMU660RA 模块获取 IMU660RA 实例
imu = IMU660RA()

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 初始化部分（舵机：Middle:101，LeftMax:117，RightMax:88）
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
ccdSuper = angle = key_4 = Key_1 = Key_2 = Statu = lastLastWidth1 = isCircleNow = crossingTime = outCrossingTime = 0
isCrossing = roadWidth1 = roadWidth2 = outCircleTimes = alreadyOutCircleTimes = isCircleNowTimes = 0
left_edge = right_edge = barrierLocation = alreadyOutCircle = lastWidth1 = crossing = outCircle = checkCircle = 0
goCircle = findCircleTimes = barrierNow = roadWidth = midline1EqualsMidline2 = 0
ccdThresholdDetermination = T1 = T2 = Yaw = lastMid_line2 = outCrossingError = 0
midline2 = midline1 = filled_mid_line = lastMid_line1 = lastLastMid_line1 = 64
ccdAllData1 = ccd_data1 = ccdAllData2 = ccd_data2 = []
fiveTimesRoadWidth1 = fiveTimesRoadWidth2 = fiveTimesMidline1 = fiveTimesMidline2 = [0, 0, 0, 0, 0]
last10Middle1 = last10Middle2 = [0] * 10
trueValue1 = trueValue2 = 0

flag = "straight"
speedFlag = "medium"
leftOrRight = "nothing"
""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 定时器内容编写
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

runpltTimes = 0
# 定义一个回调函数（定时运行程序可以写在里面）
def time_pit_handler(time):
    global ticker_flag, ccdSuper, angle, key_4, Statu, flag, runpltTimes
    ticker_flag = True
    control_encoder(encoder_l, encoder_r)  # encoder
    angle = set_servo_angle(pwm_servo, ccdSuper, flag)  # 舵机运行程序
    control_motor(motor_l, motor_r, ccdSuper, Statu, flag, speedFlag)  # 电机运行程序


pit1 = ticker(1)  # 选定1号定时器:关联采集接口,最少一个,最多八个
pit1.capture_list(encoder_l, encoder_r, ccd, key)  # 编码器关联,ccd关联
pit1.callback(time_pit_handler)  # 关联 Python 回调函数
pit1.start(10)  # 启动 ticker 实例 参数是触发周期 单位是毫秒

"""
pit2 = ticker(2)  # 选定2号定时器
pit2.callback(time_pit_handler2)  # 关联 Python 回调函数
pit2.start(30)  # 启动 ticker 实例 参数是触发周期 单位是毫秒
"""


""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
曲率 对照表： [上上次中线，上次中线，这次中线] = 曲率
[64,63,60] = 2
[64,55,40] = 6
[64,52,30] = 10
[64,40,0] = 16

flag 对照表:
speedUP： 直线加速
straight：直线
isCircle：即将入环，舵机保持101(电机通过单边循迹确定修正值)
goLeftCircle / goRightCircle：左/右强制入环：舵机强制打角
outLeftCircle / outRightCircle：左/右强制出环：舵机强制打角
alreadyOutCircle：刚出环，需要通过ccd2循迹
crossing：十字路口
onCrossing:十字路口中间
outCrossing:刚出十字路口
lv1Bend：低级弯道
lv2Bend：初级弯道
lv3Bend：高级弯道
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
runTimes = 0
while True:
    if ticker_flag:
        runTimes += 1
        """基本数据采集部分"""
        originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
        originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
        trueValue1 = sum(originalCcdData1)  # 计算ccd_data1值为 1 的元素总数
        trueValue2 = sum(originalCcdData2)  # 计算ccd_data2值为 1 的元素总数

        ccd1_average = sum([originalCcdData1[i] for i in [10, 20, 40, 50, 60, 70, 80, 100, 110]]) // 9
        ccd2_average = sum([originalCcdData2[i] for i in [10, 20, 40, 50, 60, 70, 80, 100, 110]]) // 9
        ProcessedCCD = read_ccd_data(originalCcdData1, originalCcdData2, T1, T2)
        ccd_data1 = ProcessedCCD[0]  # 处理后的二值化CCD数据
        ccd_data2 = ProcessedCCD[1]  # 处理后的二值化CCD数据
        trueWidth1 = sum(value == 1 for value in ccd_data1)  # 计算ccd_data1值为 1 的元素总数
        trueWidth2 = sum(value == 1 for value in ccd_data2)  # 计算ccd_data2值为 1 的元素总数
        lastLastMid_line1 = lastMid_line1  # 上上次的中线位置，计算曲率用
        lastMid_line1 = midline1  # 上次的中线位置
        lastMid_line2 = midline2  # 上次的中线位置
        last10Middle1 = [midline1] + last10Middle1[:-1]
        last10Middle2 = [midline2] + last10Middle2[:-1]
        left_edge1, right_edge1, midline1 = find_road_edges(ccd_data1, midline1)  # 计算左右边界与中线
        left_edge2, right_edge2, midline2 = find_road_edges(ccd_data2, midline2)  # 计算左右边界与中线
        ccdSuper1 = midline1 - 64  # CCD1的误差值
        ccdSuper2 = midline2 - 64  # CCD2的误差值
        ccdSuper = ccdSuper1  # 权重经验公式，来自均速3.8m/s的CCD车
        lastWidth1 = roadWidth1  # 上一次CCD1的道路宽度，用于判断避障和环中点
        lastWidth2 = roadWidth2  # 上一次CCD2的道路宽度，用于判断避障和环中点
        roadWidth1 = abs(left_edge1 - right_edge1)  # 这一次的道路宽度
        roadWidth2 = abs(left_edge2 - right_edge2)  # 这一次的道路宽度
        fiveTimesRoadWidth1 = [roadWidth1] + fiveTimesRoadWidth1[:-1]  # 最新五次的CCD1的道路宽度
        fiveTimesRoadWidth2 = [roadWidth2] + fiveTimesRoadWidth2[:-1]  # 最新五次的CCD2的道路宽度
        fiveTimesMidline1 = [midline1] + fiveTimesMidline1[:-1]  # 最新五次的CCD1的道路宽度
        fiveTimesMidline2 = [midline2] + fiveTimesMidline2[:-1]  # 最新五次的CCD2的道路宽度
        curvature = abs(calculate_curvature(lastLastMid_line1, lastMid_line1, midline1))  # 赛道曲率
        """
        if curvature < 5:
            flag = "straight"
        elif curvature > 5:
            flag = "lv1Bend"
        elif curvature > 10:
            flag = "lv2Bend"
        elif curvature > 15:
            flag = "lv3Bend"

        # 直线加速模块,如果较远的ccd采集到的数据也为直线,则进入加速逻辑,直到较远的ccd采集到的中线发生较大偏移
        if abs(ccdSuper2) < 6 and flag == "straight":
            flag = "speedUP"
        if abs(ccdSuper2) >= 6 and flag == "speedUP":
            flag = "straight"
        """
        if abs(midline1 - midline2) <= 5:  # 直线的判别，连续五次都找到直线则判断为目前处于直线状态
            midline1EqualsMidline2 += 1
            if midline1EqualsMidline2 == 5:
                flag = "straight"
        else:
            midline1EqualsMidline2 = 0

        # 起跑线检测模块
        if find_start_line(ccd_data1):
            Statu = 0

        """
        十字路口判别模块,分为三个区间
        step1：CCD1直道，CCD2全白
        step2：CCD1全白,CCD2全白
        step3：CCD1全白，CCD2直道
        """
        isCrossing = detect_intersection(ccd_data1, ccd_data2, lastMid_line1)
        if isCrossing:
            flag = "crossing"

        onCrossing = on_detect_intersection(ccd_data1, ccd_data2)
        if onCrossing:
            flag = "onCrossing"
            if outCrossingError == 0:
                outCrossingError = lastLastMid_line1

        outCrossing = out_detect_intersection(ccd_data1, ccd_data2, lastMid_line1, lastMid_line2)
        if outCrossing:
            flag = "outCrossing"

        if flag == "crossing":
            ccdSuper = ccdSuper1
        if flag == "onCrossing":
            ccdSuper = outCrossingError
        if flag == "outCrossing":
            ccdSuper = ccdSuper1

        """环岛部分
        if leftOrRight == "nothing":  # 防止在找到入环标志后，在后续的跑道中再次误判圆环
            realIsCircleNow, realLeftOrRight = is_circle(ccd_data1, ccd_data2)
            if realIsCircleNow:
                isCircleNowTimes += 1
                if isCircleNowTimes == 3:  # 连续三次检测到环，则设置为环
                    isCircleNow, leftOrRight = is_circle(ccd_data1, ccd_data2)
                    # isCircleNow 为是否检测到环，leftOrRight为左环还是右环
                    isCircleNowTimes = 0
            else:
                isCircleNowTimes = 0

        # 第一步，寻找入环标志：左侧和中间同时出现白色区域，即白黑白
        if (isCircleNow == True) and (goCircle == False):
            # 防止二次判环将goCircle的标志位刷掉，后续赛道存在多个环可以更改此处逻辑
            # 如果goCircle == 1，代表在之前已经检测到环
            checkCircle = 1  # 将checkCircle置1，代表进入入环状态
            flag = "isCircle"
            time.sleep(2)  # 睡眠1s来防止刚检测到入环标志就判定为入环

        # 第二步，找到环中点，进行强制打角
        if checkCircle:
            filled_midline1 = fill_line(ccd_data1, leftOrRight, checkCircle)  # 确定补线后的中线
            ccdSuper = filled_midline1 - 64  # 补线状态下的误差值,覆盖之前的ccdSuper,防止被前半段圆环误判左转
            print(f"已进入入环状态，此时补线后的中线:{filled_midline1}")
            goCircle = Go_circle_now(ccd_data1, ccd_data2, lastWidth1)  # 如果检测到环中点，将goCircle置为True
            if goCircle:
                # 在完成入环后,进入基础的循迹逻辑,环岛运行过程中一般是丢一边线的单边循迹,通过强制打角即可进入环岛
                if leftOrRight == "left":
                    flag = "goLeftCircle"
                    checkCircle = 0
                if leftOrRight == "right":
                    flag = "goRightCircle"
                    checkCircle = 0
                time.sleep(2)
                flag = "straight"

        # 第三步，在完成环岛动作后，一旦找到十字路口的样式,代表找到了出环位置(左右均全白),此时强制打角出环,然后调用ccd_data2进行直线循迹
        outCircle = (detect_intersection(ccd_data1, ccd_data2, lastMid_line1))  # 十字路口判别模式
        if outCircle and goCircle:
            outCircleTimes += 1
            if outCircleTimes == 2:
                print("找到十字路口")
                alreadyOutCircle = 1  # 每次只进行一次出环动作
                goCircle = 0  # 防止多次识别为出环
                if leftOrRight == "left":
                    flag = "outLeftCircle"
                if leftOrRight == "right":
                    flag = "outRightCircle"
                time.sleep(2)
                outCircleTimes = 0

        # 第四步，切换ccd2来读取数据(ccd2读的更远，不会被干扰)，确保成功进入直道
        if leftOrRight != "nothing" and alreadyOutCircle:  # 已经完成了入环判断，入环打角，出环打角
            flag = "alreadyOutCircle"
            ccdSuper = ccdSuper2  # 切换ccd2读取的数据来循迹，因为ccd1会被环岛白色区域误判
            if abs(ccdSuper) < 8 and abs(ccdSuper2) < 8:
                leftOrRight = "alreadyFinishedCircle"  # 当两个ccd都读到直道，将leftOrRight清除，退出环岛逻辑

        # 第五步，当ccd1和ccd2都读到了直道，说明已经完全出环
        if abs(roadWidth1 - roadWidth2 <= 10):
            alreadyOutCircleTimes = alreadyOutCircleTimes + 1
            if alreadyOutCircleTimes == 3:
                flag = "straight"
                alreadyOutCircleTimes = 0
        """

        # 按键逻辑
        key_data = key.get()  # 获取按键数据
        key_1, key_2, key_3, key_4 = key_data  # 解包按键数据

        if key_data[0]:
            ccdAllData1.append(ccd_data1)
            ccdAllData2.append(ccd_data2)
            print(f"已经将当前的ccd1和ccd2分别添加到列表中,共添加了{len(ccdAllData1)}次")
            key.clear(1)

        if key_data[1]:
            # 当2被按下，打印之前全部存储的ccd_data
            print("ccd_data1:")
            print(ccdAllData1)
            print("\nccd_data2:")
            print(ccdAllData2)
            key.clear(2)

        if key_data[2]:
            # 暂时无用处
            key.clear(3)

        if key_data[3]:
            # 按下后不执行key.clear(4)，电机启动，可一直保持key_4 == 1
            key_4 = 1  # 按键按下后将 key_4 设置为 1
            Statu = 1

        if Statu == 0:
            flag = "stop"

        # 初始确定CCD1和CCD2的阈值T1和T2
        if Statu == 1 and ccdThresholdDetermination == 0:
            ccdSuper = 0
            ccdThresholdDetermination = 1
            T1 = T2 = 0
            for _ in range(0, 20):
                originalCcdData1 = ccd.get(0)  # 读取原始的CCD数据
                originalCcdData2 = ccd.get(1)  # 读取原始的CCD数据
                T1 += threshold_determination(originalCcdData1)
                T2 += threshold_determination(originalCcdData2)
            flag = "straight"
            T1 = T1 / 20.0
            T2 = T2 / 20.0
            print(f"T1:{T1},T2:{T2}")
            ccdSuper = 0

        if runTimes % 10000 == 0:
            print(f"flag : {flag}")
            print(f"offset={ccdSuper:.2f}.")
            print(f"midline1={midline1:.2f}.")
            print(f"roadWidth={roadWidth1:.2f}.")
            print(f"leftOrRight: {leftOrRight}")
            print(f"isCircleNow={isCircleNow:.2f}.")
            print(f"goCircle={goCircle:.2f}.")
            print(f"isCrossing={isCrossing:.2f}.")
            print(f"alreadyOutCircle={alreadyOutCircle:.2f}.")
            print(f"barrierLocation={barrierLocation}.")
            print(f"ccd1:{ccd_data1[50:64]}")
            print(f"ccd2:{ccd_data2[50:64]}")


        ticker_flag = False  # 定时器关断标志



    # 屏幕显示
    lcd.str12(0, 13 * 0, f"flag : {flag}", 0xFFFF)
    lcd.str12(0, 13 * 1, "T1={:>.2f}.".format(T1), 0xFFFF)
    lcd.str12(0, 13 * 2, "T2={:>.2f}.".format(T2), 0xFFFF)
    """
    lcd.str12(0, 13 * 1, "offset={:>.2f}.".format(ccdSuper), 0xFFFF)
    lcd.str12(0, 13 * 2, "midline1={:>.2f}.".format(midline1), 0xFFFF)
    
    lcd.str24(0, 24 * 3, "roadWidth={:>.2f}.".format(roadWidth1), 0xFFFF)
    lcd.str24(0, 24 * 4, f"leftOrRight:{leftOrRight}", 0xFFFF)
    lcd.str24(0, 24 * 5, "isCircleNow={:>.2f}.".format(isCircleNow), 0xFFFF)
    lcd.str24(0, 24 * 6, "goCircle={:>.2f}.".format(goCircle), 0xFFFF)
    lcd.str24(0, 24 * 7, "isCrossing={:>.2f}.".format(isCrossing), 0xFFFF)
    lcd.str24(0, 24 * 8, "alreadyOutCircle={:>.2f}.".format(alreadyOutCircle), 0xFFFF)
    lcd.str24(0, 24 * 9, f"barrierLocation={barrierLocation}.", 0xFFFF)
    """
    gc.collect()

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break




