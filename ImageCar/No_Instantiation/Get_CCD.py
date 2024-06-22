from machine import *
from seekfree import TSL1401

def read_ccd_data(ccd):
    """
    读取 CCD 数据并进行滤波和二值化处理。

    参数:
    ccd (TSL1401): 已初始化的 CCD 实例。

    返回:
    tuple: 包含处理后的 CCD 数据1 和 CCD 数据2 及其二值化结果。
    """

    def get_mid(a, b, c):
        # 获取三个值中的中间值。
        x = 0
        if a > b:
            x = b
            b = a
            a = x
        if b > c:
            x = c
            c = b
            b = x
        if a > b:
            x = b
            b = a
            a = x
        return b

    def bin_ccd_filter(data):
        # 中值滤波函数，对 CCD 数据进行中值滤波处理。
        filtered_data = []
        # 对128个点进行平滑处理输出
        for i in range(1, len(data) - 1):
            mid_value = get_mid(data[i - 1], data[i], data[i + 1])
            filtered_data.append(mid_value)
        # 处理边界条件：保留第一个和最后一个数据点
        filtered_data.insert(0, data[0])
        filtered_data.append(data[-1])
        return filtered_data

    def binary_thresholding(data, all_black_difference_value=10, T_old=128):
        """
        二值化处理函数，对 CCD 数据进行二值化处理。

        参数:
        data (list): CCD 数据列表。
        all_black_difference_value (float): 全黑时的偏差值，用于判断阈值。
        T_old (float): 上一次的阈值，用于全黑情况下的处理。

        返回:
        list: 二值化后的 CCD 数据。
        """
        # 第一步：找出数据的最大值和最小值,最大值和最小值用于初步估计数据的对比度和分布情况
        # 找出数据列表中的最大值和最小值，确定数据的动态范围。
        max_val = max(data)
        min_val = min(data)

        # 第二步：判断最大值和最小值的偏差是否大于全黑时的偏差值
        # 如果差值小于或等于这个偏差值，则认为数据是全黑的
        # 在全黑情况下，使用上一次的阈值(T_old)进行二值化，避免在全黑情况下计算新的阈值
        if (max_val - min_val) <= all_black_difference_value:
            return [0 if x <= T_old else 1 for x in data]

        # 第三步：初始估计阈值
        T = (max_val + min_val) / 2

        while True:
            """
            第四步：二值化处理图像，并产生两个组数据
            进入迭代循环，不断调整阈值 T，以逐步逼近最佳阈值。
            将数据分为两组：大于当前阈值 T 的数据 (sum_h) 和小于等于当前阈值 T 的数据 (sum_l)。
            分别计算两组数据的平均值：max_ave 和 min_ave, 更新阈值为两组平均值的平均值 T_last。
            如果新阈值 T_last 与旧阈值 T 的差值小于一个很小的数（如 1e-6），则认为阈值已稳定，终止迭代。
            迭代过程确保阈值在数据分布的基础上进行动态调整，逐步逼近最佳阈值。
            """

            sum_h = [x for x in data if x > T]
            sum_l = [x for x in data if x <= T]
            if len(sum_h) == 0:
                max_ave = 0
            else:
                max_ave = sum(sum_h) / len(sum_h)
            if len(sum_l) == 0:
                min_ave = 0
            else:
                min_ave = sum(sum_l) / len(sum_l)

            # 第六步：计算最终的阈值
            T_last = (max_ave + min_ave) / 2

            # 检查阈值是否稳定
            if abs(T_last - T) < 1e-6:
                break

            T = T_last

        # 返回二值化后的数据
        return [0 if x <= T_last else 1 for x in data]

    # 读取 CCD 数据
    ccd_data1 = ccd.get(0)
    ccd_data2 = ccd.get(1)

    # CCD 数据滤波
    filtered_ccd1 = bin_ccd_filter(ccd_data1)
    filtered_ccd2 = bin_ccd_filter(ccd_data2)

    # CCD 数据二值化
    binary_ccd1 = binary_thresholding(filtered_ccd1)
    binary_ccd2 = binary_thresholding(filtered_ccd2)

    return binary_ccd1, binary_ccd2


def calculate_error_and_kp(left_black, right_black):
    """
    计算偏差值和动态 Kp 值。

    参数:
    left_black (int): 左侧黑点位置。
    right_black (int): 右侧黑点位置。

    返回:
    tuple: 包含偏差值 (Error) 和动态 Kp 值。
    """
    # 计算偏差值
    error = left_black - (128 - right_black)

    # 计算动态 Kp 值
    kp = 0.05 * abs(error)

    return error, kp


def adjust_steering(error):
    """
    调整舵机转弯方向和速度。

    参数:
    error (int): 偏差值。

    返回:
    str: 舵机调整方向和速度信息。
    """
    if error < -10:
        return "舵机向左转弯"
    elif error > 10:
        return "舵机向右转弯"
    else:
        return "舵机直行，不转弯"

def map_error_to_servo_angle(error, mid_angle=100, left_max_angle=125, right_max_angle=80):
    """
    将偏差值映射到舵机角度。

    参数:
    error (int): 偏差值。
    mid_angle (int): 舵机中值角度。
    left_max_angle (int): 舵机左转最大角度。
    right_max_angle (int): 舵机右转最大角度。

    返回:
    float: 舵机角度。
    """
    if error < 0:
        # 偏差为负数时（左转），将 error 从 [-127, 0] 映射到 [mid_angle, left_max_angle]
        angle = mid_angle + (error / -127) * (left_max_angle - mid_angle)
    else:
        # 偏差为正数时（右转），将 error 从 [0, 127] 映射到 [mid_angle, right_max_angle]
        angle = mid_angle + (error / 127) * (right_max_angle - mid_angle)
    return angle

def process_ccd_data(ccd_data):
    """
    处理 CCD 数据以识别赛道类型并调整舵机。

    参数:
    ccd_data (list): CCD 数据列表。

    返回:
    dict: 包含偏差值、Kp 值和调整方向信息。

    在直道，偏差（Error）会变得很小，绝对值小于10，控制舵机直行，不转弯。
    十字路口都是与270°的弯道连接在一起的。由于十字路口没有两端的黑色引导线，通过CCD采集的数据分析，
    计算进入前的3次偏差位置，求出它的斜率，再通过斜率计算出智能小车在十字路口上舵机转弯大小，从而保证小车顺利通过十字路口。
    紧跟着就进入270°的弯道。为了防止舵机误判，当上一个偏差与本次的偏差超过某一个值时，保持上一次的偏差，这样就能顺利平滑通过弯道了。
    从CCD采集回来小S弯道的数据来看，由于小S弯道的位置偏差较小，而且采用一次元函数动态Kp的方法来控制舵机转弯，
    Kp的值可以通过这些小偏差的改变而改变，即Kp=0.05×偏差。因此，可以保证智能车以较高的速度完美通过小S弯道。
    """
    left_black = ccd_data.index(max(ccd_data[:64]))  # 找到左侧黑点位置
    right_black = ccd_data.index(max(ccd_data[64:])) + 64  # 找到右侧黑点位置

    # 计算 superError
    indices_with_value_1 = [i for i, v in enumerate(ccd_data) if v == 1]
    if indices_with_value_1:
        weighted_average_index = sum(indices_with_value_1) / len(indices_with_value_1)
    else:
        weighted_average_index = 64  # 如果没有值为 1 的索引，默认值为 64

    super_error = weighted_average_index - 64

    error, kp = calculate_error_and_kp(left_black, right_black)
    steering_adjustment = adjust_steering(error)

    return error, kp, steering_adjustment, super_error

