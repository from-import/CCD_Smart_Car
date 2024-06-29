from machine import PWM
import gc
import time
from seekfree import MOTOR_CONTROLLER
from smartcar import encoder

# 初始化全局变量
dutyL = 0
dutyR = 0
errorl = 0
errorR = 0
error_pre_lastl = 0
error_pre_lastr = 0
error_prel = 0
error_prer = 0

# 定义模糊算法的常数和参数
PFF = [-24, -12, -6, 0, 6, 12, 24]  # 输入P的语言值特征点
DFF = [-6.5, -3, 0, 3, 6.5]         # 输入D的语言值特征点
UFF = [0, 7, 14, 21, 50, 80, 120]   # 输出U的语言值特征点

# 模糊规则表
rule = [
    [5, 5, 4, 4, 4],  # Pn=-3
    [4, 4, 3, 2, 2],  # Pn=-2
    [3, 2, 1, 0, 1],  # Pn=-1
    [3, 1, 0, 1, 3],  # Pn=0
    [1, 0, 1, 2, 3],  # Pn=1
    [2, 2, 3, 4, 4],  # Pn=2
    [4, 4, 4, 5, 5]   # Pn=3
]

# 模糊算法函数
def Fuzzy(P, D):
    # 计算P的隶属度PF
    if P > PFF[0] and P < PFF[6]:
        if P <= PFF[1]:
            Pn = -2
            PF = (PFF[1] - P) / (PFF[1] - PFF[0])
        elif P <= PFF[2]:
            Pn = -1
            PF = (PFF[2] - P) / (PFF[2] - PFF[1])
        elif P <= PFF[3]:
            Pn = 0
            PF = (PFF[3] - P) / (PFF[3] - PFF[2])
        elif P <= PFF[4]:
            Pn = 1
            PF = (PFF[4] - P) / (PFF[4] - PFF[3])
        elif P <= PFF[5]:
            Pn = 2
            PF = (PFF[5] - P) / (PFF[5] - PFF[4])
        elif P <= PFF[6]:
            Pn = 3
            PF = (PFF[6] - P) / (PFF[6] - PFF[5])
    elif P <= PFF[0]:
        Pn = -2
        PF = 1
    elif P >= PFF[6]:
        Pn = 3
        PF = 0

    PF_complement = 1 - PF

    # 计算D的隶属度DF
    if D > DFF[0] and D < DFF[4]:
        if D <= DFF[1]:
            Dn = -2
            DF = (DFF[1] - D) / (DFF[1] - DFF[0])
        elif D <= DFF[2]:
            Dn = -1
            DF = (DFF[2] - D) / (DFF[2] - DFF[1])
        elif D <= DFF[3]:
            Dn = 0
            DF = (DFF[3] - D) / (DFF[3] - DFF[2])
        elif D <= DFF[4]:
            Dn = 1
            DF = (DFF[4] - D) / (DFF[4] - DFF[3])
    elif D <= DFF[0]:
        Dn = -2
        DF = 1
    elif D >= DFF[4]:
        Dn = 1
        DF = 0

    DF_complement = 1 - DF

    # 使用规则表计算Un
    Un = [
        rule[Pn - 1 + 3][Dn - 1 + 3],
        rule[Pn + 3][Dn - 1 + 3],
        rule[Pn - 1 + 3][Dn + 3],
        rule[Pn + 3][Dn + 3]
    ]

    # 计算UF的最小值和最大值
    UF = [
        min(PF, DF),
        min(PF_complement, DF),
        min(PF, DF_complement),
        min(PF_complement, DF_complement)
    ]

    # 根据Un的值和UF的最小值计算模糊输出U
    U_sum = 0
    UF_sum = 0

    for i in range(4):
        U_sum += UF[i] * UFF[Un[i]]
        UF_sum += UF[i]

    if UF_sum != 0:
        U = U_sum / UF_sum
    else:
        U = 0

    return U

# 模糊控制电机
def control_motor_fuzzy(motor_l, motor_r, P, D, Key_4):
    global dutyL, dutyR, errorl, errorR, error_pre_lastl, error_pre_lastr, error_prel, error_prer
    global encl_data, encr_data

    # 使用模糊算法计算输出偏差
    U = Fuzzy(P, D)

    # 设置初始目标值
    speed_L = 20 + U
    speed_R = 20 - U

    # 防止按键启动前的误差积累
    if Key_4:
        # 左轮PID
        errorl = (int)(speed_L - encl_data) * (1)
        dutyL = dutyL + (errorl - error_prel) * Motor_P + errorl * Motor_I + (
                    errorl - 2 * (error_prel) + error_pre_lastl) * Motor_D
        error_pre_lastl = error_prel
        error_prel = errorl
        print(errorl)

        # 右轮PID
        errorR = (int)(speed_R - encr_data) * (1)
        dutyR = dutyR + (errorR - error_prer) * Motor_P + errorR * Motor_I + (
                    errorR - 2 * (error_prer) + error_pre_lastr) * Motor_D
        error_pre_lastr = error_prer
        error_prer = errorR
        print(errorR)

    # 限幅，运行
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
    print(dutyL, dutyR)
    gc.collect()


# 模糊控制舵机
def control_servo_fuzzy(pwm_servo, P, D):
    # 使用模糊算法计算输出偏差
    offset = Fuzzy(P, D)
    # 设置舵机角度
    angle = set_servo_angle(pwm_servo, offset)
    return angle

