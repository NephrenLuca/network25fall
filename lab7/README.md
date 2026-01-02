# Lab 7：网络层控制平面流表下发 - 实现与说明

## 实验目标

实现三种路由算法在Fat Tree拓扑中的流表下发：

1. **Left Path Routing (LPR)**：选择最左边的可用路径
2. **Random Selection Routing (RSR)**：随机选择一条可用路径
3. **Least Loaded Routing (LLR)**：选择负载最小的路径

## 文件说明

- `LPR.py`：Left Path Routing 控制器实现
- `RSR.py`：Random Selection Routing 控制器实现
- `LLR.py`：Least Loaded Routing 控制器实现
- `FatTree_routing.py`：原始框架代码
- `parallel_traffic_generator.py`：并行流量生成器（用于LPR和RSR测试）
- `sequential_traffic_generator.py`：顺序流量生成器（用于LLR测试）
- `simple_switch.py`：基础学习交换机实现
- `test_paths.py`：路径计算测试脚本

## Fat Tree 拓扑结构

```
核心层 (Core): s17, s18, s19, s20
聚合层 (Aggregation): s9-s16
边缘层 (Edge): s1-s8
主机: h1-h16 (每个边缘交换机连接2个主机)
```

### 连接规则

- **边缘交换机**: s1-s8，每个连接2个主机
- **聚合交换机**:
  - 奇数聚合交换机 (s9,11,13,15): 连接到edge(i-8)和edge(i-7)，以及核心s17,s18
  - 偶数聚合交换机 (s10,12,14,16): 连接到edge(i-9)和edge(i-8)，以及核心s19,s20

## 路由算法实现

### 1. Left Path Routing (LPR)

**原理**: 在所有可用路径中选择ID最小的路径（最"左边"的路径）

**路径选择逻辑**:
```python
# 获取所有路径后，选择最小的
lpr_path = min(paths, key=lambda x: tuple(x))
```

**测试**: 使用 `parallel_traffic_generator.py`

### 2. Random Selection Routing (RSR)

**原理**: 在所有可用路径中随机选择一条

**路径选择逻辑**:
```python
# 随机选择一条路径
rsr_path = random.choice(paths)
```

**测试**: 使用 `parallel_traffic_generator.py`

### 3. Least Loaded Routing (LLR)

**原理**: 计算每条路径的最大链路负载，选择负载最小的那条路径。如果有多条等价路径，按LPR原则选择。

**负载计算**:
- 维护每条链路的流计数
- 路径负载 = max(路径上所有链路的负载)
- 选择最小路径负载的路径

**测试**: 使用 `sequential_traffic_generator.py`（顺序启动流，便于观察负载变化）

## 运行方法

### 1. 启动 Ryu 控制器

```bash
# LPR
ryu-manager LPR.py --observe-links --verbose

# RSR
ryu-manager RSR.py --observe-links --verbose

# LLR
ryu-manager LLR.py --observe-links --verbose
```

### 2. 启动 Mininet 拓扑

```bash
# LPR 和 RSR 测试
sudo python parallel_traffic_generator.py

# LLR 测试
sudo python sequential_traffic_generator.py
```

## 输出格式

### LPR/RSR 输出示例
```
Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4]
Path for 10.0.0.1 -> 10.0.0.8: [1, 9, 17, 11, 4]
```

### LLR 输出示例
```
LLR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4] (max load: 2)
```

## 关键实现细节

### 路径计算

1. **识别聚合交换机**: 根据Fat Tree连接规则找到连接到源/目的边缘交换机的聚合交换机
2. **确定核心交换机**: 根据聚合交换机类型确定可用的核心交换机
3. **生成路径**: 组合边缘->聚合->核心->聚合->边缘的路径

### 流表安装

1. **匹配规则**:
   - ARP包: `eth_type, in_port, arp_spa, arp_tpa`
   - IP包: `eth_type, in_port, ipv4_src, ipv4_dst`

2. **动作**: `OFPActionOutput(out_port)`

3. **优先级**: 1 (高于默认的table-miss规则)

### 负载跟踪 (LLR专用)

- 使用字典 `link_loads` 跟踪每条链路的流数量
- 路径选择时计算 `max_load = max(链路负载)`
- 选择 `min(max_load)` 的路径

## 注意事项

1. **拓扑发现**: 使用 `--observe-links` 参数通过LLDP发现网络拓扑
2. **流表老化**: 在实际部署中需要处理流表超时，但本实验简化了这个过程
3. **负载估计**: LLR使用流计数作为负载估计，实际应使用带宽统计
4. **路径对称**: 代码假设路径是对称的，实际网络中可能需要分别处理双向流量

## 测试验证

运行 `python test_paths.py` 可以验证路径计算的正确性，确保：
- 正确识别所有可用路径
- LPR选择最左边的路径
- 路径格式正确
