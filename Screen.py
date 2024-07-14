from machine import *
from display import *
import gc
import time


def init_Screen():
    """
    功能:
    - 初始化 LCD 屏幕的引脚和驱动。
    - 设置屏幕颜色和模式。
    - 清屏并逐行显示传入的字符串数组。
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
    lcd.mode(0)
    # 清屏 参数是 RGB565 格式的颜色数据
    lcd.clear(0x0000)
    return (lcd)

    gc.collect()

    """
    # 显示字符串的函数 [x,y,str,color]
    # x - 起始显示 X 坐标
    # y - 起始显示 Y 坐标
    # str - 字符串
    # color - 字符颜色 可以不填使用默认的前景色
    lcd.str12(0, 0,"15={:b},{:d},{:o},{:#x}.".format(15,15,15,15),0xF800)
    lcd.str16(0,12,"1.234={:>.2f}.".format(1.234),0x07E0)
    lcd.str24(0,28,"123={:<6d}.".format(123),0x001F)
    lcd.str32(0,52,"123={:>6d}.".format(123),0xFFFF)
    0xF800:红色；0x07E0：绿色；0x001F：蓝色；0xFFFF：白色；0x0000：黑色；
    Tips:
    设置6行的显示余量
    """
def display_strings(lcd, key, value):
    lcd.clear(0x0000)
    # key = ["a","b","c"]
    # value = [1,2,3]
    # {}——》:分隔符； > 右对齐； .2f 浮点数，两位小数
    # 使用enumerate遍历附加参数
    # 最终的显示界面
    for i in range(0, len(key)):
        formatted_value = f"{value[i]:.2f}"
        lcd.str12(0, i * 12, f"{key[i]}={formatted_value}", 0xFFFF)





