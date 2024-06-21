from machine import *

# 包含 gc 与 time 类
import gc
import time

# 核心板上 C4 是 LED
led1 = Pin('C4' , Pin.OUT, pull = Pin.PULL_UP_47K, value = True)
# 选择学习板上的二号拨码开关作为退出选择开关
end_switch = Pin('C19', Pin.IN, pull=Pin.PULL_UP_47K, value = True)
end_state = end_switch.value()

while True:
    time.sleep_ms(500)
    led1.toggle()
    print("led1 ={:>6d}".format(led1.value()))
    gc.collect()
    
    # 如果拨码开关打开 对应引脚拉低 就退出循环
    # 这么做是为了防止写错代码导致异常 有一个退出的手段
    if end_switch.value() != end_state:
        print("Ticker stop.")
        break
