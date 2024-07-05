from CCD_Tool import find_road_edges

"""
函数名: is_circle
作用: 通过分析CCD数据，判断是否进入环岛并检测环岛的方向（左环或右环）。

参数:
ccd_data1 (list): 第一个CCD传感器的二值化数据，其中1表示道路，0表示非道路。
ccd_data2 (list): 第二个CCD传感器的二值化数据，用于进一步确认环岛的存在和方向。

返回值: tuple:
如果未检测到环岛，则返回 (False, "nothing")
如果检测到可能的环岛，则返回一个包含两个元素的元组 (True, direction)；
其中 direction 表示环岛方向 ("left" 或 "right")。

说明:
此函数首先调用 find_road_edges 函数获取两个CCD数据的道路左边界、右边界和中线位置。
接着，根据第一个CCD的中线位置判断是否可能进入环岛：如果中线在预设的中心位置64 ± 10范围内，
则认为可能进入环岛。随后，根据第二个CCD的数据进一步判断环岛的方向：
1. 如果左环存在，左边界不变但右边界增宽，且在一定区间内检测到连续的道路标识。
2. 如果右环存在，右边界不变但左边界增宽，且在一定区间内检测到连续的道路标识。
根据这些条件，返回是否检测到环岛及其方向。
"""


def is_circle(ccd_data1, ccd_data2):
    # 注意：正常状态下的左边缘=中线-20，右边缘=中线+20
    # 注意：在入环标志位下，并保持车辆直行，才能继续检测Go_circle_now，防止误检测

    debug = 1  # debug == 1时，Print出每个值来判断哪里有问题
    left_edge1, right_edge1, mid_line1 = find_road_edges(ccd_data1)
    left_edge2, right_edge2, mid_line2 = find_road_edges(ccd_data2)
    width2 = abs(left_edge2 - right_edge2)

    if debug:
        print(f"step1: mid_line1={mid_line1},mid_line2={mid_line2}")
        print(f"step2: left_edge2={left_edge2},right_edge2={right_edge2},width2 = {width2}")

    # Step1：判断近端CCD中线是否在 64 ± 10 以内
    if abs(mid_line1 - 64) < 10:

        # Step2：如果左边缘坐标不变但是总宽度变大，代表右环
        if abs(left_edge2 - 40) <= 5 and width2 > 50:
            # Step3 检查右环的条件
            for i in range(105, 126):
                if ccd_data2[i:i - 10:-1] == [1] * 10:
                    return True, "right"

        # Step2：如果右边缘坐标不变但是总宽度变大，代表左环
        if abs(right_edge2 - 80) <= 5 and width2 > 50:
            # Step3: 检查左环的条件
            for i in range(5, 26):
                if ccd_data2[i:i + 10:1] == [1] * 10:
                    return True, "left"

    return False, "nothing"


"""
函数名: Go_circle_now
作用: 通过比较两组CCD数据的宽度变化来判断是否达到环岛的中点位置，以便决定是否开始环岛导航。

参数:
ccd_data1 (list): 第一个CCD传感器的二值化数据，用于检测环岛的中点位置。
ccd_data2 (list): 第二个CCD传感器的二值化数据，用于与第一个传感器的数据进行比较，以确认是否进入环岛中点。
last_width (int, optional): 上一次测量的宽度，默认值为45。此参数用于与当前宽度进行比较，判断是否进入环岛中点。

返回值: bool:
如果检测到已经到达环岛的中点位置，则返回 True。
如果未到达环岛的中点位置，则返回 False。

说明:
此函数首先使用 find_road_edges 函数从两个CCD数据中获取道路的左边界、右边界和中线位置。
根据第一个CCD数据计算当前道路宽度，如果宽度大于45（表示车辆可能接近环岛中心），函数将进一步检查：
1. 比较上一次测量的宽度（last_width）和当前宽度，判断宽度是否显著减小，减小超过5个单位视为可能到达环岛中点。
2. 比较第二组CCD数据的宽度与第一组的宽度，第二组的宽度应大于第一组，因为第二组CCD扫描到的是第一组前面的更广区域。
如果这些条件满足，函数将返回 True，表示车辆可能已经到达环岛中点，可以开始执行环岛导航程序。
"""


def Go_circle_now(ccd_data1, ccd_data2, last_width=int(45)):
    # 注意，在入环标志位下，才进行Go_circle的检测，防止误判
    left_edge1, right_edge1, mid_line1 = find_road_edges(ccd_data1)
    left_edge2, right_edge2, mid_line2 = find_road_edges(ccd_data2)
    current_width1 = right_edge1 - left_edge1  # 计算当前宽度
    current_width2 = right_edge2 - left_edge2  # 计算当前宽度

    if current_width1 > 45:
        # 判断宽度是否变小,来判断CCD是否扫描到了环的中点位置
        print(f"last_width:{last_width},current_width1:{current_width1},current_width2:{current_width2}")
        if last_width > current_width1 + 5 and current_width2 > current_width1:
            # 此处的 +5 和 current_width1 > 45 都会被车速影响(车速越快，宽度变化速率越快，需要调参)
            # 此时CCD1找到圆环中点，CCD2扫描到CCD1前面的区域，因此2宽度大于1
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
