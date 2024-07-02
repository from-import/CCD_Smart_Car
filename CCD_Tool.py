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

    # 初始化 left_edge 和 right_edge
    left_edge = start
    right_edge = start


    # 向左扫描
    while left_edge > 0 and ccd_data[left_edge] == 1:
        left_edge -= 1

    # 向右扫描
    while right_edge < len(ccd_data) - 1 and ccd_data[right_edge] == 1:
        right_edge += 1

    # 确保扫描结果有效
    if left_edge == start and ccd_data[left_edge] == 1:
        left_edge = 0
    if right_edge == start and ccd_data[right_edge] == 1:
        right_edge = len(ccd_data) - 1

    # 如果没有检测到左边界或右边界,启用丢单线算法
    if (left_edge == start or left_edge == 0) and right_edge != start:
        mid_line = right_edge - 25  # 仅检测到右边界
    elif (right_edge == start or right_edge == len(ccd_data) - 1) and left_edge != start:
        mid_line = left_edge + 25  # 仅检测到左边界
    elif right_edge != start and left_edge != start:
        mid_line = (left_edge + right_edge) // 2  # 检测到左右边界
    else:
        mid_line = 64 if lastMiddlePosition is None else lastMiddlePosition  # 未检测到左右边界

    return left_edge, right_edge, mid_line  # 返回左边界、右边界和中线位置的元组

"""
函数名: detect_start_line
作用: 检测CCD数据缓冲区中的起跑线(斑马线)。

参数:
    ccd_buf (list): 包含128个元素的列表，表示CCD数据。每个元素为0（黑色）或1（白色）。

返回值:
    int: 如果检测到有效的起跑线，则返回1；否则返回0。

说明:
    此函数遍历 `ccd_buf` 数组，寻找符合起跑线条件的像素序列。
    它检查连续的5个像素是否满足以下条件：
    - 当前像素及其下一个像素的值为1。
    - 接下来的三个像素值为0。
    如果找到满足条件的序列，确定起跑线的左右边界。
    如果连续找到五个这样的序列，则设置 `getinto_garage_flag` 为1并返回。

示例用法:
    detect_start_line(ccd_buf)
"""


def detect_start_line(ccd_buf):
    getinto_garage_flag = 0
    cntColorChange = 0
    jLeft = 0
    jRight = 0

    for i in range(124):  # 遍历到123（包含）
        if (ccd_buf[i] == 1 and
                ccd_buf[i + 1] == 1 and
                ccd_buf[i + 2] == 0 and
                ccd_buf[i + 3] == 0 and
                ccd_buf[i + 4] == 0):

            jLeft = i + 2

            for iTmp in range(jLeft, 124):
                if (ccd_buf[iTmp] == 0 and
                        ccd_buf[iTmp + 1] == 0 and
                        ccd_buf[iTmp + 2] == 1 and
                        ccd_buf[iTmp + 3] == 1 and
                        ccd_buf[iTmp + 4] == 1):
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



