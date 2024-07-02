import matplotlib.pyplot as plt
from Find_Circle import find_roundabout, detect_roundabout

kuandu = 50
left = [0] * 58 + [1] * 34 + [0] * 36
middle = [0] * 51 + [1] * 26 + [0] * 51
right = [0] * 28 + [1] * 36 + [0] * 64
leftCircle = [1] * 15 + [0] * 36 + [1] * 26 + [0] * 51
rightCircle = [0] * 51 + [1] * 26 + [0] * 36 + [1] * 15


def find_road_edges(ccd_data, lastMiddlePosition=64):
    if lastMiddlePosition is None:
        lastMiddlePosition = 64  # 设置默认值

    start = lastMiddlePosition

    # 初始化 left_edge 和 right_edge
    left_edge = start
    right_edge = start
    print(left_edge)
    print(right_edge)

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
函数名: ImageCreate
作用: 绘制CCD数据图像并在图中标注中线位置和参考线。

参数:
    ccd_data (list): 包含CCD数据的列表，其中1表示道路，0表示非道路。
    name (str): 图像的名称标签，用于图例和标题。
    
说明:
此函数首先调用 `find_road_edges` 函数获取道路的左侧和右侧边界位置，并计算出中线位置。
然后使用Matplotlib库绘制包含以下信息的图像：
- CCD数据曲线（红色）
- 中线位置的竖直线（蓝色实线）
- x=64处的参考竖直线（黑色虚线）

调用案例:
left = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
ImageCreate(left, "left")
"""


def ImageCreate(ccd_data, name, lastMiddlePosition=None):
    left_edge, right_edge, mid_line = find_road_edges(ccd_data)
    plt.figure(figsize=(8, 6))
    plt.plot(ccd_data, label=name, color='red')

    plt.axvline(x=mid_line, color='blue', linestyle='-', label='Middle Line')
    plt.axvline(x=64, color='black', linestyle='--', label='x=64')

    plt.title(name)
    plt.xlabel(f'left, mid_line, right: {left_edge, mid_line, right_edge}')
    plt.ylabel('Value')
    plt.legend()
    plt.show()


ImageCreate(left, "left")
ImageCreate(middle, "middle")
ImageCreate(right, "right")
ImageCreate(leftCircle, "leftCircle", 64)
ImageCreate(rightCircle, "rightCircle", 64)

print(find_roundabout(leftCircle))
print(find_roundabout(rightCircle))
