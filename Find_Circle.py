def find_road_edges(ccd_data, lastMiddlePosition=None):
    """工具方法无需理会"""
    left_edge = None  # 左边界位置初始化为 None
    right_edge = None  # 右边界位置初始化为 None

    # 检测连续两个相同值的元素，确定左边界和右边界
    for i in range(len(ccd_data) - 1):
        if ccd_data[i] == 1 and ccd_data[i + 1] == 1 and left_edge is None:
            left_edge = i  # 找到连续两个1，作为左边界，避免误差影响
        if ccd_data[i] == 0 and ccd_data[i + 1] == 0 and left_edge is not None:
            right_edge = i - 1  # 找到连续两个0，作为右边界，避免误差影响
            break

    # 如果没有检测到左边界或右边界
    if left_edge is None:
        left_edge = 0  # 假设左边界在最左边
    if right_edge is None:
        right_edge = len(ccd_data) - 1  # 假设右边界在最右边

    # 计算中线位置
    mid_line = (left_edge + right_edge) // 2

    # 根据上一次的中线位置调整当前中线位置
    if lastMiddlePosition is not None:
        mid_line = (mid_line + lastMiddlePosition) // 2

    return left_edge, right_edge, mid_line  # 返回左边界、右边界和中线位置的元组


"""
环岛判断方法1

函数名: detect_roundabout
作用: 判断是否进入环岛。

参数:
    ccd_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值:
    bool: 如果检测到可能的环岛，则返回True；否则返回False。

说明:
此函数首先调用 find_road_edges 函数获取道路的左侧和右侧边界位置，并计算出中线位置。
然后根据道路宽度和中线偏移量进行判断：
- 如果道路宽度大于90或小于40，或者中线偏移量绝对值大于20，则判定可能进入环岛。
- 否则，返回False。

调用案例:
ccd_data = [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1]
is_roundabout = detect_roundabout(ccd_data)
print("是否进入环岛:", is_roundabout)
"""

def detect_roundabout(ccd_data):
    left_edge, right_edge = find_road_edges(ccd_data)

    if left_edge is not None and right_edge is not None:
        road_width = right_edge - left_edge
        middle_error = int(0.5 * (left_edge + right_edge)) - 64

        # 根据道路宽度和中线偏移量判断是否进入环岛
        if road_width > 90 or road_width < 40 or abs(middle_error) > 20:
            return True

    return False




"""
环岛判断方法2

函数名: find_roundabout
作用: 通过分析CCD数据的道路宽度变化，判断是否进入环岛。

参数:
    ccd_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值:
    bool: 如果检测到可能的环岛，则返回True；否则返回False。

说明:
此函数首先遍历CCD数据，计算每段连续道路的宽度，并将宽度存储在列表width_list中。
然后，通过比较连续两段道路宽度的变化，判断是否存在显著变化（超过设定阈值threshold_width）。
如果检测到显著的宽度变化，则判定可能进入环岛。

调用案例:
ccd_data = [0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
is_roundabout = find_roundabout(ccd_data)
print("是否进入环岛:", is_roundabout)
"""

def find_roundabout(ccd_data):
    # 初始化参数
    is_road = False
    road_start = 0
    road_end = 0
    road_width = 0
    roundabout_detected = False
    threshold_width = 20  # 定义宽度变化的阈值，用于判断是否为环岛
    width_list = []

    # 遍历CCD数据，计算每段连续道路的宽度
    for i in range(1, len(ccd_data)):
        if ccd_data[i] == 1 and not is_road:
            # 道路开始
            road_start = i
            is_road = True
        elif ccd_data[i] == 0 and is_road:
            # 道路结束
            road_end = i
            road_width = road_end - road_start
            width_list.append(road_width)
            is_road = False

    # 最后一段道路处理
    if is_road:
        road_end = len(ccd_data)
        road_width = road_end - road_start
        width_list.append(road_width)

    # 判断是否存在环岛，通过分析宽度变化
    for i in range(1, len(width_list)):
        if abs(width_list[i] - width_list[i-1]) >= threshold_width:
            roundabout_detected = True
            break

    return roundabout_detected


