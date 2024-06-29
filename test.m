% 定义三次函数系数
a = 0.02; % 可以根据需要调整a的值以达到增长速度要求
b = 0.05;
c = 0.9;
d = 0;

% 定义x轴的数据
x = linspace(0, 20, 100); % 从0到20，共100个点

% 计算y轴的数据
y = a*x.^3 + b*x.^2 + c*x + d;

% 计算在x=6时的y值
y_6 = a*6^3 + b*6^2 + c*6 + d;

% 计算在x=20时的y值
y_15 = a*15^3 + b*15^2 + c*15 + d;

% 计算比值
ratio = y_15 / y_6;

% 输出结果
fprintf('在x=6时的y值: %.4f\n', y_6);
fprintf('在x=15时的y值: %.4f\n', y_15);
fprintf('函数在x=15时y值与在x=6时y值的比值: %.4f\n', ratio);

% 绘制图形
figure;
plot(x, y, 'LineWidth', 2);
title('Cubic Function y = ax^3 + bx^2 + cx + d');
xlabel('x');
ylabel('y');
grid on;

% 增加垂直线以显示x = 6和x = 20的位置
hold on;
line([6 6], [0 max(y)], 'Color', 'r', 'LineStyle', '--', 'LineWidth', 1);
line([20 20], [0 max(y)], 'Color', 'r', 'LineStyle', '--', 'LineWidth', 1);
hold off;

% 显示导数
dy = 3*a*x.^2 + 2*b*x + c;
figure;
plot(x, dy, 'LineWidth', 2);
title('Derivative of Cubic Function y = ax^3 + bx^2 + cx + d');
xlabel('x');
ylabel('dy/dx');
grid on;

