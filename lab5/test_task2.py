#!/usr/bin/env python3
"""
任务2的自动测试脚本
测试不同丢包率下的TCP流性能
"""

from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink
from mininet.log import setLogLevel
from host_iperf import IperfTopo
import time
import os

def run_iperf_server(host, port=5001):
    """在主机上运行iperf服务器"""
    host.cmd('iperf -s -p {} &'.format(port))
    time.sleep(1)

def run_iperf_client(host, server_ip, port=5001, duration=20, interval=0.5, output_file=None):
    """在主机上后台运行iperf客户端"""
    cmd = 'iperf -c {} -p {} -t {} -i {}'.format(server_ip, port, duration, interval)
    if output_file:
        cmd += ' > {} 2>&1'.format(output_file)
    # 使用 host.popen 而不是 host.cmd，避免多线程下的 shell 断言错误
    return host.popen(['sh', '-c', cmd])

def test_with_loss_rate(loss_rate):
    """使用指定丢包率进行测试"""
    print("\n" + "=" * 70)
    print("测试丢包率: {}%".format(loss_rate))
    print("=" * 70)
    
    # 创建网络，使用 OVSController 作为控制器实现
    topo = IperfTopo(loss=loss_rate)
    net = Mininet(topo=topo, controller=OVSController, link=TCLink)
    net.start()
    
    h1, h3, h4 = net.get('h1', 'h3', 'h4')
    
    # 创建输出目录
    output_dir = 'test_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 启动iperf服务器
    print("启动iperf服务器...")
    run_iperf_server(h3, 5001)
    run_iperf_server(h4, 5002)
    time.sleep(2)
    
    # Flow 1: h1->h3, 0-20sec
    print("启动TCP Flow 1: h1->h3 (0-20秒)")
    flow1_file = os.path.join(output_dir, 'flow1_loss{}_result.txt'.format(loss_rate))
    flow1_proc = run_iperf_client(h1, '10.0.0.3', 5001, 20, 0.5, flow1_file)
    
    # 等待10秒后启动Flow 2
    print("等待10秒后启动Flow 2...")
    time.sleep(10)
    
    # Flow 2: h1->h4, 10-30sec
    print("启动TCP Flow 2: h1->h4 (10-30秒)")
    flow2_file = os.path.join(output_dir, 'flow2_loss{}_result.txt'.format(loss_rate))
    flow2_proc = run_iperf_client(h1, '10.0.0.2', 5002, 20, 0.5, flow2_file)
    
    # 等待所有流完成
    print("等待所有TCP流完成...")
    flow1_proc.wait()
    flow2_proc.wait()
    
    # 显示结果摘要
    print("\nFlow 1 结果 (前20行):")
    if os.path.exists(flow1_file):
        with open(flow1_file, 'r') as f:
            lines = f.readlines()
            for line in lines[:20]:
                print(line.rstrip())
    
    print("\nFlow 2 结果 (前20行):")
    if os.path.exists(flow2_file):
        with open(flow2_file, 'r') as f:
            lines = f.readlines()
            for line in lines[:20]:
                print(line.rstrip())
    
    # 清理
    h3.cmd('killall iperf 2>/dev/null')
    h4.cmd('killall iperf 2>/dev/null')
    
    print("\n结果已保存到:")
    print("  {}".format(flow1_file))
    print("  {}".format(flow2_file))
    
    net.stop()
    time.sleep(1)

def main():
    setLogLevel('info')
    
    print("=" * 70)
    print("任务2：不同丢包率下的TCP流测试")
    print("=" * 70)
    
    # 测试不同的丢包率
    loss_rates = [0, 1, 5, 10, 20]
    
    for loss_rate in loss_rates:
        test_with_loss_rate(loss_rate)
        time.sleep(2)  # 等待网络清理
    
    print("\n" + "=" * 70)
    print("所有测试完成！")
    print("=" * 70)
    print("结果文件保存在 test_results/ 目录下")
    print("可以比较不同丢包率下的性能差异")

if __name__ == '__main__':
    main()


