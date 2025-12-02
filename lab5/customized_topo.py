#!/usr/bin/env python3
"""
任务1：定制化拓扑
拓扑结构：
- H1: 10M bps, 2ms
- H2: 20M bps, 10ms
- H3: 10M bps, 2ms
- H4: Iperf Server @ 10.0.0.4
- S1, S2: 交换机
连接：H1->S1, H2->S1, S1->S2, S2->H3, S2->H4
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel

class MyTopo(Topo):
    """自定义拓扑类"""
    
    def build(self):
        # 创建交换机
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        
        # 创建主机
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')
        
        # 添加链路，设置带宽和延迟
        # H1 -> S1: 10M bps, 2ms
        self.addLink(h1, s1, bw=10, delay='2ms')
        
        # H2 -> S1: 20M bps, 10ms
        self.addLink(h2, s1, bw=20, delay='10ms')
        
        # S1 -> S2: 默认参数（无限制）
        self.addLink(s1, s2)
        
        # S2 -> H3: 10M bps, 2ms
        self.addLink(s2, h3, bw=10, delay='2ms')
        
        # S2 -> H4: 默认参数（无限制）
        self.addLink(s2, h4)

# 用于命令行测试
topos = {'mytopo': (lambda: MyTopo())}

if __name__ == '__main__':
    setLogLevel('info')
    
    # 创建网络
    topo = MyTopo()
    # 使用 OVSController，而不是默认的“controller”二进制，避免出现
    # “c0 cannot find controller” 这类错误
    net = Mininet(topo=topo, controller=OVSController)
    net.start()
    
    print("拓扑已创建，可以使用以下命令测试：")
    print("  h1 ping h2")
    print("  h2 ping h4")
    print("  h3 ping h4")
    print("  iperf测试：h1 iperf -c h2 -t 10")
    print("输入 'exit' 退出")
    
    CLI(net)
    net.stop()


