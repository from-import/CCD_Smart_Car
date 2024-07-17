程序具体运行流程及CCD处理和元素识别的具体算法
初始化及主循环

    初始化阶段
        初始化端口方向和设备（如 OLED、PIT、SCI、AD、CCD、PWM、PAC、LED等）。
        根据用户输入（通过拨码开关 PTH）设置停车时间、速度和模糊控制参数，以及障碍物处理时间。

    主循环
        在主循环中，周期性地更新显示数据，并根据输入状态执行相应的操作。
        主要任务包括处理来自 CCD 的图像数据、执行路径规划和控制车速和方向。

CCD 处理流程

    图像采集
        在中断服务程序中，通过 ImageCapture() 函数采集 128 个像素点的数据，存储在 Pixel 数组中。

    数据归一化
        CCD_Normalization() 函数对采集到的数据进行归一化处理，消除光线强度变化的影响，使得数据更加适合后续的边缘检测。

    边缘检测
        search() 函数中，计算每个像素与前面 3 个像素的差值，存储在 CCD_Diff 数组中，用于检测图像中的边缘。
        找到图像中的上升沿和下降沿（即边缘），并存储在 RisingEdge 和 FallingEdge 数组中。

    预判道路类型
        Prejudge() 函数通过检测是否有上升沿和下降沿来预判道路类型。如果没有边缘，全白，认为是十字路口。

元素识别的具体算法

    普通道路处理
        Normal() 函数负责在普通道路上处理图像数据，寻找并更新赛道的左边缘和右边缘。
        更新参考宽度 Reference_Width，用于后续帧的边缘检测。

    十字路口处理
        CrossRoad() 函数处理检测到十字路口时的逻辑，调整车辆的方向以通过十字路口，并在通过后恢复正常的道路检测。

    障碍物处理
        Barraicade() 函数处理检测到障碍物时的逻辑，根据障碍物的位置调整车辆的路径。
        Is_Barraicade() 函数进一步确认障碍物，并判断障碍物的具体位置，调整车辆的路径。

    坡道处理
        Hill() 函数处理检测到坡道时的逻辑，根据坡道的特点调整车辆的路径和速度。
        Is_Hill() 函数进一步确认坡道，并调整车辆的路径和速度。

关键函数解析

1.起跑线检测

    int start_check(unsigned char *A, int interval, int yuzhi)
    {
        int i, tiaobian = 0;
        int last_tiaobian = 0;
        int this_tiaobian = 0;
    
        for (i = 45; i < 100; i++)
        {
            if (abs(A[i] - A[i + interval]) > yuzhi)
            {
                this_tiaobian = i;
                if (this_tiaobian != last_tiaobian + 1)
                {
                    tiaobian++;
                }
                last_tiaobian = this_tiaobian;
            }
        }
        return tiaobian;
    }

2.边缘检测

    void search()
    {
        uint8_t i = 0, L, R;
        int left_c, right_c;
        static float middle_last;
        Max_Peak = 0;
        RisingEdgeCnt = 0; // 上升沿计数
        FallingEdgeCnt = 0; // 下降沿计数
        for (i = 0; i < 5; i++) // 重置清零
        {
            RisingEdge[i] = 0;
            FallingEdge[i] = 0;
        }
        for (i = 3; i < 128; i++) // 求出最大的差分值
        {
            CCD_Diff[i] = Pixel[i] - Pixel[i - 3];
            if (fabs(CCD_Diff[i]) > Max_Peak)
                Max_Peak = fabs(CCD_Diff[i]);
        }
        for (i = 4; i < 127; i++)
        {
            if ((CCD_Diff[i] >= CCD_Diff[i - 1]) && (CCD_Diff[i] > CCD_Diff[i + 1]) && (CCD_Diff[i] > got_yuzhi)) // 寻找正的峰值，左边线
            {
                if (RisingEdgeCnt < 5) // 一行图像最多有5个上跳沿
                {
                    RisingEdge[RisingEdgeCnt] = i;
                    RisingEdgeCnt++;
                }
            }
            if ((CCD_Diff[i] < CCD_Diff[i - 1]) && (CCD_Diff[i] <= CCD_Diff[i + 1]) && (CCD_Diff[i] < -got_yuzhi)) // 寻找负的峰值，右边线
            {
                if (FallingEdgeCnt < 5) // 一行图像最多有5个下跳沿
                {
                    FallingEdge[FallingEdgeCnt] = i;
                    FallingEdgeCnt++;
                }
            }
        }
    
        Prejudge(); // 预判函数
        switch (RoadType)
        {
        case 0:
            Normal();
            if (Barraicadeflag == 1)
                Is_Barraicade();
            break;
        case 1:
            CrossRoad();
            break;
        case 2:
            Barraicade();
            break;
        case 3:
            Hill();
            break;
        default:
            Normal();
            break;
        }
        Leftlast = Left;   // 更新边界线
        Rightlast = Right; // 更新边界线
        left_c = Left - 1; // 减去2修正差分误差
        right_c = Right;
        Is_Hill();
        if (Rightlastfind || Leftlastfind)
        {
            Middle_Err = 64 - (right_c + left_c) / 2.0 + 1; // 除以整数2会损失精度
            if (fabs(Middle_Err - middle_last) > 2 && (curve_to_cross == 0))
            {
                if (RoadType != 2)
                {
                    if (fabs(Middle_Err - middle_last) > 3)
                    {
                        if (Middle_Err > middle_last)
                            Middle_Err = middle_last + 1;
                        else
                            Middle_Err = middle_last - 1;
                    }
                    else
                    {
                        if (Middle_Err > middle_last)
                            Middle_Err = middle_last + 2;
                        else
                            Middle_Err = middle_last - 2;
                    }
                }
            }
            middle_last = Middle_Err;
        }
        Push_And_Pull(Previous_Width, 15, (float)(Right - Left));
        Push_And_Pull(Previous_Error, 15, Middle_Err);
        if (Rightlastfind && Leftlastfind)
        {
            if (Both_Line_find_cnt < 20)
                Both_Line_find_cnt++;
        }
        else
            Both_Line_find_cnt = 0;
    }


3.普通道路处理

        void Normal(void)
    {
        uint8_t tempwidth;
        if (Leftlastfind == 0 && Rightlastfind == 0) // 上次没有边线
        {
            Find_Bothine();
            if (Leftlastfind == 0 && Rightlastfind == 0)
            {
                if (FindBoundary(left))
                {
                    Left = RisingEdge[RisingEdgeIndex];
                    Leftlastfind = 1;
                }
                else
                    Leftlastfind = 0;
                if (FindBoundary(right))
                {
                    Right = FallingEdge[FallingEdgeIndex];
                    Rightlastfind = 1;
                }
                else
                    Rightlastfind = 0;
                if (Leftlastfind && Rightlastfind)
                {
                    if (Right < Left)
                    {
                        Leftlastfind = 0;
                        Rightlastfind = 0;
                    }
                }
            }
        }
        else
        {
            if (Leftlastfind) // 上次找到了左线
            {
                if (FindNearest(left, Leftlast)) // 这次能找到左线
                {
                    Left = RisingEdge[RisingEdgeIndex];
                    Leftlastfind = 1;
                    if (Rightlastfind == 0) // 上次找到左线，这次找到左线，上次没找到右线
                    {
                        if (FallingEdgeCnt) // 上次找到左线，这次找到左线，上次没找到右线，这次找到右线
                        {
                            for (FallingEdgeIndex = 0; FallingEdgeIndex < FallingEdgeCnt; FallingEdgeIndex++)
                            {
                                rightfind = 0; //
                                if (FallingEdge[FallingEdgeIndex] > Left) // 找到潜在的边线了
                                {
                                    tempwidth = FallingEdge[FallingEdgeIndex] - Left;
                                    if (fabs(tempwidth - Reference_Width) >= 2) // 右线出现的太左了，慢慢靠近
                                    {
                                        if (tempwidth > Reference_Width)
                                            Reference_Width = Reference_Width + 1; // 潜在的赛道边线比参考宽度宽太多
                                        else
                                        {
                                            Reference_Width = Reference_Width - 1; // 潜在的赛道边线比参考宽度窄太多
                                        }
                                        Right = Left + Reference_Width;
                                        Rightlastfind = 0;
                                    }
                                    else
                                    {
                                        Right = FallingEdge[FallingEdgeIndex];
                                        Rightlastfind = 1;
                                    }
                                    rightfind = 1; // 找到边线了，但是还不能立马赋值
                                    break;
                                }
                            }
                            if (Rightlastfind == 0 && rightfind == 0) // 虽然说有上升沿，但是该上升沿无效
                            {
                                Right = Left + Reference_Width;
                            }
                        }
                        else // 没有下跳沿
                        {
                            Right = Left + Reference_Width;
                        }
                    }
                }
                else // 上次能找到左线，这次没能找到左线
                {
                    Leftlastfind = 0; // 丢线
                    if (FindBoundary(left))
                    {
                        if (RisingEdge[RisingEdgeIndex] < Leftlast) // 这次没能够找到与上次相邻的边界，但是有边界却比现有的边界宽
                        {
                            if (Rightlastfind == 0 && ((RoadType != 2) && (RoadType != 3))) // 上次没有找到右边界，这次左边界又往外靠，那么就是遇到十字了
                            {
                                RoadType = 1;
                            }
                        }
                        else if (RisingEdge[RisingEdgeIndex] < Leftlast + 8) // 这次的边界比上次更靠近中央，但是他们的差值不大于8
                        {
                            Left = RisingEdge[RisingEdgeIndex];
                            Leftlastfind = 1; // 未丢线
                        }
                    }
                    else // 不能找到左边界
                    {
                        if (Rightlastfind == 0 && (RoadType != 4))
                        {
                            RoadType = 1;
                        }
                    }
                }
            }
            if (Rightlastfind) // 上次找到了右线
            {
                if (FindNearest(right, Rightlast)) // 这次能找到右线
                {
                    Right = FallingEdge[FallingEdgeIndex];
                    Rightlastfind = 1;
                    if (Leftlastfind == 0) // 上次找到了右线,这次能找到右线,上次找不到左线
                    {
                        if (RisingEdgeCnt > 0) // 上次找到了右线,这次能找到右线,上次找不到左线,这次找到了左线
                        {
                            for (RisingEdgeIndex = RisingEdgeCnt - 1; RisingEdgeIndex >= 0; RisingEdgeIndex--)
                            {
                                leftfind = 0;
                                if (RisingEdge[RisingEdgeIndex] < Right) // 找到潜在的边线了
                                {
                                    tempwidth = Right - RisingEdge[RisingEdgeIndex];
                                    if (fabs(tempwidth - Reference_Width) >= 2) // 右线出现的太左了，慢慢靠近
                                    {
                                        if (tempwidth > Reference_Width)
                                            Reference_Width = Reference_Width + 1; // 潜在的赛道边线比参考宽度宽太多
                                        else
                                        {
                                            Reference_Width = Reference_Width - 1; // 潜在的赛道边线比参考宽度窄太多
                                        }
                                        Left = Right - Reference_Width;
                                        Leftlastfind = 0;
                                    }
                                    else
                                    {
                                        Left = RisingEdge[RisingEdgeIndex];
                                        Leftlastfind = 1;
                                    }
                                    leftfind = 1;
                                    break;
                                }
                            }
                            if (Leftlastfind == 0 && leftfind == 0) // 虽然说有上升沿，但是该上升沿无效
                            {
                                Left = Right - Reference_Width;
                            }
                        }
                        else // 没有上升沿
                        {
                            Left = Right - Reference_Width;
                        }
                    }
                }
                else // 上次能找到，这次没能找到与上次相邻近的线
                {
                    Rightlastfind = 0; // 丢线
                    if (FindBoundary(right)) // 能够找到右边界
                    {
                        if (FallingEdge[FallingEdgeIndex] > Rightlast) // 这次没能够找到与上次相邻的边界，但是有边界却比现有的边界宽
                        {
                            if (Leftlastfind == 0 && ((RoadType != 2) && (RoadType != 3))) // 上次没有找到左边界，这次右边界又往外靠，那么就是遇到十字了
                            {
                                RoadType = 1;
                            }
                        }
                        else if (FallingEdge[FallingEdgeIndex] > Rightlast - 8) // 这次的边界比上次更靠近中央，但是他们的差值不大于8
                        {
                            Right = FallingEdge[FallingEdgeIndex];
                            Rightlastfind = 1; // 其实是未丢线
                        }
                    }
                    else // 不能找到右边界
                    {
                        if (Leftlastfind == 0 && (RoadType != 4)) // 上次没有找到左边界，这次右边界又往外靠，那么就是遇到十字了
                        {
                            RoadType = 1;
                        }
                    }
                }
            }
            // 都能找到边线，更新参考宽度
            if (Rightlastfind && Leftlastfind)
            {
                Reference_Width = Right - Left;
                if (Reference_Width < 35)
                    Reference_Width = 35;
            }
        }
    }

4.十字路口处理
    
    void CrossRoad(void)
    {
        static uint8_t Normal_Cnt;
        static uint8_t Cross_Road_Cnt = 0;
    
        // 缓慢归零，车子回正
        if (curve_to_cross == 0)
        {
            Rightlastfind = 0;
            Leftlastfind = 0;
        }
        else
        {
            if (Rightlastfind)
            {
                if (FindNearest(right, Rightlast)) // 这次能找到左线
                {
                    Right = FallingEdge[FallingEdgeIndex];
                    Rightlastfind = 1;
                    Left = Right - Reference_Width;
                }
                else
                {
                    Rightlastfind = 0;
                    // curve_to_cross=0;
                }
            }
            else if (Leftlastfind)
            {
                if (FindNearest(left, Leftlast)) // 这次能找到左线
                {
                    Left = RisingEdge[RisingEdgeIndex];
                    Leftlastfind = 1;
                    Right = Reference_Width + Left;
                }
                else
                {
                    Leftlastfind = 0;
                    // curve_to_cross=0;
                }
            }
        }
    
        if (fabs(Middle_Err) > 1)
        {
            if (curve_to_cross == 0)
            {
                if (Middle_Err > 0)
                    Middle_Err = Middle_Err - 1;
                if (Middle_Err < 0)
                    Middle_Err = Middle_Err + 1;
            }
        }
        else
            Middle_Err = Middle_Err;
        if (curve_to_cross == 0 || (curve_to_cross == 1))
            Find_Bothine();
        if (Rightlastfind && Leftlastfind) // 能够找到两边边界
        {
            if (Right - Left < 65 && Cross_Road_Cnt > 4) // 宽度有效
            {
    
                {
                    Normal_Cnt++;
                    if (Normal_Cnt >= 3)
                    {
                        RoadType = 0;
                        curve_to_cross = 0;
                        // 跳回正常道路
                    }
                }
            }
            else
            {
                Rightlastfind = 0;
                Leftlastfind = 0;
                Normal_Cnt = 0;
            }
        }
        else
            Normal_Cnt = 0;
        if (RoadType != 1)
        {
            Cross_Road_Cnt = 0;
        }
        else
        {
            if (Cross_Road_Cnt < 10)
                Cross_Road_Cnt++;
            if (Cross_Road_Cnt > 3 && Cross_Road_Cnt < 8 && curve_to_cross == 0)
            {
                Leftlastfind = 0;
                Rightlastfind = 0;
            }
        }
    }


5.坡道处理
    
    void Hill()
    {
        uint8_t i = 0, j = 0, threshold_t;
        static uint8_t lost_cnt;
        static uint8_t Confirm_Cnt = 0;
        if (RoadTypeConfirm == 0) // 还没确认
        {
            Normal(); // 调用normal函数来搜线
            if (Confirm_Cnt < 5) // 用5个周期来确认
            {
                if (Leftlastfind == 0 || Rightlastfind == 0 || fabs(Middle_Err) > 5) // 有一条边没找到说明这个其实是弯道
                {
                    RoadType = 0;
                    Confirm_Cnt = 0;
                }
                else
                    Confirm_Cnt++;
            }
            else
                RoadTypeConfirm = 1; // 赛道类型确认了，确实是坡道
            lost_cnt = 0;
        }
        else // 已经判断是坡道了
        {
            Leftlastfind = 0;
            Rightlastfind = 0;
            threshold_t = Threshold;
            while ((Leftlastfind == 0) && (threshold_t * 1.5 > Threshold))
            {
                for (i = Leftlast - 6; i <= Leftlast + 6; i++)
                {
                    if ((CCD_Diff[i] >= CCD_Diff[i - 1]) && (CCD_Diff[i] > CCD_Diff[i + 1]) && (CCD_Diff[i] > threshold_t)) // 寻找负的峰值
                    {
                        Left = i;
                        Leftlastfind = 1;
                    }
                }
                threshold_t = threshold_t - 2;
            }
            threshold_t = Threshold;
            while ((Rightlastfind == 0) && (threshold_t * 1.5 > Threshold))
            {
                for (j = Rightlast + 6; j >= Rightlast - 6; j--)
                {
                    if ((CCD_Diff[j] < CCD_Diff[j - 1]) && (CCD_Diff[j] <= CCD_Diff[j + 1]) && (CCD_Diff[j] < -threshold_t)) // 寻找正的峰值
                    {
                        Right = j;
                        Rightlastfind = 1;
                    }
                }
                threshold_t = threshold_t - 2;
            }
            if ((Leftlastfind == 1) && (Rightlastfind == 0))
            {
                for (j = Left + 10; (j <= Left + 50) && (j < 120); j++)
                {
                    if ((CCD_Diff[j] < CCD_Diff[j - 1]) && (CCD_Diff[j] <= CCD_Diff[j + 1]) && (CCD_Diff[j] < -Threshold)) // 寻找正的峰值
                    {
                        Right = j;
                        Rightlastfind = 1;
                        break;
                    }
                }
            }
            if ((Leftlastfind == 0) || (Rightlastfind == 1))
            {
                for (i = Right - 10; (i >= Right - 50) && (i > 10); i--)
                {
                    if ((CCD_Diff[i] >= CCD_Diff[i - 1]) && (CCD_Diff[i] > CCD_Diff[i + 1]) && (CCD_Diff[i] > threshold_t)) // 寻找负的峰值
                    {
                        Left = i;
                        Leftlastfind = 1;
                        break;
                    }
                }
            }
    
            if (Leftlastfind == 0 || Rightlastfind == 0)
            {
                lost_cnt++;
                if (Right - Left > 50 || (lost_cnt >= 3 && Right - Left > 30) || (lost_cnt >= 5 && Right - Left < 20))
                {
                    RoadType = 0;
                    Confirm_Cnt = 0;
                    RoadTypeConfirm = 0;
                }
            }
            else
                lost_cnt = 0;
        }
    }
