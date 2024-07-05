from machine import *
from seekfree import TSL1401

flag = 0
last_width = 0

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips:   Statu 总启动标志，0为停止
        flag = 0  正常寻线活动
        flag = 4  单边补线
        flag = 40 入环
        flag = 10 斑马线
        flag = 11 出线
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


def Element_flag(data, left_edge, right_edge,ccdSuper2,ccdSuper):
    global flag,last_width
    isCircleNow = False
    Go_circle = False
    outCircle = False  # 读取跳变点
    number = count_transitions(data)

    # 出线,斑马线
    flag = 11 if (number == 0 and data[64] == 0) else 0
    if number > 7:
        flag = 10

    width = abs(right_edge - left_edge)

    """第一步，寻找入环标志：左侧和中间同时出现白色区域，即白黑白；进圆预入环，flag = 4"""
    if not isCircleNow and not flag:
        isCircleNow = is_circle(data,ccdSuper)  # isCircleNow为是否检测到环，leftOrRight为左环还是右环

    """第二步，找到环中点，进行强制打角"""
    #成功进入预入环，准备入环，flag=40
    if isCircleNow:
        flag = 4
        Go_circle = Go_circle_now(width)

    """第三步，在完成环岛动作后，应用出环逻辑强制出环"""
    # 成功入环，准备出环，flag=40
    if Go_circle:
        flag = 40
        if width > 100:
            outCircle = True
            flag = 5

    """第四步，切换ccd2来读取数据(ccd2读的更远，不会被干扰)，确保成功进入直道"""
    if outCircle and flag == 5:
        if abs(ccdSuper2) < 5:
            flag = 50

    if outCircle == True and ccdSuper2<5 and ccdSuper<5:
        flag = 0
        outCircle = False
        Go_circle = False
        isCircleNow = False

    # 更新width数值
    last_width = width
    return flag


# 计算跳变点数
def count_transitions(data):
    # 合计跳变数
    transitions = 0
    for i in range(1, len(data)):
        if data[i] != data[i - 1]:
            transitions += 1

    return transitions


"""
函数名: is_circle
作用: 通过分析CCD数据，判断是否进入环岛并检测环岛的方向（左环或右环）。

参数:
ccd_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值: tuple: 
如果未检测到环岛，则返回 False,"nothing"
如果检测到可能的环岛，则返回一个包含两个元素的元组 (True, direction)；
其中 direction 表示环岛方向 ("left" 或 "right")。否则返回 (False, None)。

说明:
此函数首先调用 find_road_edges 函数获取道路的左边界、右边界和中线位置。
接着判断中线是否在 64 ± 10 范围内，如果不在此范围内，则认为未进入环岛。
如果中线在此范围内，则分别检查左环和右环的条件：在左侧或右侧的CCD数据中是否存在连续5个1:
如果存在则判断为进入环岛，并返回环岛方向。
"""


def is_circle(ccd_data,ccdSuper):
    # 预入环
    # 判断中线是否在 64 ± 10 以内,是的话进入下一步
    if abs(ccdSuper) > 10:
        return False

    for i in range(0, 30):
        if ccd_data[i:i + 5] == [1, 1, 1, 1, 1]:
            return True

    for i in range(98, 127):
        if ccd_data[i:i - 5:-1] == [1, 1, 1, 1, 1]:
            return True
    return False

"""
函数名: Go_circle_now
作用: 通过分析CCD数据和道路宽度变化，判断是否现在进行舵机打角入环。

参数:
ccd_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。
last_width (int): 上一次检测到的道路宽度，默认值为0。

返回值: bool 
如果需要现在进行舵机打角入环，则返回True；否则返回False。

说明:
此函数首先调用 find_road_edges 函数获取道路的左边界、右边界和中线位置。
接着计算当前的道路宽度，并判断中线是否在 64 ± 5 范围内。(调参)
如果中线在此范围内，并且当前宽度小于上一次检测的宽度，则返回True，表示需要现在进行舵机打角入环。
否则返回False。
"""


def Go_circle_now(current_width):
    global last_width
    Go_circle = False
    if current_width < 60:
        # 判断宽度是否变小,来判断CCD是否扫描到了环的中点位置
        Go_circle = True if last_width > current_width else False
    return Go_circle


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
    left_edge, right_edge = find_road_edges(binary_data)

    if left_edge is not None and right_edge is not None:
        road_width = right_edge - left_edge
        middle_error = int(0.5 * (left_edge + right_edge)) - 64

        # 根据道路宽度和中线偏移量判断是否进入十字路口
        if road_width > 120 or road_width < 60 or abs(middle_error) > 30:
            return 1

    return 0



