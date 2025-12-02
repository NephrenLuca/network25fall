#!/usr/bin/env python3
"""
任务1的自动测试脚本
测试拓扑和iperf带宽验证
"""

from mininet.net import Mininet
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel
from customized_topo import MyTopo
import time
import os

def test_bandwidth(net, host1, host2, test_name):
    """测试两个主机之间的带宽"""
    print("\n" + "=" * 60)
    print("测试: {} -> {}".format(host1.name, host2.name))
    print("=" * 60)
    
    # 启动iperf服务器
    host2.cmd('iperf -s &')
    time.sleep(1)
    
    # 运行iperf客户端，测试10秒
    result = host1.cmd('iperf -c {} -t 10 -i 1'.format(host2.IP()))
    
    # 停止iperf服务器
    host2.cmd('killall iperf 2>/dev/null')
    
    print(result)
    
    # 保存结果
    output_dir = 'test_results'
    os.makedirs(output_dir, exist_ok=True)
    result_file = os.path.join(output_dir, 'task1_{}.txt'.format(test_name))
    with open(result_file, 'w') as f:
        f.write("测试: {} -> {}\n".format(host1.name, host2.name))
        f.write("=" * 60 + "\n")
        f.write(result)
    
    print("结果已保存到: {}".format(result_file))
    return result

def main():
    setLogLevel('info')
    
    print("=" * 60)
    print("任务1：定制化拓扑测试")
    print("=" * 60)
    
    net = None
    try:
        # 创建网络
        print("\n正在创建网络拓扑...")
        topo = MyTopo()
        # 使用 OVSController，避免旧版“controller”二进制缺失导致 c0 无法启动
        net = Mininet(topo=topo, controller=OVSController)
        
        print("正在启动网络（这可能需要几秒钟）...")
        net.start()
        print("网络启动成功！\n")
        
        h1, h2, h3, h4 = net.get('h1', 'h2', 'h3', 'h4')
        
        print("\n拓扑信息:")
        print("H1: {} (10M bps, 2ms)".format(h1.IP()))
        print("H2: {} (20M bps, 10ms)".format(h2.IP()))
        print("H3: {} (10M bps, 2ms)".format(h3.IP()))
        print("H4: {} (Iperf Server)".format(h4.IP()))
        
        # 测试ping连通性
        print("\n" + "=" * 60)
        print("测试连通性 (pingall)")
        print("=" * 60)
        net.pingAll()
        
        # 测试带宽
        print("\n" + "=" * 60)
        print("开始带宽测试")
        print("=" * 60)
        
        # H1 -> H2: 应该约10Mbps, ~12ms延迟
        test_bandwidth(net, h1, h2, 'h1_h2')
        
        # H2 -> H4: 应该<<16Mbps, ~22ms延迟
        test_bandwidth(net, h2, h4, 'h2_h4')
        
        # H3 -> H4: 应该约10Mbps, ~12ms延迟
        test_bandwidth(net, h3, h4, 'h3_h4')
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        print("\n可以使用以下命令进行交互式测试：")
        print("  h1 ping h2")
        print("  h1 iperf -c h2 -t 10")
        print("输入 'exit' 退出")
        
        CLI(net)
    except KeyboardInterrupt:
        print("\n\n用户中断了程序")
    except Exception as e:
        print("\n\n发生错误: {}".format(e))
        import traceback
        traceback.print_exc()
    finally:
        if net is not None:
            print("\n正在清理网络...")
            net.stop()
            print("清理完成")

if __name__ == '__main__':
    main()

