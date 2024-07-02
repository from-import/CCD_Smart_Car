# 激活函数和它的导数
def sigmoid(x):
    return 1 / (1 + exp(-x))

def sigmoid_derivative(x):
    return x * (1 - x)

# 指数函数实现
def exp(x):
    n = 10  # 控制精度
    result = 1.0
    term = 1.0
    for i in range(1, n + 1):
        term *= x / i
        result += term
    return result

# 生成随机数（简单线性同余生成器）
seed = 42
def random():
    global seed
    a = 1103515245
    c = 12345
    m = 2**31
    seed = (a * seed + c) % m
    return seed / m

# 初始化权重
def initialize_weights(input_size, hidden_size, output_size):
    W1 = [[random() for _ in range(input_size)] for _ in range(hidden_size)]
    W2 = [random() for _ in range(hidden_size)]
    return W1, W2

# 前向传播
def forward_propagation(X, W1, W2):
    hidden_layer_input = [sum(x*w for x, w in zip(X, W1[i])) for i in range(len(W1))]
    hidden_layer_output = [sigmoid(x) for x in hidden_layer_input]
    output_layer_input = sum(h*w for h, w in zip(hidden_layer_output, W2))
    output = sigmoid(output_layer_input)
    return hidden_layer_output, output

# 反向传播
def backward_propagation(X, y, hidden_layer_output, output, W1, W2, learning_rate=0.1):
    output_error = y - output
    output_delta = output_error * sigmoid_derivative(output)

    hidden_errors = [output_delta * w for w in W2]
    hidden_deltas = [hidden_errors[i] * sigmoid_derivative(hidden_layer_output[i]) for i in range(len(hidden_layer_output))]

    for i in range(len(W2)):
        W2[i] += learning_rate * output_delta * hidden_layer_output[i]

    for i in range(len(W1)):
        for j in range(len(W1[i])):
            W1[i][j] += learning_rate * hidden_deltas[i] * X[j]

# 训练神经网络
def train(X, y, W1, W2, epochs=1000, learning_rate=0.1):
    for _ in range(epochs):
        for i in range(len(X)):
            hidden_layer_output, output = forward_propagation(X[i], W1, W2)
            backward_propagation(X[i], y[i], hidden_layer_output, output, W1, W2, learning_rate)
    return W1, W2

# 预测函数
def predict(X, W1, W2):
    _, output = forward_propagation(X, W1, W2)
    return output

# 示例数据
input_size = 128
hidden_size = 10
output_size = 1

# 初始化权重
W1, W2 = initialize_weights(input_size, hidden_size, output_size)

# 示例训练数据
X = [[0]*128]  # 示例输入
y = [0]  # 示例标签

# 训练神经网络
W1, W2 = train(X, y, W1, W2, epochs=1000, learning_rate=0.1)

# 示例预测
test_input = [0]*128
probability = predict(test_input, W1, W2)
print("圆环的概率:", probability)