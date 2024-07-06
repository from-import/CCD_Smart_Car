from machine import *
from seekfree import MOTOR_CONTROLLER
from smartcar import encoder
import gc
import time

# 初始化全局变量
dutyL = 0
dutyR = 0
errorl = 0
errorR = 0
error_pre_lastl = 0
error_pre_lastr = 0
error_prel = 0
error_prer = 0
dir_error = 0
dir_error_last = 0
Dir_value = 0

# 定义一些常量用于电机控制和PID参数
MOTOR_P = 1
MOTOR_I = 5
MOTOR_D = 0
DIR_P = 0
DIR_I = 1
DIR_D = 0
SPEED_L = 40
SPEED_R = 40
DUTY_LIMIT_HIGH = 5000
DUTY_LIMIT_LOW = -3000
ERROR_THRESHOLD = 15

"""
control_encoder:读取编码器数据并计算实际速度

参数:
encoder_l (encoder): 已初始化的左编码器实例
encoder_r (encoder): 已初始化的右编码器实例
"""


def control_encoder(encoder_l, encoder_r):
    global encl_data, encr_data

    # 通过 get 接口读取数据
    encl_data = encoder_l.get()
    encr_data = encoder_r.get()

    # 计算小车的实际速度
    # 速度 = 脉冲数 * 周长 / 2355.2 * 周期
    encl_data = (1) * encl_data * 20.4 / (2355.2 * 0.02)
    encr_data = (1) * encr_data * 20.4 / (2355.2 * 0.02)

    # 当前速度为左右编码器数据的平均值
    Current_speed = (abs(encl_data) + abs(encr_data)) / 2
    # 打印编码器数据
    # print(encl_data, encr_data)
    gc.collect()


"""
pid_control:PID 控制算法，用于调整电机速度

参数:
target_speed (int): 目标速度
current_speed (int): 当前速度
duty (int): 当前占空比
error_pre_last (int): 前前次误差
error_pre (int): 前次误差

返回:
tuple: 更新后的占空比，前前次误差，前次误差
"""


def pid_control(target_speed, current_speed, duty, error_pre_last, error_pre):
    error = target_speed - current_speed
    duty += (error - error_pre) * MOTOR_P + error * MOTOR_I + (error - 2 * error_pre + error_pre_last) * MOTOR_D
    error_pre_last = error_pre
    error_pre = error
    return duty, error_pre_last, error_pre


def directional_control(error, dir_error, dir_error_last, dir_value):
    """
    方向控制算法，用于调整电机转向

    参数:
    error (int): 当前误差
    dir_error (int): 前次方向误差
    dir_error_last (int): 前前次方向误差
    dir_value (int): 当前方向值

    返回:
    tuple: 更新后的方向值，前次方向误差，前前次方向误差
    """
    if abs(error) > ERROR_THRESHOLD:
        dir_value = (error - dir_error) * DIR_P + error * DIR_I + (error - 2 * dir_error + dir_error_last) * DIR_D
        dir_error_last = dir_error
        dir_error = error
    return dir_value, dir_error, dir_error_last


def limit_duty(duty):
    """
    限制占空比在最大和最小值之间

    参数:
    duty (int): 当前占空比

    返回:
    int: 限制后的占空比
    """
    if duty > DUTY_LIMIT_HIGH:
        duty = DUTY_LIMIT_HIGH
    elif duty < DUTY_LIMIT_LOW:
        duty = DUTY_LIMIT_LOW
    return duty


def control_motor(motor_l, motor_r, error, Statu, flag):
    """
    控制指定的电机，并根据占空比值改变电机转速和方向

    参数:
    motor_l (MOTOR_CONTROLLER): 已初始化的左电机实例
    motor_r (MOTOR_CONTROLLER): 已初始化的右电机实例
    error (int): 当前误差值
    Statu (bool): 电机状态，True 为启动，False 为停止
    flag (int): 备用标志位，未使用
    """
    global dutyL, dutyR, errorl, errorR, error_pre_lastl, error_pre_lastr, error_prel, error_prer
    global dir_error, dir_error_last, Dir_value

    # 防止按键启动前的误差积累
    if Statu:
        # 左轮PID控制
        dutyL, error_pre_lastl, error_prel = pid_control(SPEED_L, encl_data, dutyL, error_pre_lastl, error_prel)

        # 右轮PID控制
        dutyR, error_pre_lastr, error_prer = pid_control(SPEED_R, encr_data, dutyR, error_pre_lastr, error_prer)

    # 转向PID控制
    if abs(error) > ERROR_THRESHOLD:
        Dir_value, dir_error, dir_error_last = directional_control(error, dir_error, dir_error_last, Dir_value)
        dutyR -= Dir_value
        dutyL += Dir_value

    # 按键启动时设置占空比为 0
    if not Statu:
        dutyL = dutyR = 0

    # 限制占空比
    dutyL = limit_duty(dutyL)
    dutyR = limit_duty(dutyR)

    # 更新电机PWM
    motor_l.duty(dutyL)
    motor_r.duty(dutyR)

    # 强制垃圾回收
    gc.collect()

# 示例调用
# control_motor(motor_l, motor_r, error, Statu, flag)  # 控制电机
