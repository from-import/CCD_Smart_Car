# 跳变沿检测
# 输入: ccdData,间隔,阈值
# 输出: 跳变沿个数
def start_check(ccdData, interval=3, yuzhi=20):
    tiaobian = 0
    last_tiaobian = 0
    this_tiaobian = 0

    for i in range(45, 100):
        if abs(ccdData[i] - ccdData[i + interval]) > yuzhi:
            this_tiaobian = i
            if this_tiaobian != last_tiaobian + 1:
                tiaobian += 1
            last_tiaobian = this_tiaobian

    return tiaobian


def find_road_edges_diff(ccd_diff, threshold=80, last_middle_position=None):
    """
    道路边缘检测函数，根据 CCD 差分数据进行边缘检测和更新。

    参数:
    ccd_diff (list): CCD 差分数据列表。例如: [0, 1, -1, 0, 1, -1, 0, ...]
    threshold (float): 阈值。例如: 80。用于识别边缘的差分阈值。
    last_middle_position (int): 上次检测到的中线位置。例如: 64。如果为 None，则默认为 64。

    返回:
    tuple: 包含以下元素的元组：
        - left_edge (int): 检测到的左边缘位置。例如: 20
        - right_edge (int): 检测到的右边缘位置。例如: 100
        - mid_line (int): 计算的中线位置。例如: 60
        - rising_edge_cnt (int): 上升沿计数。例如: 3
        - falling_edge_cnt (int): 下降沿计数。例如: 3
        - rising_edge (list): 上升沿位置列表。例如: [20, 50, 80, 0, 0]
        - falling_edge (list): 下降沿位置列表。例如: [100, 130, 160, 0, 0]
    """
    if last_middle_position is None:
        last_middle_position = 64  # 设置默认值

    max_peaks = 5
    rising_edge = [0] * max_peaks
    falling_edge = [0] * max_peaks
    rising_edge_cnt = 0
    falling_edge_cnt = 0

    # 寻找正峰值和负峰值
    for i in range(4, 127):
        if (ccd_diff[i] >= ccd_diff[i - 1]) and (ccd_diff[i] > ccd_diff[i + 1]) and (ccd_diff[i] > threshold):
            if rising_edge_cnt < max_peaks:
                rising_edge[rising_edge_cnt] = i
                rising_edge_cnt += 1
        if (ccd_diff[i] < ccd_diff[i - 1]) and (ccd_diff[i] <= ccd_diff[i + 1]) and (ccd_diff[i] < -threshold):
            if falling_edge_cnt < max_peaks:
                falling_edge[falling_edge_cnt] = i
                falling_edge_cnt += 1

    def find_nearest(mode, last_edge):
        if mode == 'left':
            for i in range(rising_edge_cnt):
                if abs(last_edge - rising_edge[i]) <= 3:
                    return rising_edge[i]
        else:
            for i in range(falling_edge_cnt):
                if abs(last_edge - falling_edge[i]) <= 3:
                    return falling_edge[i]
        return None

    # 使用上次中线位置进行左右边界的初始检测
    left_edge = find_nearest('left', last_middle_position)
    right_edge = find_nearest('right', last_middle_position)

    # 如果未找到边界，使用边界扫描
    if left_edge is None:
        for i in range(last_middle_position, 0, -1):
            if ccd_diff[i] > threshold:
                left_edge = i
                break
    if right_edge is None:
        for i in range(last_middle_position, len(ccd_diff)):
            if ccd_diff[i] < -threshold:
                right_edge = i
                break

    # 确保扫描结果有效
    if left_edge is None:
        left_edge = 0
    if right_edge is None:
        right_edge = len(ccd_diff) - 1

    # 计算中线
    if left_edge is not None and right_edge is not None:
        mid_line = (left_edge + right_edge) // 2
    else:
        mid_line = 64 if last_middle_position is None else last_middle_position  # 未检测到左右边界

    # 返回左边界、右边界和中线位置的元组
    return left_edge, right_edge, mid_line, rising_edge_cnt, falling_edge_cnt, rising_edge, falling_edge



def normal(ccd_data, left_last_find, right_last_find, rising_edge_cnt, falling_edge_cnt,
           rising_edge, falling_edge, road_type, last_left, last_right, ccd_diff, threshold):
    """
    普通道路处理函数，根据 CCD 数据进行道路边缘检测和更新。

    参数:
    ccd_data (list): CCD 数据列表。例如: [0, 0, 1, 1, 0, 0, 1, 1, ...]
    left_last_find (int): 上次找到左边缘的标志位。例如: 0 或 1
    right_last_find (int): 上次找到右边缘的标志位。例如: 0 或 1
    rising_edge_cnt (int): 上升沿计数。例如: 2
    falling_edge_cnt (int): 下降沿计数。例如: 3
    rising_edge (list): 上升沿位置列表。例如: [10, 20, 30, 0, 0]
    falling_edge (list): 下降沿位置列表。例如: [50, 60, 70, 0, 0]
    road_type (int): 道路类型。例如: 0 表示普通道路, 1 表示十字路口, 2 表示障碍物, 3 表示坡道
    last_left (int): 上次检测到的左边缘位置。例如: 20
    last_right (int): 上次检测到的右边缘位置。例如: 60
    ccd_diff (list): CCD 差分数据列表。例如: [0, 1, -1, 0, 1, -1, 0, ...]
    threshold (float): 阈值。例如: 0.5

    返回:
        更新后的左边缘位置 (left)
        更新后右边缘位置 (right)
        左边缘标志位 (left_last_find)
        右边缘标志位 (right_last_find)
        参考宽度 (reference_width)
        道路类型 (road_type)
    """
    reference_width = 44
    left, right = last_left, last_right
    left_find, right_find = 0, 0

    def find_nearest(mode, last_edge):
        nonlocal rising_edge, falling_edge, rising_edge_cnt, falling_edge_cnt
        find = 0
        if mode == 'left':
            if rising_edge_cnt != 0:
                for index in range(rising_edge_cnt):
                    if abs(last_edge - rising_edge[index]) <= 3:
                        find = 1
                        break
        else:
            if falling_edge_cnt != 0:
                for index in range(falling_edge_cnt):
                    if abs(last_edge - falling_edge[index]) <= 3:
                        find = 1
                        break
        return find

    def find_boundary(mode):
        nonlocal rising_edge, falling_edge, rising_edge_cnt, falling_edge_cnt
        find = 0
        if mode == 'left':
            if rising_edge_cnt != 0:
                for index in range(rising_edge_cnt - 1, -1, -1):
                    if rising_edge[index] < 75:
                        find = 1
                        break
        else:
            if falling_edge_cnt != 0:
                for index in range(falling_edge_cnt):
                    if falling_edge[index] > 53:
                        find = 1
                        break
        return find

    def find_both_line(ccd_diff, threshold):
        nonlocal rising_edge, falling_edge, rising_edge_cnt, falling_edge_cnt, left_last_find, right_last_find, left, right

        rising_edge_cnt, falling_edge_cnt = 0, 0

        for i in range(3, len(ccd_diff)):
            ccd_diff[i] = ccd_data[i] - ccd_data[i - 3]
            if abs(ccd_diff[i]) > threshold:
                if ccd_diff[i] > 0 and rising_edge_cnt < 5:
                    rising_edge[rising_edge_cnt] = i
                    rising_edge_cnt += 1
                elif ccd_diff[i] < 0 and falling_edge_cnt < 5:
                    falling_edge[falling_edge_cnt] = i
                    falling_edge_cnt += 1

        if rising_edge_cnt > 0 and falling_edge_cnt > 0:
            left = rising_edge[0]
            right = falling_edge[0]
            left_last_find = 1
            right_last_find = 1

    if left_last_find == 0 and right_last_find == 0:  # 上次没有边线
        find_both_line(ccd_diff, threshold)
        if left_last_find == 0 and right_last_find == 0:
            if find_boundary('left'):
                left = rising_edge[0]
                left_last_find = 1
            else:
                left_last_find = 0
            if find_boundary('right'):
                right = falling_edge[0]
                right_last_find = 1
            else:
                right_last_find = 0
            if left_last_find and right_last_find:
                if right < left:
                    left_last_find = 0
                    right_last_find = 0
    else:
        if left_last_find:  # 上次找到了左线
            if find_nearest('left', left):
                left = rising_edge[0]
                left_last_find = 1
                if right_last_find == 0:  # 上次找到左线，这次找到左线，上次没找到右线
                    if falling_edge_cnt:  # 上次找到左线，这次找到左线，上次没找到右线，这次找到右线
                        for index in range(falling_edge_cnt):
                            right_find = 0
                            if falling_edge[index] > left:
                                tempwidth = falling_edge[index] - left
                                if abs(tempwidth - reference_width) >= 2:
                                    if tempwidth > reference_width:
                                        reference_width += 1
                                    else:
                                        reference_width -= 1
                                    right = left + reference_width
                                    right_last_find = 0
                                else:
                                    right = falling_edge[index]
                                    right_last_find = 1
                                right_find = 1
                                break
                        if right_last_find == 0 and right_find == 0:
                            right = left + reference_width
                    else:
                        right = left + reference_width
            else:
                left_last_find = 0
                if find_boundary('left'):
                    if rising_edge[0] < left:
                        if right_last_find == 0 and ((road_type != 2) and (road_type != 3)):
                            road_type = 1
                    elif rising_edge[0] < left + 8:
                        left = rising_edge[0]
                        left_last_find = 1
                else:
                    if right_last_find == 0 and (road_type != 4):
                        road_type = 1
        if right_last_find:  # 上次找到了右线
            if find_nearest('right', right):
                right = falling_edge[0]
                right_last_find = 1
                if left_last_find == 0:  # 上次找到了右线,这次能找到右线,上次找不到左线
                    if rising_edge_cnt > 0:
                        for index in range(rising_edge_cnt - 1, -1, -1):
                            left_find = 0
                            if rising_edge[index] < right:
                                tempwidth = right - rising_edge[index]
                                if abs(tempwidth - reference_width) >= 2:
                                    if tempwidth > reference_width:
                                        reference_width += 1
                                    else:
                                        reference_width -= 1
                                    left = right - reference_width
                                    left_last_find = 0
                                else:
                                    left = rising_edge[index]
                                    left_last_find = 1
                                left_find = 1
                                break
                        if left_last_find == 0 and left_find == 0:
                            left = right - reference_width
                    else:
                        left = right - reference_width
            else:
                right_last_find = 0
                if find_boundary('right'):
                    if falling_edge[0] > right:
                        if left_last_find == 0 and ((road_type != 2) and (road_type != 3)):
                            road_type = 1
                    elif falling_edge[0] > right - 8:
                        right = falling_edge[0]
                        right_last_find = 1
                else:
                    if left_last_find == 0 and (road_type != 4):
                        road_type = 1
        if right_last_find and left_last_find:
            reference_width = right - left
            if reference_width < 35:
                reference_width = 35

    return left, right, left_last_find, right_last_find, reference_width, road_type
