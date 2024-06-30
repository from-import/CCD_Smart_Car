% 定义函数和区间
a = 0.02;
b = 0.05;
c = 0.9;
f = @(x) a * abs(x).^3 + b * x.^2 + c * abs(x);

% 定义x的范围
x = linspace(0, 15, 100);

% 定义三段区间
x1 = linspace(0, 5, 100);
x2 = linspace(5, 10, 100);
x3 = linspace(10, 15, 100);

% 计算三段函数值
y1 = f(x1);
y2 = f(x2);
y3 = f(x3);

% 线性拟合三段函数
p1 = polyfit(x1, y1, 1);
p2 = polyfit(x2, y2, 1);
p3 = polyfit(x3, y3, 1);

% 生成拟合直线的值
y1_fit = polyval(p1, x1);
y2_fit = polyval(p2, x2);
y3_fit = polyval(p3, x3);

% 输出线性拟合方程式
fprintf('Linear fit for interval 0-5: y = %.4fx + %.4f\n', p1(1), p1(2));
fprintf('Linear fit for interval 5-10: y = %.4fx + %.4f\n', p2(1), p2(2));
fprintf('Linear fit for interval 10-15: y = %.4fx + %.4f\n', p3(1), p3(2));

% 绘图
figure;
hold on;
plot(x, f(x), 'k-', 'DisplayName', 'Original Function');
plot(x1, y1_fit, 'r--', 'DisplayName', 'Linear Fit 0-5');
plot(x2, y2_fit, 'g--', 'DisplayName', 'Linear Fit 5-10');
plot(x3, y3_fit, 'b--', 'DisplayName', 'Linear Fit 10-15');
legend('show');
xlabel('x');
ylabel('f(x)');
title('Piecewise Linear Approximation of Cubic Function');
hold off;

