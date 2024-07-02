from CCD_Tool import find_road_edges

"""
函数名: is_roundabout
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


def is_roundabout(ccd_data):
    left_edge, right_edge, mid_line = find_road_edges(ccd_data)

    # 判断中线是否在 64 ± 10 以内,是的话进入下一步
    if abs(mid_line - 64) > 10:
        return False

    # 检查左环的条件
    left_ring = False
    for i in range(0, 30):
        if ccd_data[i:i + 5] == [1, 1, 1, 1, 1]:
            left_ring = True
            return True,"left"

    # 检查右环的条件
    right_ring = False
    for i in range(30, 127):
        if ccd_data[i:i - 5:-1] == [1, 1, 1, 1, 1]:
            right_ring = True
            return True,"right"


"""
环岛判断方法2

函数名: find_circle
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


