from machine import *
from smartcar import *
from seekfree import *
import gc
import time

"""
prompt
因为在每次调用函数都初始化会对性能有影响，我决定把函数里的初始化移动到主函数中执行，
在调用函数的时候直接传入主函数中创建的实例，接下来我要发送给你代码，
请你分别给出在主函数中初始化实例的代码和修改后的函数代码（不再在函数内初始化，而是在函数的输入参数中传入实例）
"""


""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 初始化部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

# 定时器数据建立
ticker_flag = False
ticker_count = 0
runtime_count = 0

"""
元件初始化
"""
led1 = Pin('C4', Pin.OUT, pull=Pin.PULL_UP_47K, value=True)  # 核心板上 C4 是 LED

end_switch = Pin('C19', Pin.IN, pull=Pin.PULL_UP_47K, value=True)  # 开发板上的 C19 是拨码开关
end_state = end_switch.value()

# 调用 machine 库的 PWM 类实例化一个 PWM 输出对象
pwm_servo = PWM("C20", pwm_servo_hz, duty_u16=duty)

wireless = WIRELESS_UART(460800)  # 实例化 WIRELESS_UART 模块 参数是波特率
wireless.send_str("Hello World.\r\n")  # 测试无线正常
time.sleep_ms(500)

"""
CCD 初始化，调用案例：

# ccd_data1, ccd_data2 = read_ccd_data(ccd)
# print(ccd_data1)
# print(ccd_data2)
"""
from Get_CCD import read_ccd_data
end_switch_pin = 'C19'
capture_period = 10
resolution = TSL1401.RES_12BIT
end_switch = Pin(end_switch_pin, Pin.IN, pull=Pin.PULL_UP_47K, value=True)
end_state = end_switch.value()
ccd = TSL1401(capture_period)
ccd.set_resolution(resolution)


"""
电机 Motor 初始化,示例调用:

control_motor(2500, 'left', motor_l, motor_r, led1)  # 控制左电机，以占空比 2500 运行
time.sleep(2)  # 运行 2 秒
control_motor(-2500, 'right', motor_l, motor_r, led1)  # 控制右电机，以占空比 -2500 运行
"""
from Motor import control_motor

# 初始化 MOTOR_CONTROLLER 电机驱动模块
motor_l = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C25_DIR_C27, 13000, duty=0, invert=True)
motor_r = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C24_DIR_C26, 13000, duty=0, invert=False)

"""
舵机 Motor_Servo 初始化，示例调用：

set_servo_angle(led1, pwm_servo, pwm_servo_hz, 90)
"""

from Motor_Servo import set_servo_angle,duty_angle
pwm_servo_hz = 300  # 使用 300Hz 的舵机控制频率
pwm_servo = PWM("C20", pwm_servo_hz)  # 学习板上舵机接口为 C20
# （中值：101，左max值：117，右max值88）
angle = 101.0
set_servo_angle(led1, pwm_servo, pwm_servo_hz, angle)  # 调用设置舵机角度的函数


"""
Motor_Brushless 无刷电机初始化，示例调用：
bldc_control(bldc1, bldc2, led1, key1)

"""

key1 = Pin('D23', Pin.IN, pull=Pin.PULL_UP_47K, value=True)
bldc1 = BLDC_CONTROLLER(BLDC_CONTROLLER.PWM_B26, freq=300, highlevel_us=1000) # 学习板上 BLDC 电调接口为 B26/B27
bldc2 = BLDC_CONTROLLER(BLDC_CONTROLLER.PWM_B27, freq=300, highlevel_us=1000)


"""
Screen 屏幕 初始化
千万别改这个代码，改了屏幕就寄

"""
from Show_CCD_On_Screen import display_loop
# 定义片选引脚
cs = Pin('C5', Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
# 拉高拉低一次 CS 片选确保屏幕通信时序正常
cs.high()
cs.low()
# 定义控制引脚
rst = Pin('B9', Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
dc = Pin('B8', Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
blk = Pin('C4', Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
# 新建 LCD 驱动实例 这里的索引范围与 SPI 示例一致 当前仅支持 IPS200
drv = LCD_Drv(SPI_INDEX=1, BAUDRATE=60000000, DC_PIN=dc, RST_PIN=rst, LCD_TYPE=LCD_Drv.LCD200_TYPE)
# 新建 LCD 实例
lcd = LCD(drv)
# color 接口设置屏幕显示颜色 [前景色,背景色]
lcd.color(0xFFFF, 0x0000)
# mode 接口设置屏幕显示模式 [0:竖屏,1:横屏,2:竖屏180旋转,3:横屏180旋转]
lcd.mode(2)
# 清屏
lcd.clear(0x0000)

# 调用 TSL1401 模块获取 CCD 实例
ccd = TSL1401(10)

# 定义一个回调函数（定时运行程序可以写在里面）
def time_pit_handler(time):
    global ticker_flag  # 需要注意的是这里得使用 global 修饰全局属性
    global ticker_count
    ticker_flag = True  # 否则它会新建一个局部变量
    ticker_count = (ticker_count + 1) if (ticker_count < 100) else (1)
    """用户自己的软件代码"""

# 选定1号定时器
pit1 = ticker(1)
# 关联采集接口 最少一个 最多八个
# 编码器关联
pit1.capture_list(encoder_l, encoder_r)
# ccd关联
pit1.capture_list(ccd)
# 关联 Python 回调函数
pit1.callback(time_pit_handler)
# 启动 ticker 实例 参数是触发周期 单位是毫秒
pit1.start(10)


"""
Encoder 初始化
"""
# 实例化 encoder 模块
encoder_l = encoder("D0", "D1", False)
encoder_r = encoder("D2", "D3", True)





""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 调参部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
# 电机参数设置
motor_dir = 1
dutyL = dutyR = 0
motor_duty_max = 2500




""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips: 主函数部分
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

while True:
    if (ticker_flag):

        # encoder读取
        encl_data = encoder_l.get()
        encr_data = encoder_r.get()

        # 读取CCD值，存储到数组
        ccd_data1, ccd_data2 = read_ccd_data(ccd)

        # 电机运行程序
        control_motor(2500, 'left', motor_l, motor_r, led1)  # 控制左电机，以占空比 2500 运行
        time.sleep(2)  # 运行 2 秒
        control_motor(-2500, 'right', motor_l, motor_r, led1)  # 控制右电机，以占空比 -2500 运行

        # 舵机运行程序
        set_servo_angle(101)

        # PC端调试软件打印数据
        print("enc ={:>6d}, {:>6d}\r\n".format(encoder_l.get(), encoder_r.get()))
        # 无线打印ccd数据
        wireless.send_str("CCD IMAGE\r\n")  # 测试无线正常
        wireless.send_ccd_image(WIRELESS_UART.ALL_CCD_BUFFER_INDEX)

        # 定时器关断标志
        ticker_flag = False

        #在屏幕上显示CCD
        display_loop(lcd, ccd, pit1, end_switch, end_state, time_pit_handler)

    # 按键跳出程序
    if end_switch.value() != end_state:
        pit1.stop()
        print("Ticker stop.")
        break
    gc.collect()
