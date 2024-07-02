from CCD_Tool import find_road_edges

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


def is_circle(ccd_data):
    left_edge, right_edge, mid_line = find_road_edges(ccd_data)

    # 判断中线是否在 64 ± 10 以内,是的话进入下一步
    if abs(mid_line - 64) > 10:
        return False, "nothing"

    # 检查左环的条件
    left_ring = False
    for i in range(0, 30):
        if ccd_data[i:i + 5] == [1, 1, 1, 1, 1]:
            left_ring = True
            return True, "left"

    # 检查右环的条件
    right_ring = False
    for i in range(100, 127):
        if ccd_data[i:i - 5:-1] == [1, 1, 1, 1, 1]:
            right_ring = True
            return True, "right"


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


def Go_circle_now(ccd_data, last_width=0):
    left_edge, right_edge, mid_line = find_road_edges(ccd_data)
    current_width = right_edge - left_edge  # 计算当前宽度

    # 判断中线是否在 64 ± 5 范围内
    if abs(mid_line - 64) <= 5:
        # 判断宽度是否变小,来判断CCD是否扫描到了环的中点位置
        if last_width > current_width:
            return True

    return False



