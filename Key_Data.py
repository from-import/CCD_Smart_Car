from machine import *
from seekfree import KEY_HANDLER
import gc

key_1 = 0
key_2 = 0
key_3 = 0
key_4 = 0

def Key_data(key):
    global key_1,key_2,key_3,key_4
    key_data = key.get()
    # 按键数据为三个状态 0-无动作 1-短按 2-长按
    #瞬时按钮
    if key_data[0]:
        key_1 = key_data[0]
        key.clear(1)
    else:
        key_1 = 0

    if key_data[1]:
        key_2 = key_data[1]
        key.clear(2)
    else:
        key_2 = 0

    #延迟按钮
    if key_data[2]:
        key_3 = key_data[2]
        key.clear(3)
    if key_data[3]:
        key_4 = key_data[3]
        key.clear(4)

    return key_1,key_2,key_3,key_4