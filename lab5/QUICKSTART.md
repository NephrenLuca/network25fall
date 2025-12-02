# 快速开始指南

## 环境检查

```bash
# 检查Mininet是否安装
which mn

# 检查iperf是否安装
which iperf

# 如果未安装，运行：
sudo apt-get update
sudo apt-get install -y mininet iperf
```

## 快速测试

### 任务1：定制化拓扑

```bash
# 方法1：使用Mininet命令行（推荐用于验证）
sudo mn --custom ./customized_topo.py --topo mytopo --test pingall --link tc

# 方法2：使用Python脚本（交互式）
sudo python3 customized_topo.py

# 方法3：使用自动测试脚本（自动测试带宽）
sudo python3 test_task1.py
```

### 任务2：TCP流测试

```bash
# 运行默认测试（10%丢包率）
sudo python3 host_iperf.py

# 运行不同丢包率对比测试（0%, 1%, 5%, 10%, 20%）
sudo python3 test_task2.py
```

### 运行所有测试

```bash
sudo ./run_all_tests.sh
```

## 结果文件位置

- `test_results/task1_*.txt` - 任务1的带宽测试结果
- `iperf_results/flow*.txt` - 任务2的iperf详细结果
- `test_results/flow*_loss*_result.txt` - 不同丢包率的对比结果

## 常见问题

### 1. 权限错误
**问题**: `Permission denied`  
**解决**: 所有脚本需要使用 `sudo` 运行

### 2. 端口占用
**问题**: `Address already in use`  
**解决**: 修改脚本中的iperf端口号，或等待几秒后重试

### 3. Mininet未安装
**问题**: `No module named 'mininet'`  
**解决**: `sudo apt-get install mininet`

### 4. 网络清理
如果测试后网络异常，可以运行：
```bash
sudo mn -c  # 清理Mininet
sudo pkill -9 iperf  # 清理iperf进程
```

## 任务2说明

**注意**: 任务2的拓扑图中只有H1, H3, H4三个主机，但要求中提到"h2发向h4"。
代码中实现了h1->h4作为Flow 2，因为拓扑中没有h2。这可能是：
- 拓扑图不完整（应该有h2）
- 或者h2是h1的笔误

如果实际需要h2，可以在拓扑中添加h2主机。

