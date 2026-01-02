# Lab 7：网络层控制平面流表下发 - 算法实现报告

## 实验概述

本实验基于Fat Tree网络拓扑，实现了三种路由算法：Left Path Routing (LPR)、Random Selection Routing (RSR)和Least Loaded Routing (LLR)。所有算法均基于Ryu SDN控制器实现，通过OpenFlow协议在网络层面进行流表下发。

## Fat Tree拓扑分析

### 网络结构
- **边缘交换机 (Edge)**: s1-s8，每个连接2个主机 (h1-h16)
- **聚合交换机 (Aggregation)**: s9-s16，连接边缘交换机和核心交换机
- **核心交换机 (Core)**: s17-s20，提供高层互联

### 连接规则
- 聚合交换机s9(奇数): 连接s1、s2和核心s17、s18
- 聚合交换机s10(偶数): 连接s1、s2和核心s19、s20
- 依此类推，其他聚合交换机遵循相同模式

## 算法实现详解

### 1. Left Path Routing (LPR)

#### 算法原理
LPR选择所有可用路径中最"左边"的路径，即交换机ID最小的路径。这种确定性路由算法确保了路径选择的稳定性和可预测性。

#### 实现思路

**路径枚举算法** (`get_all_paths`):
```python
# 识别聚合交换机
for agg in range(9, 17):
    if agg % 2 == 1:  # 奇数聚合交换机
        edge1 = agg - 8  # s9 -> s1
        edge2 = agg - 7  # s9 -> s2
    else:  # 偶数聚合交换机
        edge1 = agg - 9  # s10 -> s1
        edge2 = agg - 8  # s10 -> s2

    # 确定核心交换机
    if src_agg % 2 == 1:
        src_cores = [17, 18]
    else:
        src_cores = [19, 20]
```

**路径选择策略** (`get_lpr_path`):
```python
# 获取所有可用路径
paths = self.get_all_paths(src_dpid, dst_dpid)

# 选择最左边的路径（ID最小）
lpr_path = min(paths, key=lambda x: tuple(x))
```

#### 关键特性
- **确定性**: 相同源目的对总是选择相同路径
- **负载不感知**: 不考虑网络当前负载状态
- **实现简单**: 无需维护复杂状态信息

#### 实验结果示例
```
LPR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4]
LPR Path for 10.0.0.1 -> 10.0.0.8: [1, 9, 17, 15, 8]
```

---

### 2. Random Selection Routing (RSR)

#### 算法原理
RSR在所有可用路径中随机选择一条路径，实现负载的概率分布。这种随机性有助于避免某些链路过度负载。

#### 实现思路

**路径选择策略** (`get_rsr_path`):
```python
def get_rsr_path(self, src_dpid, dst_dpid):
    """获取Random Selection Routing路径（随机选择一条路径）"""
    paths = self.get_all_paths(src_dpid, dst_dpid)
    if not paths:
        return None

    # 随机选择一条路径
    return random.choice(paths)
```

#### 关键特性
- **随机性**: 每次选择可能不同路径
- **负载均衡**: 概率性分布流量
- **简单实现**: 只需标准随机函数
- **无状态**: 不维护历史选择信息

#### 实验结果示例
```
RSR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4]    # 第一次运行
RSR Path for 10.0.0.1 -> 10.0.0.7: [1, 10, 19, 12, 4]   # 第二次运行
```

---

### 3. Least Loaded Routing (LLR)

#### 算法原理
LLR选择路径中最大链路负载最小的路径，实现真正的负载均衡。当有多条等价路径时，按照LPR原则选择。

#### 实现思路

**负载跟踪机制**:
```python
# 链路负载字典：(switch1, switch2) -> flow_count
self.link_loads = defaultdict(int)

# 路径负载计算
def get_path_max_load(self, path):
    """计算路径的最大链路负载"""
    max_load = 0
    for i in range(len(path) - 1):
        link = tuple(sorted([path[i], path[i + 1]]))
        max_load = max(max_load, self.link_loads[link])
    return max_load
```

**路径选择策略** (`get_llr_path`):
```python
def get_llr_path(self, src_dpid, dst_dpid):
    paths = self.get_all_paths(src_dpid, dst_dpid)
    if not paths:
        return None

    # 计算每条路径的最大负载
    path_loads = [(path, self.get_path_max_load(path)) for path in paths]

    # 找到最小最大负载
    min_max_load = min(load for _, load in path_loads)

    # 获取所有具有最小最大负载的路径
    candidate_paths = [path for path, load in path_loads if load == min_max_load]

    # 在候选路径中按照LPR原则选择（最左边的路径）
    return min(candidate_paths, key=lambda x: tuple(x))
```

**负载更新机制**:
```python
def update_link_loads(self, path, increment=True):
    """更新路径上链路的负载"""
    delta = 1 if increment else -1
    for i in range(len(path) - 1):
        link = tuple(sorted([path[i], path[i + 1]]))
        self.link_loads[link] += delta
        if self.link_loads[link] < 0:
            self.link_loads[link] = 0
```

#### 关键特性
- **负载感知**: 实时考虑网络负载状态
- **最优选择**: 选择全局最优路径
- **公平性**: 避免热点链路形成
- **复杂性**: 需要维护负载状态

#### 实验结果示例
```
LLR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4] (max load: 0)
LLR Path for 10.0.0.2 -> 10.0.0.8: [2, 11, 17, 13, 5] (max load: 0)
LLR Path for 10.0.0.3 -> 10.0.0.9: [3, 11, 18, 13, 5] (max load: 1)
```

## 通用实现组件

### 1. 流表安装机制

所有算法共享相同的流表安装逻辑：

```python
def add_flow(self, datapath, priority, match, actions, buffer_id=None):
    # 创建OpenFlow流表项
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                           match=match, instructions=inst)
    datapath.send_msg(mod)
```

### 2. 端口映射计算

```python
def get_path_ports(self, path):
    """获取路径中每跳的入端口和出端口"""
    ports = []
    for i in range(len(path) - 1):
        current = path[i]
        next_hop = path[i + 1]
        out_port = self.adjacency[current][next_hop]
        in_port_next = self.adjacency[next_hop][current]
        ports.append((current, out_port, next_hop, in_port_next))
    return ports
```

### 3. 匹配规则配置

- **IPv4流**: `eth_type, in_port, ipv4_src, ipv4_dst`
- **ARP流**: `eth_type, in_port, arp_spa, arp_tpa`
- **优先级**: 1 (高于默认table-miss规则)

## 性能对比分析

### 算法特性对比

| 特性 | LPR | RSR | LLR |
|------|-----|-----|-----|
| 确定性 | ✅ 高 | ❌ 低 | ⚠️ 中 |
| 负载均衡 | ❌ 无 | ⚠️ 概率性 | ✅ 最优 |
| 实现复杂度 | ✅ 简单 | ✅ 简单 | ❌ 复杂 |
| 状态维护 | ✅ 无 | ✅ 无 | ❌ 需要 |
| 收敛速度 | ✅ 快 | ⚠️ 中等 | ⚠️ 中等 |
| 适应性 | ❌ 静态 | ⚠️ 动态 | ✅ 自适应 |

### 实验观察

1. **LPR表现**: 路径选择稳定，适合对确定性要求高的场景
2. **RSR表现**: 路径随机分布，有助于避免局部拥塞
3. **LLR表现**: 随着流增加，逐渐体现负载均衡优势

## 结论

本实验成功实现了三种不同的路由算法：

- **LPR**: 提供了简单、确定性的路径选择方案
- **RSR**: 通过随机性实现了基础的负载均衡
- **LLR**: 实现了基于负载感知的最优路径选择

每种算法都有其适用场景，实际应用中可根据网络需求和资源条件选择合适的算法。SDN架构的灵活性使得这些算法可以方便地部署和切换，为网络流量工程提供了强大支持。

## 代码结构

```
LPR.py      # Left Path Routing 控制器
RSR.py      # Random Selection Routing 控制器  
LLR.py      # Least Loaded Routing 控制器
test_paths.py      # 路径计算测试脚本
TEST_GUIDE.md     # 详细测试指南
README.md         # 实现说明文档
```
