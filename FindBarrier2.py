from CCD_Tool import find_road_edges

"""
障碍处理函数1

函数名: obstacle_deal

参数:
    line (list): 包含二值化后的CCD数据，其中1表示道路，0表示非道路。

返回值:
    tuple: 返回一个元组，依次为障碍开始位置(obstacle_down)，障碍结束位置(obstacle_up)，
           障碍宽度(obstacle_width)，障碍轴心位置(obstacle_axis)，左侧障碍标志(L_Obstacle)，
           右侧障碍标志(R_Obstacle)，以及障碍检测标志(obstacle)。

说明:
此函数首先遍历CCD数据，检测障碍的开始和结束位置，并计算障碍宽度和位置。
然后，根据设定的条件和阈值判断是否检测到障碍，并处理障碍的离开过程。
函数包含多个参数和变量，用于控制障碍检测和处理的过程。

调用案例:
ccd_data = [0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1]
result = obstacle_deal(ccd_data)
print("障碍检测结果:", result)
"""


def obstacle_deal(line):
    left_edge, right_edge, mid_position = find_road_edges(line)  # 中线位置
    obstacle_flag_down = 0
    obstacle_flag_up = 0
    LxQ4 = 0
    RxQ4 = 0
    Down_sec_Q = 0
    obstacle_width = 0
    obstacle_axis = 0

    # 假定的测试值
    right_black2 = 100  # 替换为实际值
    left_black2 = 50  # 替换为实际值
    CCD3_width = right_black2 - left_black2

    # 初始化参数
    obstacle_down = 0
    obstacle_up = 0
    L_Obstacle = 0
    R_Obstacle = 0
    obstacle = 0
    obstacle_flag = 0

    threshold2 = 1  # 定义合适的阈值
    obstacle_count = 3  # 定义需要检测到的障碍数量
    s_bar = 0
    car_speed = 10  # 定义车速
    s_bar_cnt = 100  # 定义合适的S_bar计数值

    # 遍历CCD数组，检测障碍的开始和结束位置
    for i in range(24, 103):
        if line[i] - line[i + 3] >= threshold2:
            obstacle_flag_down += 1
            if obstacle_flag_down >= 3:
                obstacle_down = i
                LxQ4 = 1
                for j in range(obstacle_down, 100):
                    if line[j + 3] - line[j] >= threshold2:
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
                    else:
                        obstacle_flag_up = 0
                break
        else:
            obstacle_flag_down = 0

    # 如果检测到的障碍不满足条件，则重置
    if obstacle_flag_up < 3:
        obstacle_up = 0
    if obstacle_flag_down < 3:
        obstacle_down = 0

    # 判断是否开启障碍处理
    obstacle_switch = True
    mid_black = 0
    zhijiao = 0
    black_area = 0
    podao = 0
    start = 1
    offset = 0  # 替换为实际值

    if (obstacle_switch and mid_black == 0 and zhijiao == 0 and black_area == 0 and podao == 0 and start != 0):
        # 根据条件更新障碍标志
        if 10 <= obstacle_width <= 18 and abs(offset) <= 15 and 10 <= CCD3_width <= 45:
            obstacle_flag += 1
        else:
            obstacle_flag = 0

        # 如果障碍标志达到指定数量，则认为检测到障碍
        if obstacle_flag >= obstacle_count:
            obstacle = 1

        if obstacle:
            if L_Obstacle:
                left_black = 90
            else:
                right_black = 43
            # Beep() # 替换为适当的蜂鸣器函数
        else:
            # NoBeep() # 替换为适当的关闭蜂鸣器函数
            pass

        # 处理离开障碍
        if obstacle == 1:
            s_bar += car_speed
            if s_bar >= s_bar_cnt:
                s_bar = 0
                obstacle = 0

    return obstacle_down, obstacle_up, obstacle_width, obstacle_axis, L_Obstacle, R_Obstacle, obstacle
