from machine import *
from seekfree import MOTOR_CONTROLLER
from smartcar import encoder
import gc
import time

"""
初始化全局变量
"""
# 电机PID
# PID
dutyL = 0
dutyR = 0
errorl = 0
errorR = 0
error_pre_lastl = 0
error_pre_lastr = 0
error_prel = 0
error_prer = 0

# 位置环PID
dir_error = 0
dir_error_last = 0
Dir_value = 0
#
Stop = 0


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


Distance = 0


def Record_Distance(Record_dis):
    global Distance, encl_data, encr_data
    if Record_dis == 1:
        Distance = Distance + (abs(encl_data) + abs(encr_data)) / 2 * 10 * 0.005
    else:
        Distance = 0

    return Distance


def control_motor(motor_l, motor_r, error, Statu, flag):
    global dutyL, dutyR, errorl, errorR, error_pre_lastl, error_pre_lastr, error_prel, error_prer
    global encl_data, encr_data
    global Stop
    """
    控制指定的电机，并根据占空比值改变电机转速和方向。

    参数:
        error,ccd中线误差
        Statu总启动标志，0为停止
        flag特殊场景运行
    """

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 调参
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    Motor_P = 15
    Motor_I = 6.5
    Motor_D = 0

    # 设置初始目标值(先匀速运行)

    speed_L = 45
    speed_R = 45
    """
    else:
        speed_L = 50
        speed_R = 50"""
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 直线PID
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    #防止按键启动前的误差积累
    if Statu:
        # 左轮PID
        errorl = (int)(speed_L - encl_data) * (1)
        dutyL = dutyL + (errorl - error_prel) * Motor_P + errorl * Motor_I + (
                    errorl - 2 * (error_prel) + error_pre_lastl) * Motor_D
        error_pre_lastl = error_prel
        error_prel = errorl
        # print(errorl)

        # 右轮PID
        errorR = (int)(speed_R - encr_data) * (1)
        dutyR = dutyR + (errorR - error_prer) * Motor_P + errorR * Motor_I + (
                    errorR - 2 * (error_prer) + error_pre_lastr) * Motor_D
        error_pre_lastr = error_prer
        error_prer = errorR
        # print(errorR)
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 调参
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    global dir_error, dir_error_last, Dir_value
    Dir_P = 5
    Dir_I = 1.2
    Dir_D = 15
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 转向PID(等待传入offset)
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    if abs(error) > 20:
        Dir_value = (error - dir_error) * Dir_P + error * Dir_I + (error - 2 * (dir_error) + dir_error_last) * Dir_D
        dir_error = error
        dir_error_last = dir_error

        dutyR = dutyR - Dir_value
        dutyL = dutyL + Dir_value

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 其他功能
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    #
    #
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 开环控制部分（Statu 总启动标志，0为停止）(flag不为0代表特殊情况)
          特殊情况表赋值看Elements_CCD.py
    Tips:   Statu 总启动标志，0为停止
        flag = 0  正常寻线活动
        flag = 4  圆环单边补线
        flag = 40 入环
        flag = 10 斑马线
        flag = 11 出线
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    if flag == 10:
        Stop = 1

    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 按键启动,出线停车
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    if Stop:
        dutyL = dutyR = 0
    if flag == 11:
        # 出线停机，注意PID误差此时会累加，调试时使用
        dutyL = dutyR = 0
    if not Statu:
        dutyL = dutyR = 0
    """ ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Tips: 限幅，运行
    +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"""
    if dutyL > 5000:
        dutyL = 5000
    elif dutyL < -3000:
        dutyL = -3000
    if dutyR > 5000:
        dutyR = 5000
    elif dutyR < -3000:
        dutyR = -3000

    # 更新电机PWM
    motor_l.duty(dutyL)
    motor_r.duty(dutyR)
    # print(dutyL, dutyR)
    gc.collect()
















