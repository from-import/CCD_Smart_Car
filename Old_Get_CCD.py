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


"""函数作用：return目前计算出来的阈值"""
def threshold_determination(data):
    # 第一步：找出数据的最大值和最小值,最大值和最小值用于初步估计数据的对比度和分布情况
    # 找出数据列表中的最大值和最小值，确定数据的动态范围。
    max_val = max(data)
    min_val = min(data)
    T = (max_val + min_val) / 2  # 第三步：初始估计阈值

    while True:
        """二值化处理图像，并产生两个组数据
        进入迭代循环，不断调整阈值 T，以逐步逼近最佳阈值。
        将数据分为两组：大于当前阈值 T 的数据 (sum_h) 和小于等于当前阈值 T 的数据 (sum_l)。
        分别计算两组数据的平均值：max_ave 和 min_ave, 更新阈值为两组平均值的平均值 T_last。
        如果新阈值 T_last 与旧阈值 T 的差值小于一个很小的数（如 1e-6），则认为阈值已稳定，终止迭代。
        迭代过程确保阈值在数据分布的基础上进行动态调整，逐步逼近最佳阈值。"""
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
    return T  # 阈值


"""
二值化处理函数，对 CCD 数据进行二值化处理。

参数:
data (list): CCD 数据列表。
all_black_difference_value (float): 全黑时的偏差值，用于判断阈值。
T_old (float): 上一次的阈值，用于全黑情况下的处理。

返回:
list: 二值化后的 CCD 数据。
"""

def binary_thresholding(data,T):
    return [0 if x <= T else 1 for x in data]


"""
函数名：read_ccd_data
函数作用：读取 CCD 数据并进行滤波和二值化处理。

参数: ccd (TSL1401): 已初始化的 CCD 实例。

返回: tuple: 包含处理后的 CCD 数据1 和 CCD 数据2 及其二值化结果。
"""


def read_ccd_data(ccd_data1, ccd_data2,T1,T2):
    # CCD 数据滤波
    filtered_ccd1 = bin_ccd_filter(ccd_data1)
    filtered_ccd2 = bin_ccd_filter(ccd_data2)

    # CCD 数据二值化
    binary_ccd1 = binary_thresholding(filtered_ccd1,T1)
    binary_ccd2 = binary_thresholding(filtered_ccd2,T2)

    return [binary_ccd1, binary_ccd2]


"""
函数名：map_error_to_servo_angle
函数作用：将偏差值映射到舵机角度。

参数:
error (int): 偏差值。
mid_angle (int): 舵机中值角度。
left_max_angle (int): 舵机左转最大角度。
right_max_angle (int): 舵机右转最大角度。

返回: float: 舵机角度。
"""
def map_error_to_servo_angle(error, mid_angle=100, left_max_angle=125, right_max_angle=80):

    if error < 0:
        # 偏差为负数时（左转），将 error 从 [-127, 0] 映射到 [mid_angle, left_max_angle]
        angle = mid_angle + (error / -127) * (left_max_angle - mid_angle)
    else:
        # 偏差为正数时（右转），将 error 从 [0, 127] 映射到 [mid_angle, right_max_angle]
        angle = mid_angle + (error / 127) * (right_max_angle - mid_angle)
    return angle

"""
在直道，偏差（Error）会变得很小，绝对值小于10，控制舵机直行，不转弯。
十字路口都是与270°的弯道连接在一起的。由于十字路口没有两端的黑色引导线，通过CCD采集的数据分析，
计算进入前的3次偏差位置，求出它的斜率，再通过斜率计算出智能小车在十字路口上舵机转弯大小，从而保证小车顺利通过十字路口。
紧跟着就进入270°的弯道。为了防止舵机误判，当上一个偏差与本次的偏差超过某一个值时，保持上一次的偏差，这样就能顺利平滑通过弯道了。
从CCD采集回来小S弯道的数据来看，由于小S弯道的位置偏差较小，而且采用一次元函数动态Kp的方法来控制舵机转弯，
Kp的值可以通过这些小偏差的改变而改变，即Kp=0.05×偏差。因此，可以保证智能车以较高的速度完美通过小S弯道。
"""


"""
函数名：adjust_exposure_time
函数作用：根据反馈的曝光量调整 CCD 的曝光时间。

参数:
ccd (TSL1401): 已初始化的 CCD 实例。
target_exposure (float): 设定的目标曝光量。
kp (float): 调节器的比例增益。

返回: float: 调整后的曝光时间。
"""
def adjust_exposure_time(ccd, target_exposure=0.5, kp=0.1):
    # 曝光时间初始值
    exposure_time = 100

    # 读取当前 CCD 数据并计算其平均值作为实际曝光量
    ccd_data = ccd.get(0)
    actual_exposure = sum(ccd_data) / len(ccd_data)

    # 计算曝光量偏差
    exposure_error = target_exposure - actual_exposure

    # 调整曝光时间
    exposure_time = exposure_time + kp * exposure_error

    # 限制曝光时间在合理范围内
    if exposure_time < 10:
        exposure_time = 10
    elif exposure_time > 1000:
        exposure_time = 1000

    # 设置新的曝光时间
    ccd.set_exposure_time(exposure_time)

    return exposure_time