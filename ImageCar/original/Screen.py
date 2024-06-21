from machine import *
from display import *
import gc
import time

def display_strings(strings):
    """
    注意:这个函数接受的输入是数组，类似["A","B2344","AJDDKSKD"]
    不要直接传单个字符串，单个字符串也要用数组格式传： ["string"]
    初始化并在 LCD 上逐行显示字符串。

    参数:
    strings (list of str): 需要显示的字符串数组。每个字符串会在屏幕上的一行显示。
                           字符串数量和长度需要根据屏幕的分辨率和显示区域调整。

    功能:
    - 初始化 LCD 屏幕的引脚和驱动。
    - 设置屏幕颜色和模式。
    - 清屏并逐行显示传入的字符串数组。

    示例:
    strings = ["Hello, World!", "This is a test.", "Displaying strings on LCD."]
    display_strings(strings)

    这个示例会在 LCD 屏幕上显示三行字符串：
    - 第一行显示 "Hello, World!"
    - 第二行显示 "This is a test."
    - 第三行显示 "Displaying strings on LCD."
    """

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
    # 清屏 参数是 RGB565 格式的颜色数据
    lcd.clear(0x0000)

    y = 0
    for string in strings:
        # 显示字符串的函数 [x,y,str,color]
        # x - 起始显示 X 坐标
        # y - 起始显示 Y 坐标
        # str - 字符串
        # color - 字符颜色 可以不填使用默认的前景色
        lcd.str12(0, y, string, 0xF800)
        y += 12  # 假设每个字符串占用 12 个像素高度

    gc.collect()


"""
# 调用案例
strings = ["Hello, World!", "This is a test.", "Displaying strings on LCD."]
display_strings(strings)
"""
