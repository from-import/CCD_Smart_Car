from machine import *
from seekfree import MOTOR_CONTROLLER
from smartcar import encoder
import gc
import time

"""
初始化全局变量
"""
# PID
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


def control_encoder(encoder_l, encoder_r):
    global encl_data, encr_data
    # 通过 get 接口读取数据
    encl_data = encoder_l.get()
    encr_data = encoder_r.get()
    # 计算小车的实际速度
    # 速度 = 脉冲数 * 周长 / 2368 * 周期
    encl_data = (1) * encl_data * 20.4 / (2355.2 * 0.02)
    encr_data = (1) * encr_data * 20.4 / (2355.2 * 0.02)
    Current_speed = (abs(encl_data) + abs(encr_data)) / 2
    # print(encl_data,encr_data)
    gc.collect()


"""
control_motor:控制指定的电机，并根据占空比值改变电机转速和方向。

参数:
duty (int): 电机的占空比值，范围为 ±10000。正数表示正转，负数表示反转。
motor_l (MOTOR_CONTROLLER): 已初始化的左电机实例。
motor_r (MOTOR_CONTROLLER): 已初始化的右电机实例。
"""


def control_motor(motor_l, motor_r, error, Statu, flag):
    global dutyL, dutyR, errorl, errorR, error_pre_lastl, error_pre_lastr, error_prel, error_prer
    global encl_data, encr_data, Stop

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 调参
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    Motor_P = 1
    Motor_I = 5
    Motor_D = 0

    # 设置初始目标值
    speed_L = 40
    speed_R = 40

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 直线PID
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""

    if Statu:  # 防止按键启动前的误差积累
        errorl = (int)(speed_L - encl_data) * 1  # 左轮PID
        dutyL = dutyL + (errorl - error_prel) * Motor_P + errorl * Motor_I + (
                errorl - 2 * (error_prel) + error_pre_lastl) * Motor_D
        error_pre_lastl = error_prel
        error_prel = errorl

        errorR = (int)(speed_R - encr_data) * 1  # 右轮PID
        dutyR = dutyR + (errorR - error_prer) * Motor_P + errorR * Motor_I + (
                errorR - 2 * (error_prer) + error_pre_lastr) * Motor_D
        error_pre_lastr = error_prer
        error_prer = errorR

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 调参
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    global dir_error, dir_error_last, Dir_value
    Dir_P = 0
    Dir_I = 1
    Dir_D = 0

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 转向PID(等待传入offset)
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    # 处理误差小于15的情况
    if 0 < abs(error) < 15:
        Dir_value = (0.05 * error) * ((error - dir_error) * Dir_P + error * Dir_I +
                                      (error - 2 * (dir_error) + dir_error_last) * Dir_D)
        dir_error = error
        dir_error_last = dir_error

        dutyR = dutyR - Dir_value
        dutyL = dutyL + Dir_value

    if 15 < abs(error) < 64:
        Dir_value = ((error - dir_error) * Dir_P + error * Dir_I +
                     (error - 2 * (dir_error) + dir_error_last) * Dir_D)
        dir_error = error
        dir_error_last = dir_error
        dutyR = dutyR - Dir_value
        dutyL = dutyL + Dir_value

    if flag == "isCircle":
        dutyR = dutyL = 2000  # 入环检测后强制直行
    # 限幅
    if dutyL > 5000:
        dutyL = 5000
    elif dutyL < -3000:
        dutyL = -3000
    if dutyR > 5000:
        dutyR = 5000
    elif dutyR < -3000:
        dutyR = -3000

    if not Statu:
        dutyL = dutyR = 0  # 按键启动

    # 更新电机PWM
    motor_l.duty(dutyL)
    motor_r.duty(dutyR)
    # print(dutyL, dutyR)
    gc.collect()


"""
# 示例调用
control_motor(2500, 'left', motor_l, motor_r, led1)  # 控制左电机，以占空比 2500 运行
time.sleep(2)  # 运行 2 秒
control_motor(-2500, 'right', motor_l, motor_r, led1)  # 控制右电机，以占空比 -2500 运行
"""
