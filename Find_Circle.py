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
    for i in range(0, 20):
        if ccd_data[i:i + 10] == [1] * 10:
            return True, "left"

    # 检查右环的条件
    for i in range(105, 127):
        if ccd_data[i:i - 10:-1] == [1] * 10:
            return True, "right"
    return False, "nothing"


"""
函数名: Go_circle_now
作用: 通过分析CCD数据和道路宽度变化，判断是否现在检测到了环的中点位置

参数:
ccd_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。
last_width (int): 上一次检测到的道路宽度，默认值为0。

返回值: bool
如果需要现在进行舵机打角入环，则返回True；否则返回False。

说明:
此函数首先调用 find_road_edges 函数获取道路的左边界、右边界和中线位置。
接着计算当前的道路宽度，并判断宽度是否大于50(调参)
如果宽度满足要求，并且当前宽度小于上一次检测的宽度+5，则返回True，表示需要现在进行舵机打角入环。
否则返回False。
"""


def Go_circle_now(ccd_data, last_width=45):
    left_edge, right_edge, mid_line = find_road_edges(ccd_data)
    current_width = right_edge - left_edge  # 计算当前宽度

    if current_width > 50:
        # 判断宽度是否变小,来判断CCD是否扫描到了环的中点位置
        if last_width > current_width + 5:
            return True

    return False


"""
函数名: fill_line
作用: 根据中线位置对CCD数据进行对称补线

参数:
ccd_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。
direction (str): 方向，'left' 表示从中线向右查找右边界并补左边界，'right' 表示从中线向左查找左边界并补右边界。
fill (bool): 是否进行补线操作，True 表示进行补线，False 表示不进行补线。
lastMiddlePosition (int, 可选): 上一次的中线位置，默认为64。

返回值: int: 中线位置。

说明:
此函数首先判断是否需要进行补线操作，如果不需要直接返回上一次的中线位置。
如果需要补线，通过调用 `find_road_edges` 函数来找到道路的左右边界和中线位置。
根据方向 'left' 或 'right'，分别从中线位置向对应方向查找边界。
找到边界后，在边界位置±21处进行对称补线操作。
最终返回修改后的中线位置。
"""


def fill_line(ccd_data, direction, fill, lastMiddlePosition=64):
    if not fill:
        
        return lastMiddlePosition

    left_edge, right_edge, mid_line = find_road_edges(ccd_data, lastMiddlePosition)

    if direction == 'left':
        # 左环，优先向右查找边界
        if right_edge != lastMiddlePosition:
            mid_line = right_edge - 20
        else:
            mid_line = lastMiddlePosition

    elif direction == 'right':
        # 右环，优先向左查找边界
        if left_edge != lastMiddlePosition:
            mid_line = left_edge + 20
        else:
            mid_line = lastMiddlePosition

    return mid_line



