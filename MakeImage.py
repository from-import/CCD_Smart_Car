import matplotlib.pyplot as plt

left = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
middle = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
          1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
right = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
         1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def find_road_edges(ccd_data, lastMiddlePosition=None):
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
def ImageCreate(ccd_data, name):
    left_edge, right_edge, mid_line = find_road_edges(ccd_data, None)
    plt.figure(figsize=(8, 6))
    plt.plot(ccd_data, label=name, color='red')

    # 添加竖直线
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