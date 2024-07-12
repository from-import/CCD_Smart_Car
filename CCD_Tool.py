def hah():
    pass


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


def find_road_edges(ccd_data, lastMiddlePosition=64):
    if lastMiddlePosition is None:
        lastMiddlePosition = 64  # 设置默认值

    start = lastMiddlePosition
    left_edge = start
    right_edge = start

    # 向左扫描
    while 0 < left_edge < len(ccd_data) and ccd_data[left_edge] == 1:
        left_edge -= 1

    # 向右扫描
    while len(ccd_data) - 1 > right_edge >= 0 and ccd_data[right_edge] == 1:
        right_edge += 1

    # 确保扫描结果有效
    if left_edge == start and start < len(ccd_data) and ccd_data[left_edge] == 1:
        left_edge = 0
    if right_edge == start and start < len(ccd_data) and ccd_data[right_edge] == 1:
        right_edge = len(ccd_data) - 1

    if (left_edge == start or left_edge == 0) and right_edge != start:
        # 仅检测到右边界
        mid_line = right_edge - 22  # 补中线
        left_edge = right_edge - 44  # 补左线

    elif (right_edge == start or right_edge == len(ccd_data) - 1) and left_edge != start:
        # 仅检测到左边界
        mid_line = left_edge + 22  # 补中线
        right_edge = left_edge + 44  # 补右线

    elif left_edge <= 5 and right_edge >= len(ccd_data) - 5:
        # 处理全白情况
        mid_line = 64  # 假设道路在中间
        left_edge = 21  # 设置默认左边界
        right_edge = 107  # 设置默认右边界
        return left_edge, right_edge, mid_line  # 返回左边界、右边界和中线位置的元组

    elif right_edge != start and left_edge != start:
        # 同时检测到左右边界且不为全白情况
        mid_line = (left_edge + right_edge) // 2
    else:
        mid_line = 64 if lastMiddlePosition is None else lastMiddlePosition  # 未检测到左右边界

    return left_edge, right_edge, mid_line  # 返回左边界、右边界和中线位置的元组


"""
函数名: find_start_line
作用: 检测CCD数据缓冲区中的起跑线(斑马线)。

参数:
    ccd_buf (list): 包含128个元素的列表，表示CCD数据。每个元素为0（黑色）或1（白色）。
    interval (int): 间隔，检查像素值变化的距离。默认值为2。
    threshold (int): 阈值，判断像素值变化的阈值。默认值为1。

返回值:
    int: 如果检测到有效的起跑线，则返回1；否则返回0。

说明:
    此函数遍历 `ccd_buf` 数组，检测边缘变化以判断是否存在起跑线。
    它通过检查像素值变化是否超过指定的 `threshold` 来统计边缘变化次数。
    如果边缘变化次数达到或超过5次，则认为检测到起跑线，并返回1。

示例用法:
    find_start_line(ccd_buf)
"""


def find_start_line(ccd_buf, interval=3, threshold=1):
    edge_count = 0
    last_edge_index = -1

    for i in range(45, 100):
        if abs(ccd_buf[i] - ccd_buf[i + interval]) >= threshold:
            if last_edge_index == -1 or i != last_edge_index + 1:
                edge_count += 1
            last_edge_index = i

    # 如果边缘变化次数超过一定数量，认为检测到起跑线
    if edge_count >= 5:  # 这里假设5是合理的阈值，可以根据实际情况调整
        return 1
    else:
        return 0


"""
函数作用：寻找进入十字路口的点和离开十字路口的点
"""


def detect_intersection(ccd1, ccd2, lastMid_line1):
    left_edge1, right_edge1, mid_line1 = find_road_edges(ccd1, lastMid_line1)
    width1 = abs(left_edge1 - right_edge1)  # 判断CCD1宽度是否为直道
    check_indices = [20, 30, 40, 50, 60, 70, 80, 90, 100]  # 检查CCD2特定位置的元素是否均为1
    if all(ccd2[i] == 1 for i in check_indices):
        if width1 < 60:
            return True
    return False


def on_detect_intersection(ccd1, ccd2):
    check_indices = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    if all(ccd2[i] == 1 for i in check_indices):
        if all(ccd1[i] == 1 for i in check_indices):
            return True
    return False


def out_detect_intersection(ccd1, ccd2, lastMid_line1, lastMid_line2):
    left_edge1, right_edge1, mid_line1 = find_road_edges(ccd1, lastMid_line1)
    left_edge2, right_edge2, mid_line2 = find_road_edges(ccd2, lastMid_line2)
    width1 = abs(left_edge1 - right_edge1)  # 判断CCD1宽度是否为直道
    width2 = abs(left_edge2 - right_edge2)  # 判断CCD2宽度是否为直道
    if width1 < 60 and width2 < 60:
        return True
    return False


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
