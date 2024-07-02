import matplotlib.pyplot as plt
from CCD_Tool import find_road_edges
from Find_Circle import is_circle
from Find_Barrier import find_barrier


width = 50
left = [0] * 58 + [1] * 34 + [0] * 36
middle = [0] * 51 + [1] * 26 + [0] * 51
right = [0] * 28 + [1] * 36 + [0] * 64

leftCircle = [1] * 15 + [0] * 36 + [1] * 26 + [0] * 51
rightCircle = [0] * 51 + [1] * 26 + [0] * 36 + [1] * 15

rightBarrier = [0]*51 + [1]*13 + [1]*3 + [0]*10 + [0]*51
leftBarrier = [0]*51 + [0]*10 + [1]*3 + [1]*13 + [0]*51

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



def ImageCreate(ccd_data, name, lastMiddlePosition=64):
    left_edge, right_edge, mid_line = find_road_edges(ccd_data,lastMiddlePosition)
    plt.figure(figsize=(8, 6))
    plt.plot(ccd_data, label=name, color='red')

    plt.axvline(x=mid_line, color='blue', linestyle='-', label='Middle Line')
    plt.axvline(x=64, color='black', linestyle='--', label='x=64')

    plt.title(name)
    plt.xlabel(f'left, mid_line, right: {left_edge, mid_line, right_edge}')
    plt.ylabel('Value')
    plt.legend()
    plt.show()

def ImageCreate2(ccd_data, name):
    plt.figure(figsize=(8, 6))
    plt.plot(ccd_data, label=name, color='red')
    plt.axvline(x=64, color='black', linestyle='--', label='x=64')
    plt.title(name)
    plt.xlabel(f'Null')
    plt.ylabel('Value')
    plt.legend()
    plt.show()

ImageCreate(left, "left")
ImageCreate(middle, "middle")
ImageCreate(right, "right",40)
ImageCreate(leftCircle, "leftCircle", 64)
ImageCreate(rightCircle, "rightCircle", 64)
ImageCreate2(leftBarrier, "leftBarrier")
ImageCreate2(rightBarrier, "rightBarrier")
print(is_circle(leftCircle))
print(is_circle(rightCircle))

ImageCreate(leftBarrier, "leftBarrier", 64)
ImageCreate(rightBarrier, "rightBarrier", 64)
print(find_barrier(leftBarrier,27))
print(find_barrier(rightBarrier,28))
