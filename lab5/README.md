# 网络实验5 - Mininet拓扑与TCP流测试

本实验包含两个主要任务：
1. 定制化拓扑测试
2. TCP流性能测试（不同丢包率）

## 环境要求

- Ubuntu WSL
- Mininet
- Python 3
- iperf

### 安装依赖

```bash
sudo apt-get update
sudo apt-get install -y mininet iperf python3
```

## 文件说明

- `customized_topo.py` - 任务1的定制化拓扑定义
- `host_iperf.py` - 任务2的TCP流测试脚本
- `test_task1.py` - 任务1的自动测试脚本
- `test_task2.py` - 任务2的不同丢包率对比测试脚本
- `run_all_tests.sh` - 运行所有测试的自动化脚本

## 使用方法

### 任务1：定制化拓扑测试

#### 方法1：使用Mininet命令行
```bash
sudo mn --custom ./customized_topo.py --topo mytopo --test pingall --link tc
```

#### 方法2：使用Python脚本
```bash
sudo python3 customized_topo.py
```

#### 方法3：使用自动测试脚本
```bash
sudo python3 test_task1.py
```

在Mininet CLI中，可以使用以下命令测试：
```bash
# 测试连通性
pingall

# 测试带宽（H1 -> H2）
h1 iperf -c h2 -t 10

# 测试带宽（H2 -> H4）
h2 iperf -c h4 -t 10

# 测试带宽（H3 -> H4）
h3 iperf -c h4 -t 10
```

### 任务2：TCP流测试

#### 运行默认测试（10%丢包率）
```bash
sudo python3 host_iperf.py
```

#### 运行不同丢包率对比测试
```bash
sudo python3 test_task2.py
```

这将测试丢包率为 0%, 1%, 5%, 10%, 20% 的情况。

### 运行所有测试

```bash
chmod +x run_all_tests.sh
sudo ./run_all_tests.sh
```

## 拓扑说明

### 任务1拓扑
```
H1 (10M bps, 2ms) ──┐
                     │
H2 (20M bps, 10ms) ──┼── S1 ── S2 ──┬── H3 (10M bps, 2ms)
                                    └── H4 (Iperf Server)
```

### 任务2拓扑
```
H1 (20M bps, 2ms) ── S1 ──[Loss 10%]── S2 ──┬── H3
                                             └── H4
```

## 测试结果

测试结果将保存在以下目录：
- `test_results/` - 任务1和任务2的测试结果
- `iperf_results/` - 任务2的iperf详细结果

## 注意事项

1. 所有脚本需要使用 `sudo` 权限运行（Mininet需要root权限）
2. 如果遇到端口占用问题，可以修改脚本中的iperf端口号
3. 测试完成后，脚本会自动清理iperf进程
4. 在WSL环境中，确保网络配置正确

## 预期结果

### 任务1带宽参考范围
- H1 – H2: 10Mbps with ~12ms latency
- H2 – H4: <<16Mbps with ~22ms latency
- H3 – H4: 10Mbps with ~12ms latency

### 任务2观察要点
- TCP Flow 1 (h1->h3): 0-20秒的带宽变化
- TCP Flow 2 (h1->h4): 10-30秒的带宽变化
- 不同丢包率对TCP性能的影响（拥塞控制、重传等）


