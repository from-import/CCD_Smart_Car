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

