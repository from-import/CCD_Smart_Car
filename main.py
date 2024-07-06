from machine import *
from smartcar import *
from seekfree import *
from display import *
import gc
import time
from Find_Barrier import find_barrier
from Get_CCD import *
from CCD_Tool import *
from Find_Circle import *
from Old_Motor_Origin import control_motor, control_encoder
from Old_Motor_Servo import set_servo_angle, duty_angle
from Screen import init_Screen

# 删除下面这一行
from deleteME import Pin, TSL1401, WIRELESS_UART, MOTOR_CONTROLLER, encoder, PWM, KEY_HANDLER, ticker

"""SMGG.Tips:
main主要进行初始化，后面的算法处理单独封装，以达到可读，参数调整方便的效果"""
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
调用案例：ccd_data1, ccd_data2 = read_ccd_data(ccd)
"""
ccd = TSL1401(1)  # 调用 TSL1401 模块获取 CCD 实例,参数是采集周期 调用多少次 capture/read 更新一次数据
ccd.set_resolution(TSL1401.RES_12BIT)  # 调整 CCD 的采样精度为 12bit
wireless = WIRELESS_UART(460800)  # 实例化 WIRELESS_UART 模块 参数是波特率
wireless.send_str("Hello World.\r\n")  # 测试无线正常
time.sleep_ms(500)

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

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 初始化部分（舵机：Middle:101，LeftMax:117，RightMax:88）
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
ccdSuper = angle = key_4 = Key_1 = Key_2 = Statu = isCircleNow =roadWidth1 = roadWidth2 = 0
left_edge = right_edge = barrierLocation = alreadyOutCircle = outCircle = checkCircle = goCircle = findCircleTimes = barrierNow = roadWidth = 0
mid_line2 = mid_line = filled_mid_line = 64
ccdAllData1 = ccd_data1 = ccdAllData2 = ccd_data2 = []

flag = "Straight"
leftOrRight = "nothing"
""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 定时器内容编写
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


# 定义一个回调函数（定时运行程序可以写在里面）
def time_pit_handler(time):
    global ticker_flag, ccdSuper, angle, key_4, Statu, flag
    ticker_flag = True

    control_encoder(encoder_l, encoder_r)  # encoder
    control_motor(motor_l, motor_r, key_4, ccdSuper, Statu)  # 电机运行程序
    angle = set_servo_angle(pwm_servo, ccdSuper)  # 舵机运行程序


pit1 = ticker(1)  # 选定1号定时器:关联采集接口,最少一个,最多八个
pit1.capture_list(encoder_l, encoder_r, ccd, key)  # 编码器关联,ccd关联
pit1.callback(time_pit_handler)  # 关联 Python 回调函数
pit1.start(10)  # 启动 ticker 实例 参数是触发周期 单位是毫秒

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 主函数部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

while True:
    if ticker_flag:
        key_data = key.get()  # 获取按键数据
        key_1, key_2, key_3, key_4 = key_data  # 解包按键数据

        if key_data[0]:
            # 当1被按下，存储当前的全部ccd_data到列表中
            print(f"已经将当前的ccd1和ccd2分别添加到列表中,共添加了{len(ccdAllData1)}次")
            ccdAllData1.append(ccd_data1)
            ccdAllData2.append(ccd_data2)
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
            print("key3 = {:>6d}.".format(key_data[2]))
            key.clear(3)
        if key_data[3]:
            # 按下后不执行key.clear(4)，电机启动，可一直保持key_4 == 1
            key_4 = 1  # 按键按下后将 key_4 设置为 1
            Statu = 1

        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        Tips: 基本数据采集部分
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        ccd_data1, ccd_data2 = read_ccd_data(ccd)  # 读取CCD值，存储到数组
        left_edge, right_edge, mid_line = find_road_edges(ccd_data1, mid_line)  # 计算左右边界与中线
        left_edge2, right_edge2, mid_line2 = find_road_edges(ccd_data2, mid_line2)  # 计算左右边界与中线

        # ccdSuper>0,需要右转
        ccdSuper1 = mid_line - 64  # CCD1的误差值
        ccdSuper2 = mid_line2 - 64  # CCD2的误差值

        ccdSuper = 0.8 * ccdSuper1 + 0.2 * ccdSuper2

        lastWidth1 = roadWidth  # 上一次CCD1的道路宽度，用于判断避障和环中点
        roadWidth1 = abs(left_edge - right_edge)  # 这一次的道路宽度

        lastWidth2 = roadWidth2  # 上一次CCD2的道路宽度，用于判断避障和环中点
        roadWidth2 = abs(left_edge2 - right_edge2)  # 这一次的道路宽度

        """直线加速模块,如果较远的ccd采集到的数据也为直线,则进入加速逻辑,直到较远的ccd采集到的中线发生较大偏移"""
        if abs(ccdSuper2) < 8 and flag == "Straight":
            flag = "speedUP"
        if abs(ccdSuper2) >= 8 and flag == "speedUP":
            flag = "Straight"

        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        Tips: 环岛部分
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        if leftOrRight == "nothing":  # 防止在找到入环标志后，在后续的跑道中再次误判圆环
            isCircleNow, leftOrRight = is_circle(ccd_data1, ccd_data2)  # isCircleNow为是否检测到环，leftOrRight为左环还是右环

        """第一步，寻找入环标志：左侧和中间同时出现白色区域，即白黑白"""
        if (isCircleNow == True) and (goCircle == False) and (checkCircle == 0):
            # 防止二次判环将goCircle的标志位刷掉，后续赛道存在多个环可以更改此处逻辑
            # 如果goCircle已经变成True，代表在之前已经检测到环
            findCircleTimes += 1  # 每读到一次入环标志，就将findCircleTimes +1，连续n次读到即进入入环状态
            if findCircleTimes == 2:  # 目前n为2
                checkCircle = 1  # 将checkCircle置1，代表进入入环状态
                print("进入入环状态")
                flag = "isCircle"
                findCircleTimes = 0
                time.sleep(1)  # 睡眠1s来防止刚检测到入环标志就判定为入环


        """第二步，找到环中点，进行强制打角"""
        if checkCircle:
            filled_mid_line = fill_line(ccd_data1, leftOrRight, checkCircle)  # 确定补线后的中线
            ccdSuper = filled_mid_line - 64  # 补线状态下的误差值,覆盖之前的ccdSuper,防止被前半段圆环误判左转
            print(f"已进入入环状态，此时补线后的中线:{filled_mid_line}")
            goCircle = Go_circle_now(ccd_data1, ccd_data2, lastWidth1)  # 如果检测到环中点，将goCircle置为True
            if goCircle:
                # 在完成入环后,进入基础的循迹逻辑,环岛运行过程中一般是丢一边线的单边循迹，通过强制打角即可进入环岛
                if leftOrRight == "left":
                    flag = "goLeftCircle"
                    checkCircle = 0  # 此时置0，退出补线逻辑
                if leftOrRight == "right":
                    flag = "goRightCircle"
                    checkCircle = 0  # 此时置0，退出补线逻辑

        """第三步，在完成环岛动作后，应用出环逻辑强制出环"""
        # 一旦找到十字路口的样式,代表找到了出环位置(左右均全白),此时强制打角出环,然后调用ccd_data2进行直线循迹
        outCircle = (detect_intersection(ccd_data1))
        if outCircle and goCircle:
            print("找到十字路口")
            alreadyOutCircle = 1  # 每次只进行一次出环动作
            goCircle = 0  # 防止多次识别为出环
            if leftOrRight == "left":
                print("此刻进行出环左打角\n")
                set_servo_angle(pwm_servo, 40)
            if leftOrRight == "right":
                print("此刻进行出环右打角\n")
                set_servo_angle(pwm_servo, -40)

        """第四步，切换ccd2来读取数据(ccd2读的更远，不会被干扰)，确保成功进入直道"""
        if leftOrRight != "nothing" and alreadyOutCircle:  # 已经完成了入环判断，入环打角，出环打角
            ccdSuper = ccdSuper2  # 切换ccd2读取的数据来循迹，因为ccd1会被环岛白色区域误判
            if abs(ccdSuper) < 8 and abs(ccdSuper2) < 8:
                leftOrRight = "alreadyFindCircle"  # 当两个ccd都读到直道，将leftOrRight清除，退出环岛逻辑

        """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        Tips: 避障部分
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
        barrierNow, barrierLocation = find_barrier(ccd_data1, lastWidth1)
        if barrierNow:
            if barrierLocation == "left":
                pass

            if barrierLocation == "right":
                pass

        # print("enc ={:>6d}, {:>6d}\r\n".format(encoder_l.get(), encoder_r.get())) # 打印编码器数据
        # wireless.send_ccd_image(WIRELESS_UART.ALL_CCD_BUFFER_INDEX)  # 无线打印ccd数据

        # 定时器关断标志
        ticker_flag = False

    # 屏幕显示
    lcd.str24(0, 24 * 4, f"flag : {flag}", 0xFFFF)
    lcd.str24(0, 24 * 1, "offset={:>.2f}.".format(ccdSuper), 0xFFFF)
    lcd.str24(0, 24 * 2, "mid_line={:>.2f}.".format(mid_line), 0xFFFF)
    lcd.str24(0, 24 * 3, "roadWidth={:>.2f}.".format(roadWidth1), 0xFFFF)
    lcd.str24(0, 24 * 4, f"{leftOrRight}", 0xFFFF)
    lcd.str24(0, 24 * 5, "isCircleNow={:>.2f}.".format(isCircleNow), 0xFFFF)
    lcd.str24(0, 24 * 6, "goCircle={:>.2f}.".format(goCircle), 0xFFFF)
    lcd.str24(0, 24 * 7, "filled_mid_line={:>.2f}.".format(filled_mid_line), 0xFFFF)
    lcd.str24(0, 24 * 8, "alreadyOutCircle={:>.2f}.".format(alreadyOutCircle), 0xFFFF)

    # 通过 wave 接口显示数据波形 (x,y,width,high,data,data_max)
    # lcd.wave(0, 24 * 10, 128, 64, ccd_data1, max=200)
    # lcd.wave(0, 24 * 10+ 64, 128, 64, ccd_data2, max=200)

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()
