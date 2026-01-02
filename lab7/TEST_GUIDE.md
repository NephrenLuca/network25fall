# Lab 7：网络层控制平面流表下发 - 详细测试指南

## 目录
1. [测试环境准备](#测试环境准备)
2. [LPR算法测试](#lpr算法测试)
3. [RSR算法测试](#rsr算法测试)
4. [LLR算法测试](#llr算法测试)
5. [输出截图要求](#输出截图要求)
6. [常见问题及解决方案](#常见问题及解决方案)
7. [实验报告要求](#实验报告要求)

---

## 测试环境准备

### 1. 环境依赖检查
确保以下软件已正确安装：
- Ryu Controller (Python 3.8环境)
- Mininet
- Open vSwitch (OVS)

### 2. 激活正确的Python环境
```bash
# 激活包含Ryu的conda环境
conda activate myenv3_8

# 验证环境
which ryu-manager
ryu-manager --version
```

### 3. 验证安装
```bash
# 检查Python版本（应为3.8）
python --version

# 检查Ryu版本（在激活环境后）
ryu-manager --version

# 检查Mininet
mn --version
```

### 4. 启动Open vSwitch服务
```bash
# 检查OVS状态
sudo systemctl status openvswitch-switch

# 如果未启动，启动服务
sudo systemctl start openvswitch-switch

# 验证OVS
sudo ovs-vsctl show
```

### 5. 快速环境检查
运行快速检查脚本：
```bash
python quick_test.py
```
此脚本会自动检查所有依赖并报告问题。

---

## LPR算法测试

### 测试步骤

#### 步骤1：启动Ryu控制器
打开第一个终端：
```bash
cd /home/ling/network/lab7
ryu-manager LPR.py --observe-links --verbose
```
等待看到类似输出：
```
loading app LPR.py
instantiating app LPR.py
...
switch_features_handler is called
```

#### 步骤2：启动Mininet拓扑
打开第二个终端：
```bash
cd /home/ling/network/lab7
sudo python parallel_traffic_generator.py
```

#### 步骤3：观察输出
在Ryu控制器终端观察路径选择输出，格式类似：
```
LPR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4]
LPR Path for 10.0.0.1 -> 10.0.0.8: [1, 9, 17, 15, 8]
...
```

#### 步骤4：验证流表安装
在Mininet终端等待测试完成，或手动开启CLI验证：
```bash
# 修改parallel_traffic_generator.py第131行，取消注释
CLI(net)
```

然后在Mininet CLI中验证：
```bash
# 查看交换机流表
sh ovs-ofctl dump-flows s1
sh ovs-ofctl dump-flows s9
sh ovs-ofctl dump-flows s17
```

#### 步骤5：记录路径信息
根据你的学号最后两位计算：
- x = 学号后两位
- 测试路径：H{x%16} → H{(x+4)%16} 和 H{x%16} → H{(x+5)%16}

例如，学号后两位为01：
- H1 → H5 (10.0.0.1 → 10.0.0.5)
- H1 → H6 (10.0.0.1 → 10.0.0.6)

---

## RSR算法测试

### 测试步骤

#### 步骤1：启动Ryu控制器
```bash
ryu-manager RSR.py --observe-links --verbose
```

#### 步骤2：启动Mininet拓扑
```bash
sudo python parallel_traffic_generator.py
```

#### 步骤3：观察输出
RSR会随机选择路径，输出格式：
```
RSR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4]
RSR Path for 10.0.0.1 -> 10.0.0.8: [1, 10, 19, 16, 8]
...
```

#### 步骤4：多次运行对比
运行多次测试，观察同一对主机是否选择不同路径：
```bash
# 重新运行多次，观察路径变化
sudo python parallel_traffic_generator.py
```

#### 步骤5：记录路径信息
同样根据学号记录H{x%16} → H{(x+4)%16} 和 H{x%16} → H{(x+5)%16}的路径

---

## LLR算法测试

### 测试步骤

#### 步骤1：启动Ryu控制器
```bash
ryu-manager LLR.py --observe-links --verbose
```

#### 步骤2：启动Mininet拓扑
```bash
sudo python sequential_traffic_generator.py
```

#### 步骤3：观察输出
LLR会显示路径和负载信息：
```
LLR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4] (max load: 0)
LLR Path for 10.0.0.1 -> 10.0.0.8: [1, 9, 17, 15, 8] (max load: 0)
...
```

#### 步骤4：分析负载变化
观察前10条流的路径选择，注意max load值的变化：
- 初始所有路径负载为0
- 随着流增加，某些路径的负载会增加
- 新流会选择负载较小的路径

#### 步骤5：记录前10条流路径
测试过程中记录前10条流的路径信息

---

## 输出截图要求

### LPR/RSR输出截图

#### 要求格式：
```
Path for 10.0.0.x -> 10.0.0.y: [交换机路径列表]
```

#### 示例：
```
Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4]
Path for 10.0.0.1 -> 10.0.0.8: [1, 9, 17, 15, 8]
```

#### 截图内容：
1. Ryu控制器终端的路径输出
2. 清晰显示学号对应的主机对路径选择
3. 包含完整的交换机路径列表

### LLR输出截图

#### 要求：
- 记录前10条流的路径选择
- 显示每条路径的max load值
- 展示负载均衡效果

#### 示例：
```
LLR Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4] (max load: 0)
LLR Path for 10.0.0.2 -> 10.0.0.8: [2, 11, 17, 13, 5] (max load: 0)
...
```

### 额外验证截图

#### iperf流建立验证：
1. 在Mininet中开启CLI
2. 检查iperf进程状态
3. 截取一条iperf流的输出示例

```bash
# Mininet CLI命令
iperf -c 10.0.0.7 -u -p 5000 -b 1M -t 5
```

---

## 常见问题及解决方案

### 问题1：Ryu控制器无法启动
**症状**：`Address already in use` 错误

**解决方案**：
```bash
# 查找并杀死已有进程
ps aux | grep ryu
kill -9 <pid>

# 或者使用不同端口
ryu-manager LPR.py --observe-links --verbose --ofp-tcp-listen-port 6634
```

### 问题2：Mininet卡在"Starting switches"
**症状**：显示 `*** Starting 1 switches s1 ...` 后停止响应

**解决方案**：
```bash
# 检查OVS服务状态
sudo systemctl status openvswitch-switch

# 重启OVS服务
sudo systemctl restart openvswitch-switch

# 清理已有进程
sudo pkill -f mn
sudo pkill -f ryu
```

### 问题3：无路径输出或连接失败
**症状**：Ryu无路径选择输出，Mininet显示连接失败

**解决方案**：
1. 检查网络连接顺序：先启动Ryu，再启动Mininet
2. 确认Ryu监听在6633端口：
   ```bash
   netstat -tlnp | grep 6633
   ```
3. 检查拓扑发现：确保使用了 `--observe-links` 参数

### 问题4：流表安装失败
**症状**：Packet-in事件重复触发

**解决方案**：
1. 检查流表优先级设置
2. 验证匹配字段正确性
3. 确认交换机datapath存在：
   ```bash
   # 在Ryu控制器中检查
   print("Available switches:", list(self.datapath_list.keys()))
   ```

### 问题5：LLR负载计算异常
**症状**：负载值异常或路径选择不符合预期

**解决方案**：
1. 检查链路负载更新逻辑
2. 验证路径计算正确性
3. 运行路径测试：
   ```bash
   python test_paths.py
   ```

### 问题6：内存或性能问题
**症状**：程序运行缓慢或内存不足

**解决方案**：
1. 减少测试时间
2. 清理流表缓存
3. 检查Python进程资源使用

### 问题7：Conda环境问题
**症状**：ryu-manager命令找不到

**解决方案**：
```bash
# 激活正确的环境
conda activate myenv3_8

# 或者使用完整路径
/home/ling/miniconda3/envs/myenv3_8/bin/ryu-manager LPR.py --observe-links --verbose
```

### 问题8：端口冲突
**症状**：控制器启动失败，提示端口被占用

**解决方案**：
```bash
# 检查端口使用
netstat -tlnp | grep 6633

# 使用不同端口
ryu-manager LPR.py --observe-links --verbose --ofp-tcp-listen-port 6634
# 相应地修改Mininet控制器端口
```

### 问题9：拓扑发现失败
**症状**：控制器没有收到switch enter事件

**解决方案**：
1. 确保使用了 `--observe-links` 参数
2. 检查LLDP数据包是否被正确处理
3. 在控制器中添加调试输出：
   ```python
   @set_ev_cls(event.EventLinkAdd, MAIN_DISPATCHER)
   def link_add_handler(self, ev):
       print(f"Link added: {ev.link.src.dpid} -> {ev.link.dst.dpid}")
   ```

---

## 调试技巧

### 1. 启用详细日志
```bash
# Ryu控制器详细日志
ryu-manager LPR.py --observe-links --verbose --log-level DEBUG

# Mininet详细日志
sudo python parallel_traffic_generator.py 2>&1 | tee mininet.log
```

### 2. 检查网络连接
```bash
# 在Mininet CLI中
pingall  # 检查所有主机连通性
iperf h1 h2  # 测试带宽
net  # 查看网络拓扑
```

### 3. 监控流表变化
```bash
# 实时监控流表
watch -n 1 "sudo ovs-ofctl dump-flows s1 | head -20"

# 比较不同时刻的流表
sudo ovs-ofctl dump-flows s1 > flows_before.txt
# ... 运行测试 ...
sudo ovs-ofctl dump-flows s1 > flows_after.txt
diff flows_before.txt flows_after.txt
```

### 4. 控制器状态检查
在Ryu控制器中添加临时调试代码：
```python
# 在_packet_in_handler开始处添加
print(f"Current switches: {list(self.datapath_list.keys())}")
print(f"Current flows: {len(self.installed_flows)}")
print(f"Adjacency table size: {len(self.adjacency)}")
```

---

## 实验报告要求

### 1. 报告结构
1. **引言**：实验目的和背景介绍
2. **理论分析**：三种路由算法的原理说明
3. **实现方案**：代码架构和关键技术说明
4. **测试结果**：详细的测试过程和结果分析
5. **结论**：算法性能对比和实验总结

### 2. 必须包含内容

#### 算法设计分析
- LPR：确定性路径选择的优势和局限性
- RSR：随机性带来的负载均衡效果
- LLR：负载感知路由的实现机制

#### 运行结果截图
- LPR算法路径选择结果
- RSR算法的随机性验证（多次运行对比）
- LLR算法的负载均衡效果
- iperf流量成功建立的证明

#### 性能分析
- 对比三种算法的路径分布
- 分析LLR的负载均衡效果
- 讨论实际应用场景

### 3. 提交文件清单
- LPR.py
- RSR.py
- LLR.py
- 实验报告（PDF格式）
- 测试截图

### 4. 评分要点
- ✅ 算法实现正确性 (40%)
- ✅ 代码结构和注释 (20%)
- ✅ 测试结果完整性 (20%)
- ✅ 报告分析深度 (20%)

---

## 快速测试检查清单

- [ ] Ryu控制器正常启动（显示switch features）
- [ ] Mininet拓扑创建成功（显示主机连接）
- [ ] 路径选择输出正常显示
- [ ] iperf流能够建立
- [ ] 流表正确安装（无重复packet-in）
- [ ] LLR负载值正确更新
- [ ] 所有截图清晰可读
- [ ] 报告内容完整详细

---

## 技术支持

如遇到问题，请：
1. 检查上述常见问题解决方案
2. 查看Ryu和Mininet日志输出
3. 使用调试模式运行：
   ```bash
   ryu-manager LPR.py --observe-links --verbose --log-level DEBUG
   ```
4. 参考代码注释和README.md文档
