from machine import *
from seekfree import TSL1401


def search(pixel, got_yuzhi=150, flag=0):
    max_peak = 0
    rising_edge_cnt = 0
    falling_edge_cnt = 0
    rising_edge = [0] * 5
    falling_edge = [0] * 5
    ccd_diff = [0] * 128

    # 求出最大的差分值
    for i in range(3, 128):
        ccd_diff[i] = pixel[i] - pixel[i - 3]
        if abs(ccd_diff[i]) > max_peak:
            max_peak = abs(ccd_diff[i])

    # 寻找上升沿和下降沿
    for i in range(4, 127):
        if (ccd_diff[i] >= ccd_diff[i - 1]) and (ccd_diff[i] > ccd_diff[i + 1]) and (ccd_diff[i] > got_yuzhi):
            if rising_edge_cnt < 5:
                rising_edge[rising_edge_cnt] = i
                rising_edge_cnt += 1
        if (ccd_diff[i] < ccd_diff[i - 1]) and (ccd_diff[i] <= ccd_diff[i + 1]) and (ccd_diff[i] < -got_yuzhi):
            if falling_edge_cnt < 5:
                falling_edge[falling_edge_cnt] = i
                falling_edge_cnt += 1

    if rising_edge_cnt == 0 and falling_edge_cnt == 0:
        searchFlag = 1
    else:
        searchFlag = 0

    left, right = 0, 0
    left_last_find, right_last_find = False, False

    # 处理左边和右边的检测逻辑
    if rising_edge_cnt > 0:
        left = rising_edge[0]
        left_last_find = True
    if falling_edge_cnt > 0:
        right = falling_edge[0]
        right_last_find = True

    if left_last_find and right_last_find:
        if right < left:
            left_last_find = False
            right_last_find = False

    if left_last_find and right_last_find:
        reference_width = right - left

    return left, right, (left + right) // 2, searchFlag


def get_mid(a, b, c):
    # 获取三个值中的中间值。
    x = 0
    if a > b:
        x = b
        b = a
        a = x
    if b > c:
        x = c
        c = b
        b = x
    if a > b:
        x = b
        b = a
        a = x
    return b


def bin_ccd_filter(data):
    ave = 0
    data_temp = data[:]
    data_temp2 = [0] * 4
    for i in range(len(data) - 4):
        data_temp2 = data_temp[i:i + 4]
        for j in range(4):
            ave += data_temp2[j]
        data[4 // 2 + i] = ave // 4
        ave = 0
    return data


"""函数作用：return目前计算出来的阈值"""


def threshold_determination(data):
    # 第一步：找出数据的最大值和最小值,最大值和最小值用于初步估计数据的对比度和分布情况
    # 找出数据列表中的最大值和最小值，确定数据的动态范围。
    max_val = max(data)
    min_val = min(data)
    T = (max_val + min_val) / 2  # 第三步：初始估计阈值

    while True:
        """二值化处理图像，并产生两个组数据
        进入迭代循环，不断调整阈值 T，以逐步逼近最佳阈值。
        将数据分为两组：大于当前阈值 T 的数据 (sum_h) 和小于等于当前阈值 T 的数据 (sum_l)。
        分别计算两组数据的平均值：max_ave 和 min_ave, 更新阈值为两组平均值的平均值 T_last。
        如果新阈值 T_last 与旧阈值 T 的差值小于一个很小的数（如 1e-6），则认为阈值已稳定，终止迭代。
        迭代过程确保阈值在数据分布的基础上进行动态调整，逐步逼近最佳阈值。"""
        sum_h = [x for x in data if x > T]
        sum_l = [x for x in data if x <= T]
        if len(sum_h) == 0:
            max_ave = 0
        else:
            max_ave = sum(sum_h) / len(sum_h)
        if len(sum_l) == 0:
            min_ave = 0
        else:
            min_ave = sum(sum_l) / len(sum_l)
        # 第六步：计算最终的阈值
        T_last = (max_ave + min_ave) / 2
        # 检查阈值是否稳定
        if abs(T_last - T) < 1e-6:
            break
        T = T_last
    return T  # 阈值


"""
二值化处理函数，对 CCD 数据进行二值化处理。

参数:
data (list): CCD 数据列表。
all_black_difference_value (float): 全黑时的偏差值，用于判断阈值。
T_old (float): 上一次的阈值，用于全黑情况下的处理。

返回:
list: 二值化后的 CCD 数据。
"""


def binary_thresholding(data, T):
    return [0 if x <= T else 1 for x in data]


"""
函数名：read_ccd_data
函数作用：读取 CCD 数据并进行滤波和二值化处理。

参数: ccd (TSL1401): 已初始化的 CCD 实例。

返回: tuple: 包含处理后的 CCD 数据1 和 CCD 数据2 及其二值化结果。
"""


def read_ccd_data(ccd_data1, ccd_data2, T1, T2, crossFlag, flag=0):
    # CCD 数据滤波
    filtered_ccd1 = bin_ccd_filter(ccd_data1)
    filtered_ccd2 = bin_ccd_filter(ccd_data2)

    # CCD 数据二值化
    binary_ccd1 = binary_thresholding(filtered_ccd1, T1)
    binary_ccd2 = binary_thresholding(filtered_ccd2, T2)

    return [binary_ccd1, binary_ccd2]


def white(ccd_data, n=40):
    ccd_data[:n] = [0] * n
    ccd_data[-n:] = [0] * n
    return ccd_data


"""
find_road_edges : 查找道路左侧和右侧的边界位置，并计算中线位置。
说明：在首行引线检测正确的前提下具有较强的抗干扰性，能更有效地消除十字垂直交叉黑色引线的干扰以及引线外黑色噪点的影响

参数:
ccd_data (list): CCD 数据，1 表示道路，0 表示非道路。
lastMiddlePosition (int): 上一次的中线位置，用于平滑当前的中线计算。默认为None

返回:
tuple: 包含左侧边界索引(left_edge)、右侧边界索引(right_edge)和中线位置(mid_line)的元组。

调用案例: left, right, middle = find_road_edges(ccd_data, lastMiddlePosition)
"""

lastMiddlePosition_short = 64
lastMiddlePosition_long = 64


def find_road_edges(ccd_data, flag, name):
    global lastMiddlePosition_short, lastMiddlePosition_long

    # ccd数值调用选择(1为ccd1，2为ccd2，一共两个)
    if name == 1:
        lastMiddlePosition = lastMiddlePosition_short
    else:
        lastMiddlePosition = lastMiddlePosition_long

    if lastMiddlePosition is None:
        lastMiddlePosition = 64  # 设置默认值

    start = lastMiddlePosition

    # 初始化 left_edge 和 right_edge
    left_edge = start
    right_edge = start

    # 向左扫描
    while left_edge > 0 and left_edge < len(ccd_data) and ccd_data[left_edge] == 1:
        left_edge -= 1

    # 向右扫描
    while right_edge < len(ccd_data) - 1 and right_edge >= 0 and ccd_data[right_edge] == 1:
        right_edge += 1

    # 确保扫描结果有效
    if left_edge == start and start < len(ccd_data) and ccd_data[left_edge] == 1:
        left_edge = 0
    if right_edge == start and start < len(ccd_data) and ccd_data[right_edge] == 1:
        right_edge = len(ccd_data) - 1

    if (left_edge == start or left_edge == 0) and right_edge != start:
        # 仅检测到右边界
        mid_line = right_edge - 30

    elif (right_edge == start or right_edge == len(ccd_data) - 1) and left_edge != start:
        # 仅检测到左边界
        mid_line = left_edge + 30

    elif right_edge != start and left_edge != start:
        # 同时检测到左右边界且不为全白情况
        mid_line = (left_edge + right_edge) // 2
    else:
        mid_line = 64 if lastMiddlePosition is None else lastMiddlePosition  # 未检测到左右边界

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips：只有short镜头会存在特殊元素处理
    Tips:对于特殊元素的补线活动
        flag = 4  圆环单边补线
        由leftOrRight标记进行选择补线

        flag = 40 入环   舵机打角，由mid_line选定打角方向
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    # print(name)
    if name == 1:
        if flag:
            if Special_Elements(left_edge, right_edge, flag, mid_line):
                mid_line = Special_Elements(left_edge, right_edge, flag, mid_line)
                print(mid_line)

    # ccd数值存储(1为ccd1，2为ccd2，一共两个)
    if name == 1:
        lastMiddlePosition_short = (left_edge + right_edge) // 2
    else:
        lastMiddlePosition_long = (left_edge + right_edge) // 2

    return left_edge, right_edge, mid_line  # 返回左边界、右边界和中线位置的元组


leftOrRight = 0


def Special_Elements(left_edge, right_edge, flag, line):
    # 保留leftOrRight的数值
    global leftOrRight, lastMiddlePosition_short
    if flag == 4 or flag == 2023:
        if abs(left_edge - right_edge) > 70:
            # 左1右0
            leftOrRight = 1 if (abs(left_edge - 64) > abs(right_edge - 64)) else 0
            # print(leftOrRight)
        # 单边找补，补到中线
        mid_line = right_edge - 15 if leftOrRight else left_edge + 15
        return mid_line

    if flag == 40:
        mid_line = right_edge - 37 if not leftOrRight else left_edge + 37
        return mid_line

    # 圆环特殊补线，可以调整大小，为急弯
    if flag == 5:
        mid_line = right_edge - 27 if leftOrRight else left_edge + 27
        return mid_line

    if flag == 501:
        mid_line = 100 if not leftOrRight else 28
        return mid_line

    if flag == 50:
        # 单边找补，补到中线（左近环右边补，右进环左边补）
        mid_line = right_edge - 20 if leftOrRight else left_edge + 20
        return mid_line


"""
函数名：calculate_curvature
作用：计算基于连续三个中线位置的曲率。

参数:
x1 (float): 第一个位置的中线位置。
x2 (float): 第二个位置的中线位置。
x3 (float): 第三个位置的中线位置。

返回:
float: 计算得到的曲率值。

行驶路径类型可以分为直道、曲率小的 s 弯、曲率大的 S 弯和普通弯道 4 类
u 型弯道和 0 型弯道可以认为是多个同方向普通弯道连接在一起，都可以被认为是普通弯道
若计算出来的曲率 q接近 0，则说明该段道路为直道或者小 S 弯
若曲率 q 比较大，则说明该段道路为普通弯道；若计算出来的曲率 q 非常大，则说明该段弯道为大 S 弯
"""


def calculate_curvature(x1, x2, x3):
    curvature = abs((x3 - x2) - (x2 - x1))
    return curvature








