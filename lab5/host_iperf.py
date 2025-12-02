#!/usr/bin/env python3
"""
任务2：在虚拟终端上执行任务
拓扑结构：
- H1: IP 10.0.0.1, MAC 00:00:00:00:ff01, 20M bps, 2ms
- H3: IP 10.0.0.3, MAC 00:00:00:00:ff03
- H4: IP 10.0.0.2, MAC 00:00:00:00:ff02
- S1: 20M bps, 2ms
- S2: 20M bps, 10ms
- S1-S2: Loss 10%

TCP Flow 1: h1->h3, 0-20sec
TCP Flow 2: h1->h4, 10-30sec (注意：拓扑中没有h2，应该是h1->h4)
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
import time
import os

class IperfTopo(Topo):
    """任务2的拓扑类"""
    
    def build(self, loss=10):
        # 创建交换机
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        
        # 创建主机，设置IP和MAC地址
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:ff:01')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:ff:03')
        h4 = self.addHost('h4', ip='10.0.0.2/24', mac='00:00:00:00:ff:02')
        
        # 添加链路
        # H1 -> S1: 20M bps, 2ms
        self.addLink(h1, s1, bw=20, delay='2ms', cls=TCLink)
        
        # S1 -> S2: 20M bps, 10ms, 丢包率
        self.addLink(s1, s2, bw=20, delay='10ms', loss=loss, cls=TCLink)
        
        # S2 -> H3: 默认参数
        self.addLink(s2, h3, cls=TCLink)
        
        # S2 -> H4: 默认参数
        self.addLink(s2, h4, cls=TCLink)

def run_iperf_server(host, port=5001):
    """在主机上运行iperf服务器"""
    host.cmd('iperf -s -p {} &'.format(port))
    time.sleep(1)

def run_iperf_client(host, server_ip, port=5001, duration=20, interval=0.5, output_file=None):
    """在主机上后台运行iperf客户端，每interval秒测量一次

    注意：使用 host.popen 而不是 host.cmd，避免在多线程/并发场景下
    触发 Mininet 中 host.shell 的断言错误。
    """
    cmd = 'iperf -c {} -p {} -t {} -i {}'.format(server_ip, port, duration, interval)
    if output_file:
        cmd += ' > {} 2>&1'.format(output_file)
    # 通过 /bin/sh -c 执行带重定向的命令
    return host.popen(['sh', '-c', cmd])

def main():
    setLogLevel('info')
    
    # 创建网络
    topo = IperfTopo(loss=10)  # 默认10%丢包率
    # 使用 OVSController，避免 “c0 cannot find controller” 等错误
    net = Mininet(topo=topo, controller=OVSController, link=TCLink)
    net.start()
    
    h1, h3, h4 = net.get('h1', 'h3', 'h4')
    
    print("=" * 60)
    print("任务2：TCP流测试")
    print("=" * 60)
    print("拓扑已创建")
    print("H1: 10.0.0.1")
    print("H3: 10.0.0.3")
    print("H4: 10.0.0.2")
    print("S1-S2链路丢包率: 10%")
    print("=" * 60)
    
    # 启动iperf服务器
    print("\n启动iperf服务器...")
    run_iperf_server(h3, 5001)  # Flow 1的服务器
    run_iperf_server(h4, 5002)  # Flow 2的服务器
    time.sleep(2)
    
    # 创建输出目录
    output_dir = 'iperf_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 启动Flow 1: h1->h3, 0-20sec
    print("\n启动TCP Flow 1: h1->h3 (0-20秒)")
    flow1_file = os.path.join(output_dir, 'flow1_result.txt')
    flow1_proc = run_iperf_client(h1, '10.0.0.3', 5001, 20, 0.5, flow1_file)
    
    # 等待10秒后启动Flow 2
    print("等待10秒后启动Flow 2...")
    time.sleep(10)
    
    # 启动Flow 2: h1->h4, 10-30sec (实际运行20秒)
    print("启动TCP Flow 2: h1->h4 (10-30秒)")
    flow2_file = os.path.join(output_dir, 'flow2_result.txt')
    flow2_proc = run_iperf_client(h1, '10.0.0.2', 5002, 20, 0.5, flow2_file)
    
    # 等待所有流完成
    print("\n等待所有TCP流完成...")
    flow1_proc.wait()
    flow2_proc.wait()
    
    print("\n测试完成！")
    print("Flow 1结果保存在: {}".format(flow1_file))
    print("Flow 2结果保存在: {}".format(flow2_file))
    
    # 显示结果摘要
    print("\n" + "=" * 60)
    print("Flow 1 结果摘要:")
    print("=" * 60)
    if os.path.exists(flow1_file):
        with open(flow1_file, 'r') as f:
            print(f.read())
    
    print("\n" + "=" * 60)
    print("Flow 2 结果摘要:")
    print("=" * 60)
    if os.path.exists(flow2_file):
        with open(flow2_file, 'r') as f:
            print(f.read())
    
    # 清理
    h3.cmd('killall iperf 2>/dev/null')
    h4.cmd('killall iperf 2>/dev/null')
    
    print("\n输入 'exit' 退出，或使用CLI进行进一步测试")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    main()

