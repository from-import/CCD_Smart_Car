from machine import *
from seekfree import TSL1401
from Get_CCD import read_ccd_data, find_road_edges
from Motor_Origin import Record_Distance

flag = 0
last_width = 0

isCircleNow = False
Go_circle = False
outCircle = False
WaitoutCircle = False

timer = 0
circle_count = 0

""" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Tips:   Statu 总启动标志，0为停止
        flag = 0  正常寻线活动
        flag = 2023 用来标记长镜头对特殊元素的影响
        flag = 4  单边补线
        flag = 40 入环
        flag = 5  预备出环
        flag = 50 出环
        flag = 10 斑马线
        flag = 11 出线
        flag = 7788 十字路口
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""


def Element_flag(data, left_edge, right_edge, Yaw, data2):
    global flag, last_width
    global isCircleNow, Go_circle, outCircle, WaitoutCircle
    global Ready_Circle, If_Circle_Go, timer, circle_count
    number = count_transitions(data)
    width = count_white(data)

    # 出线停车
    if flag == 11 or flag == 0:
        flag = 11 if (number == 0 and data[64] == 0) else 0
        return 11

    # 斑马线停车
    if number > 5 and width < 40:
        flag = 10
        return 10

    """第一步，寻找入环标志：左侧和中间同时出现白色区域，即白黑白；进圆预入环，flag = 4"""
    isCircleNow = is_circle(width, left_edge, right_edge)
    if isCircleNow:
        circle_count += 1  # 增加计数
        if circle_count >= 50:  # 检查是否达到10次
            last_width = width  # 更新width数值
            return 2023  # CCD2识别到50次入环特征，flag设置为2023
    else:
        circle_count = 0  # 重置计数器
        last_width = width  # 更新width数值
        return 0

    """第二步，找到环中点，进行强制打角，flag = 40"""
    if isCircleNow:
        flag = 4
        Go_circle = Go_circle_now(width)

    """第三步，进入环岛，并且丢单线，持续识别出环标志,flag = 5,预备出环，用圆环内补线逻辑"""
    if Go_circle:
        # print('Go_circle')
        flag = 40
        isCircleNow = False
        # 入环成功，开始丢线走圆内急弯
        WaitoutCircle = Wait_to_outCircle(data)

    """第四步，识别到大部分为白色的特征，进入出环阶段"""
    if WaitoutCircle:
        # print('WaitoutCircle')
        flag = 5
        Go_circle = False
        outCircle = True

    # print(abs(Yaw),outCircle)
    if outCircle and abs(Yaw) > 280:
        # print('outCircle')
        WaitoutCircle = False
        flag = 501

    if flag == 501 and abs(Yaw) > 345:
        # 僵直，维持原状态
        flag = 50
        outCircle = False

    if flag == 50:
        if out_detect_intersection(data, data2):
            timer += 1
        if timer == 150:
            flag = 0
            timer = 0
        Ready_Circle = False
        If_Circle_Go = False

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
Tips:因为圆环会存在（白黑白黑）的特征，此时左右边界的特征表现为直道 
        此现象较复杂，容易导致一些误判，所以放弃此种特征
        我们统一使用[0*128]中白点的数量来代替width
"""


# 计算白点数目，不同于width
def count_white(data):
    # 初始化字典，记录0和1的个数
    count = {0: 0, 1: 0}

    # 遍历CCD数据
    for value in data:
        if value in count:
            count[value] += 1
    # print(count[1])
    return count[1]


"""
函数名: is_circle
作用: 通过分析CCD数据，判断是否进入环岛并检测环岛的方向（左环或右环）。
_——————____,现象，单边出现大量白色

思路：设定区间框选单边的正常范围，判断是否一边是不丢线状态
    （____白色容错区间左边线34-47——中线64——白色容错区间右边线81-94____）
        True：判断另外一边是否出现大量白色的特征
        True：is_circle
"""


def is_circle(number_white, left_edge, right_edge):
    left_edge_min = 35
    left_edge_max = 49
    right_edge_min = 79
    right_edge_max = 93
    """ 
    else:
        left_edge_min = 35
        left_edge_max = 46
        right_edge_min = 82
        right_edge_max = 93
    """

    if left_edge_min < left_edge < left_edge_max or right_edge_min < right_edge < right_edge_max:
        if number_white > 70:
            return True
    return False


"""
函数名: Go_circle_now
作用: 通过分析CCD数据和道路宽度变化，判断是否现在进行舵机打角入环。

思路：黑色内环会让我们后面看到的白色渐渐变少
        因为使用了简单的白色量的方式所以可以很简单的逻辑

    注意，后面逻辑简单化的前提是我们的is_Circle条件需要足够的苛刻
"""

Ready_Circle = False
If_Circle_Go = False


def Go_circle_now(current_width):
    global last_width
    global Ready_Circle, If_Circle_Go
    # 可以使用扫描圆中点的方式，但也可以用扫描大小的方式
    # 扫描大小的方式可以调整入圆的时间
    # if last_width < current_width：
    if current_width > 70:
        Ready_Circle = True

    if Ready_Circle and current_width < 50:
        return True

    # if If_Circle_Go and current_width > 55:
    # return True
    return False


"""
函数名: Wait_to_outCircle
作用: 通过分析CCD数据和道路宽度变化，判断是否现在准备出环。
思路：入环成功，开始丢线走圆内急弯，这个环节会出现类似于转弯的特性
"""


def Wait_to_outCircle(data, num_ones=6, segment_length=15):
    # 数组左右6个都为1则认为开始丢线
    # 检查前15个元素
    for i in range(segment_length - num_ones + 1):
        if all(x == 1 for x in data[i:i + num_ones]):
            return True

    # 检查最后15个元素
    for i in range(len(data) - segment_length, len(data) - num_ones + 1):
        if all(x == 1 for x in data[i:i + num_ones]):
            return True

    return False


"""
函数名: Out_Circle_now
作用: 通过分析CCD数据和道路宽度变化，判断是否现在进入出环程序。
思路：出现一个类似于十字的大白色特征时我们知道应该出环了
"""


def Out_Circle_now(width):
    if width > 60:
        return True
    return False


"""
函数名: find_intersection
作用: 分析二值化后的CCD数据，判断是否存在十字路口。

参数:
binary_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值:
bool: True表示检测到十字路口；否则返回False。

说明:
此函数检查在给定的CCD数据中，索引为10, 20, 30, 40, 50, 60, 70, 80, 90, 100的元素是否均为1。
如果这些位置上的元素均为1，则判定进入十字路口。
否则，返回False。
"""


def detect_intersection(ccd1, ccd2):
    left_edge1, right_edge1, mid_line1 = find_road_edges(ccd1, 0, 1)
    width1 = abs(left_edge1 - right_edge1)  # 判断CCD1宽度是否为直道
    check_indices = [20, 30, 40, 50, 60, 70, 80, 90, 100]  # 检查CCD2特定位置的元素是否均为1
    if all(ccd2[i] == 1 for i in check_indices):
        if width1 < 50:
            return True
    return False


def on_detect_intersection(ccd1, ccd2):
    check_indices = [30, 40, 50, 60, 70, 80, 90]
    if all(ccd2[i] == 1 for i in check_indices):
        if all(ccd1[i] == 1 for i in check_indices):
            return True
    return False


def out_detect_intersection(ccd1, ccd2):
    left_edge1, right_edge1, mid_line1 = find_road_edges(ccd1, 0, 1)
    left_edge2, right_edge2, mid_line2 = find_road_edges(ccd2, 0, 2)
    width1 = abs(left_edge1 - right_edge1)  # 判断CCD1宽度是否为直道
    width2 = abs(left_edge2 - right_edge2)  # 判断CCD2宽度是否为直道
    if width1 < 50 and width2 < 50:
        return True
    return False
