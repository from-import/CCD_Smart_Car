
# 本示例程序演示如何使用 display 库
# 使用 RT1021-MicroPython 核心板搭配对应拓展学习板的屏幕接口测试

# 示例程序运行效果为循环在 IPS200 上刷新全屏颜色 然后显示数字 画线

# 从 machine 库包含所有内容
from machine import *

# 包含 display 库
from display import *

# 包含 gc time 类
import gc
import time

# 定义片选引脚
cs = Pin('C5' , Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
# 拉高拉低一次 CS 片选确保屏幕通信时序正常
cs.high()
cs.low()
# 定义控制引脚
rst = Pin('B9' , Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
dc  = Pin('B8' , Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
blk = Pin('C4' , Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
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

while True:
    time.sleep_ms(500)
    lcd.clear(0xF800)
    time.sleep_ms(500)
    lcd.clear(0x07E0)
    time.sleep_ms(500)
    lcd.clear(0x001F)
    time.sleep_ms(500)
    lcd.clear(0xFFFF)
    time.sleep_ms(500)
    lcd.clear(0x0000)
    time.sleep_ms(500)
    
    # 显示数据与显示字符串对于 Python 来说没有区别
    # 显示字符串的函数 [x,y,str,color]
    # x - 起始显示 X 坐标
    # y - 起始显示 Y 坐标
    # str - 字符串
    # color - 字符颜色 可以不填使用默认的前景色
    lcd.str12(0, 0,"15={:b},{:d},{:o},{:#x}.".format(15,15,15,15),0xF800)
    lcd.str16(0,12,"1.234={:>.2f}.".format(1.234),0x07E0)
    lcd.str24(0,28,"123={:<6d}.".format(123),0x001F)
    lcd.str32(0,52,"123={:>6d}.".format(123),0xFFFF)
    # 显示一条线的函数 [x1,y1,x1,y1,color,thick]
    # x1 - 起始 X 坐标
    # y1 - 起始 Y 坐标
    # x2 - 结束 X 坐标
    # y2 - 结束 Y 坐标
    # color - 线的颜色 可以不填使用默认的前景色
    # thick - 线的宽度 可以不填 默认 1
    lcd.line(0,84,200,16 + 84,color=0xFFFF,thick=1)
    lcd.line(200,84,0,16 + 84,color=0x3616,thick=3)
    time.sleep_ms(1000)
    
    gc.collect()
