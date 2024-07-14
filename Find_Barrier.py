import time
from CCD_Tool import find_road_edges

"""
函数名：find_barrier

参数:
    ccd_buf (list): 包含128个元素的列表，表示CCD数据。每个元素为0（白色）或1（黑色）。
    lastRoadWidth (int): 上一次测量的道路宽度。

返回值:
    tuple: 
    - (bool): 如果检测到障碍物，则返回True；否则返回False。
    - (str): 如果检测到障碍物，则返回障碍物位置 ("left" 或 "right")；否则返回"nothing"。

说明:
    此函数首先调用 `find_road_edges` 函数获取道路的左边界、右边界和中线位置。
    然后计算当前的道路宽度，并根据当前和上一次的道路宽度计算宽度变化率。
    如果宽度变化率超过设定的阈值（假设为20%），则判断为障碍物。
    如果没有检测到障碍物，则返回False和"nothing"。

示例用法:
    ccd_buf = [0] * 51 + [1] * 13 + [1] * 2 + [0] * 11 + [0] * 51  # 初始化CCD数据
    lastRoadWidth = 40  # 上一次的道路宽度
    obstacle_detected = find_barrier(ccd_buf, lastRoadWidth)
    print("是否检测到障碍物及位置:", obstacle_detected)
"""

def find_barrier(ccd_buf,lastRoadWidth):
    left_edge, right_edge, mid_position = find_road_edges(ccd_buf)  # 中线位置
    left_barrier = False
    right_barrier = False

    current_width = right_edge - left_edge
    widthRate = abs(current_width - lastRoadWidth) / lastRoadWidth if lastRoadWidth != 0 else 0

    # 假设宽度变化率阈值为20%
    threshold = 0.3

    if widthRate > threshold:
        if mid_position < 64:
            right_barrier = True
        else:
            left_barrier = True

    if left_barrier:
        return True, "left"
    elif right_barrier:
        return True, "right"
    else:
        return False, "nothing"