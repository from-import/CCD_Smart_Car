from machine import *
from seekfree import TSL1401


"""
函数名: detect_start_line(ccd_buf, start_line_thres)
作用: 检测CCD数据缓冲区中的起跑线(斑马线)。

参数:
    ccd_buf (list): 包含128个元素的列表，表示CCD数据。每个元素为0（白色）或1（黑色）。
    start_line_thres (int): 用于确定起跑线存在的阈值。

返回值:
    int: 如果检测到有效的起跑线，则返回1；否则返回0。

说明:
    此函数遍历 `ccd_buf` 数组，寻找符合起跑线条件的像素序列。
    它检查连续的5个像素是否满足以下条件：
    - 当前像素及其下一个像素的值大于 `start_line_thres`。
    - 接下来的三个像素值小于 `start_line_thres`。
    如果找到满足条件的序列，确定起跑线的左右边界。
    如果连续找到五个这样的序列，则设置 `getinto_garage_flag` 为1并返回。

示例用法:
    ccd_buf = [0] * 128  # 初始化为128个零
    start_line_thres = 100  # 起跑线阈值
    getinto_garage_flag = detect_start_line(ccd_buf, start_line_thres)
    print("getinto_garage_flag:", getinto_garage_flag)
"""
def detect_start_line(ccd_buf, start_line_thres):
    cntColorChange = 0
    getinto_garage_flag = 0
    jLeft = 0
    jRight = 0

    for i in range(124):  # Iterate up to 123 (inclusive)
        if (ccd_buf[i] > start_line_thres and
                ccd_buf[i + 1 if i + 1 < 128 else 127] > start_line_thres and
                ccd_buf[i + 2 if i + 2 < 128 else 127] < start_line_thres and
                ccd_buf[i + 3 if i + 3 < 128 else 127] < start_line_thres and
                ccd_buf[i + 4 if i + 4 < 128 else 127] < start_line_thres):

            jLeft = i + 2

            for iTmp in range(jLeft, 124):
                if (ccd_buf[iTmp] < start_line_thres and
                        ccd_buf[iTmp + 1] < start_line_thres and
                        ccd_buf[iTmp + 2] > start_line_thres and
                        ccd_buf[iTmp + 3] > start_line_thres and
                        ccd_buf[iTmp + 4] > start_line_thres):

                    jRight = iTmp + 1
                    break

            if jRight - jLeft > 2:
                cntColorChange += 1

            if cntColorChange >= 5:
                cntColorChange = 0
                getinto_garage_flag = 1
                break

    return getinto_garage_flag



"""
find_road_edges : 查找道路左侧和右侧的边界位置，并计算中线位置。

参数:
binary_data (list): 二值化后的CCD数据，1表示道路，0表示非道路。

返回:
tuple: 包含左侧边界索引(left_edge)、右侧边界索引(right_edge)和中线位置(mid_line)的元组。

调用案例: left,right,middle = find_road_edges(ccd1)
"""
def find_road_edges(binary_data):
    left_edge = None
    right_edge = None

    for i in range(len(binary_data)):
        if binary_data[i] == 1 and left_edge is None:
            left_edge = i
        if binary_data[i] == 0 and left_edge is not None:
            right_edge = i - 1
            break

    return left_edge ,right_edge




"""
CCD_Error(binary_data) : 查找道路左侧和右侧的边界位置，并计算中线位置。

参数:
binary_data (list): 二值化后的CCD数据，1表示道路，0表示非道路。

返回:
误差值
"""
def CCD_Error(binary_data):
    left_edge = None
    right_edge = None

    for i in range(len(binary_data)):
        if binary_data[i] == 1 and left_edge is None:
            left_edge = i
        if binary_data[i] == 0 and left_edge is not None:
            right_edge = i - 1
            break

    return int(0.5 * (left_edge + right_edge)) - 64



"""

detect_roundabout : 判断是否进入环岛。

函数名: detect_roundabout(binary_data)

作用: 分析二值化后的CCD数据，判断是否存在环岛。

参数:
binary_data (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值:
bool: 如果检测到可能的环岛（根据道路宽度和中线偏移量），则返回True；否则返回False。

说明:
此函数首先调用 find_road_edges 函数获取道路的左侧和右侧边界位置，并计算出中线位置。
然后根据道路宽度和中线偏移量进行判断：
- 如果道路宽度大于90或小于40，或者中线偏移量绝对值大于20，则判定可能进入环岛。
- 否则，返回False。

调用案例:
binary_data = [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1]
is_roundabout = detect_roundabout(binary_data)
print("是否进入环岛:", is_roundabout)
"""




def detect_roundabout(binary_data):
    left_edge, right_edge = find_road_edges(binary_data)

    if left_edge is not None and right_edge is not None:
        road_width = right_edge - left_edge
        middle_error = int(0.5 * (left_edge + right_edge)) - 64

        # 根据道路宽度和中线偏移量判断是否进入环岛
        if road_width > 90 or road_width < 40 or abs(middle_error) > 20:
            return 1

    return 0

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




"""
避障算法函数名: detect_obstacle(ccd_buf, obstacle_threshold)

作用: 检测障碍物。

参数:
    ccd_buf (list): 包含128个元素的列表，表示CCD数据。每个元素为0（白色）或1（黑色）。
    obstacle_threshold (int): 用于确定障碍物存在的阈值。

返回值:
    int: 如果检测到障碍物，则返回1；否则返回0。

说明:
    此函数遍历 `ccd_buf` 数组，寻找连续的黑色区域，其长度超过阈值 `obstacle_threshold`。
    如果找到符合条件的障碍物区域，则返回1；否则返回0。

示例用法:
    ccd_buf = [0] * 128  # 初始化为128个零
    obstacle_threshold = 5  # 障碍物长度阈值
    obstacle_detected = detect_obstacle(ccd_buf, obstacle_threshold)
    print("是否检测到障碍物:", obstacle_detected)
    
"""
def detect_obstacle(ccd_buf, obstacle_threshold = 10):
    obstacle_detected = 0
    black_count = 0

    for pixel in ccd_buf:
        if pixel == 1:
            black_count += 1
        else:
            if black_count >= obstacle_threshold:
                obstacle_detected = 1
                break
            black_count = 0

    if black_count >= obstacle_threshold:
        obstacle_detected = 1

    return obstacle_detected


def detect_obstacle(line):
    """
    避障算法函数名: detect_obstacle(line)

    作用: 检测障碍物。

    参数:
        line (list): 包含128个元素的列表，表示CCD数据。每个元素为0（白色）或1（黑色）。

    返回值:
        int: 如果检测到障碍物，则返回1；否则返回0。

    说明:
        此函数模拟C语言中的障碍物检测函数。首先进行连续下降的黑色区域检测，然后根据一定的条件判断是否存在障碍物。
        如果符合障碍物条件，则设置全局变量，并根据情况进行其他相关处理。
        最后返回1表示检测到障碍物，返回0表示未检测到障碍物。

    示例用法:
        ccd_data = [0] * 128  # 初始化为128个零
        obstacle_detected = detect_obstacle(ccd_data)
        print("是否检测到障碍物:", obstacle_detected)
    """
    global obstacle, offset, LeftBlack, RightBlack, CCD3_width, obstacle_flag, obstacle_conut, Start
    global Obstacle_Switch, mid_black, zhijiao, black_area, podao, LxQ4, RxQ4, L_Obstacle, R_Obstacle

    obstacle_flag_down = 0
    obstacle_flag_up = 0
    obstacle_width = 0
    obstacle_axis = 0
    CCD3_width = RightBlack2 - LeftBlack2  # 需要根据具体情况调整

    for i in range(24, 103):
        if (line[i] - line[i + 3]) >= Threshold2:
            obstacle_flag_down += 1
            if obstacle_flag_down >= 3:
                obstacle_down = i
                LxQ4 = 1
                for j in range(obstacle_down, 100):
                    if (line[j + 3] - line[j]) >= Threshold2:
                        obstacle_flag_up += 1
                        if obstacle_flag_up >= 3:
                            obstacle_up = j
                            obstacle_width = obstacle_up - obstacle_down
                            obstacle_axis = (obstacle_up + obstacle_down) // 2
                            if obstacle_down > 64 and obstacle_up > 64:
                                L_Obstacle = 0
                                R_Obstacle = 1
                            elif obstacle_down < 64 and obstacle_up < 64:
                                L_Obstacle = 1
                                R_Obstacle = 0
                            RxQ4 = 1
                            break
                break
        else:
            obstacle_flag_down = 0

    if obstacle_flag_up < 3:
        obstacle_up = 0
    if obstacle_flag_down < 3:
        obstacle_down = 0

    if Obstacle_Switch and mid_black == 0 and zhijiao == 0 and black_area == 0 and podao == 0 and Start != 0:
        if 10 <= obstacle_width <= 18 and abs(offset) <= 15 and 10 <= CCD3_width <= 45:
            obstacle_flag += 1
        else:
            obstacle_flag = 0

        if obstacle_flag >= obstacle_conut:
            obstacle = 1

        if obstacle:
            if L_Obstacle:
                LeftBlack = 90
            else:
                RightBlack = 43
            # Beep()  # 某种声音信号处理函数

    else:
        # NoBeep()  # 某种非障碍状态下的声音信号处理函数
        pass

    # 出障碍处理
    if obstacle == 1:
        S_bar += CarSpeed
        if S_bar >= S_bar_cnt:
            S_bar = 0
            obstacle = 0

    return 1 if obstacle else 0
