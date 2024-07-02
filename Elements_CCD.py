from machine import *
from seekfree import TSL1401
from CCD_Tool import find_road_edges,CCD_Error

transitions = 0
flag = 0
error = 0
left_edge = None
right_edge = None
Stop = 0


def Element_flag(data):
    global transitions, flag
    number = count_transitions(data)
    # 出线,斑马线
    Statu = 0 if (number == 0 and data[64] == 0) else 1
    if number > 5:
        Stop = 1
    if Stop:
        Statu = 0

    """
    if (number > 5):
        # 斑马线停车
        flag = 10
    elif number == 3:
        # 入环
        flag = 3
    """

    return Statu


# 计算跳变点数
def count_transitions(data):
    global transitions
    # 合计跳变数
    transitions = 0
    for i in range(1, len(data)):
        if data[i] != data[i - 1]:
            transitions += 1

    return transitions


"""
CCD_Error(binary_data) : 查找道路左侧和右侧的边界位置，并计算中线位置。

参数:
binary_data (list): 二值化后的CCD数据，1表示道路，0表示非道路。

返回:
误差值
"""


def CCD_Error(binary_data):
    global error, left_edge, right_edge
    left_edge = None
    right_edge = None

    for i in range(len(binary_data)):
        if binary_data[i] == 1 and left_edge is None:
            left_edge = i
        if binary_data[i] == 0 and left_edge is not None:
            right_edge = i - 1
            break
    # 补线
    if left_edge == None:
        left_edge = 1
    if right_edge == None:
        right_edge = 128
    error = int(0.5 * (left_edge + right_edge)) - 64

    return error


"""

detect_roundabout : 判断是否进入环岛。

函数名: detect_roundabout(binary_data)

作用: 分析二值化后的CCD数据，判断是否存在环岛。

参数:
binary_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值:
bool: 如果检测到可能的环岛（根据道路宽度和中线偏移量），则返回True；否则返回False。

说明:
此函数首先调用 find_road_edges 函数获取道路的左侧和右侧边界位置，并计算出中线位置。
然后根据道路宽度和中线偏移量进行判断：
- 如果道路宽度大于90或小于40，或者中线偏移量绝对值大于20，则判定可能进入环岛。
- 否则，返回False。

调用案例:
binary_data = [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1]
is_roundabout = detect_roundabout(binary_data)
print("是否进入环岛:", is_roundabout)
"""



def detect_roundabout(binary_data):
    left_edge , right_edge = find_road_edges(binary_data)
    middle_error = CCD_Error(binary_data)

    if left_edge is not None and right_edge is not None:
        road_width = right_edge - left_edge

        # 根据道路宽度和中线偏移量判断是否进入环岛
        if road_width > 90 or road_width < 40 or abs(middle_error) > 20:
            return 1

    return 0


"""

detect_intersection : 检测十字路口。

函数名: detect_intersection(binary_data)

作用: 分析二值化后的CCD数据，判断是否存在十字路口。

参数:
binary_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值:
bool: 如果检测到可能的十字路口（根据道路宽度和中线偏移量），则返回True；否则返回False。

说明:
此函数首先调用 find_road_edges 函数获取道路的左侧和右侧边界位置，并计算出中线位置。
然后根据道路宽度和中线偏移量进行判断：
- 如果道路宽度大于120或小于60，或者中线偏移量绝对值大于30，则判定可能是十字路口。
- 否则，返回False。

调用案例:
binary_data = [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1]
is_intersection = detect_intersection(binary_data)
print("是否进入十字路口:", is_intersection)
"""


def detect_intersection(binary_data):
    global error, left_edge, right_edge

    if left_edge is not None and right_edge is not None:
        road_width = right_edge - left_edge
        middle_error = error

        # 根据道路宽度和中线偏移量判断是否进入十字路口
        if road_width > 120 or road_width < 60 or abs(middle_error) > 30:
            return 1

    return 0


