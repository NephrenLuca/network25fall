# Lab 7：网络层控制平面流表下发

## 一、基本介绍

实验用到的网络组件：&#x20;

* Ryu Controller：OpenFlow接口之上，可以在Ryu编写自己的控制程序，基于Python&#x20;
* OpenFlow VirtualSwitch：OpenFlow接口之下，行为与硬件交换机一致，性能弱于硬件交换机&#x20;
* mininet：网络模拟平台，建立虚拟的OpenFlow网络

Ryu控制器安装：

* 推荐方式：使用conda创建虚拟环境，使用python3.8和旧版本的setuptools（如果你mininet的python依赖也是放在虚拟环境里的，不需要修改原有的mininet环境，新开一个conda环境即可）

```
conda create -n <环境名称> python=3.8
conda activate <环境名称>
pip uninstall setuptools
pip install setuptools==67.6.1
pip install ryu
pip install eventlet==0.30.2
```

* 方式2：从源码安装，也同样需要使用python3.8并且使用旧版本setuptools\
  git clone <https://github.com/faucetsdn/ryu.git> ; cd ryu; pip install .&#x20;

* ryu-manager --version 指令查看是否安装成功

  \*如果同学按照conda虚拟环境的方式执行给出所有指令，则应当看到如下提示\
  ![](https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2FDjmoiycBCweb2IMQhJz0%2Fimage.png?alt=media\&token=f9583119-9d55-43a5-9e2d-b4b11d7cdee0)

* 如果ryu-manager命令报错，python版本选择3.8及以前，eventlet库版本选择0.30.2，pip install eventlet==0.30.2

参考资料： <https://ryu.readthedocs.io/en/latest/index.html>

Tips：一些报错的解决方案

ImportError：cannot import name 'ALREADY\_HANDLLED': 理论上如果按照conda虚拟环境方式安装所给出的指令执行，在未安装eventlet时会报错，安装0.30.2的eventlet后报错消失\
&#x20;<https://github.com/faucetsdn/ryu/pull/166>

ryu-manager启动报错 “OSError: \[Errno 98] Address already in use”：<https://blog.csdn.net/jiao424525707/article/details/103059456>

### 1. OpenFlow VirtualSwitch (OVS)

* 传递虚拟机VM之间的流量&#x20;
* 以及实现VM和外界网络的通信

<figure><img src="https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2F9CpI3IFZZe4nOTiq7kal%2Fimage.png?alt=media&#x26;token=20f6ea80-d021-422c-93d9-944b1f9a56ae" alt="" width="519"><figcaption><p>OpenFlow VirtualSwitch（OVS）</p></figcaption></figure>

OVS中一些关键的概念：

* Bridge: 代表一个以太网交换机（Switch）
* Port: 端口是收发数据包的单元，每个 Port 都隶属于一个 Bridge
* Interface: OVS与外部交换数据包的组件，一个接口就是一个网卡
* Datapath: 在 OVS 中，datapath负责执行数据交换，每个交换机有一个datapath-id
* Flow table:定义了端口之间数据包的交换规则

工作流程与原理：

<figure><img src="https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2FlmzwoWHDmZvbKF3rf16M%2F%E4%BC%81%E4%B8%9A%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_17308778879146.png?alt=media&#x26;token=83b90b30-6cbe-46ce-ba93-012c346a4fc7" alt="" width="563"><figcaption><p>OVS工作流程示意图</p></figcaption></figure>

<figure><img src="https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2Fr1sWnyeXq85XDM0SJUGY%2Fimage.png?alt=media&#x26;token=a99bb918-20c6-4f3f-b8c0-cbc3f9512ec3" alt="" width="563"><figcaption><p>OVS架构</p></figcaption></figure>

Datapath：

* 把从接收端口收到的数据包在流表中进行匹配，并执行匹配到的动作

vswitchd：

* OVS的核心部件，实现交换功能&#x20;
* 和上层 controller 通信遵从 OPENFLOW 协议&#x20;
* 和内核模块通过netlink通信

ovsdb：

* 存了整个OVS 的配置信息&#x20;
* ovs-vswitchd 会根据数据库中的配置信息工作

OVS命令行工具

* ovs-dpctl：用来配置交换机内核模块，可以控制转发规则&#x20;
* ovs-ofctl：用来控制OVS 作为OpenFlow 交换机工作时候的流表内容&#x20;
* ovs-vsctl：主要是获取或者更改ovs-vswitchd 的配置信息&#x20;
* ovsdb-tool：数据库管理工具

命令行工具： ovs-ofctl

```
ovs-ofctl --help               显示功能及用法
ovs-ofctl show SWITCH           查看设备信息 	  ovs-ofctl show s1
ovs-ofctl dump-flows SWITCH       输出交换机内流表     ovs-ofctl dump-flows s1
ovs-ofctl add-flow SWITCH FLOW    添加流	    ovs-ofctl add-flow s1 in_port=1,actions=output:2
```

命令行工具： ovs-dpctl

```
ovs-dpctl --help           显示功能及用法

ovs-dpctl dump-flows       输出OVS的kernel flow cache表
; 是整个OpenFlow流表的子集，存在OVS‘s flow cache，5s内失效，这使得OVS可以支持很大的流表

ovs-dpctl show 		   显示包查找信息（包数/字节数/命中率）-s见各端口细节
```

### 2. Ryu使用指南

运行指令：ryu-manager yourapp.py&#x20;

<https://github.com/faucetsdn/ryu/tree/master/ryu/app> 中有一些例子可供参考，我们下面的例子中给出的参考是simple\_switch.py

应用举例：

开启两个terminal，在两个terminal分别输入step1和step2的指令&#x20;

Step 1：Openflow控制器端：ryu-manager simple\_switch.py --verbose&#x20;

Step 2：Mininet生成网络：sudo mn --topo single,3 --mac --switch ovsk --controller remote&#x20;

下文为对step2的指令的解释

* mininet 创建三个虚拟主机，给定IP地址&#x20;
* 在内核中创建一个三端口的Openflow软件交换机&#x20;
* 通过虚拟的以太网线缆连接虚拟主机与软件交换机&#x20;
* 为每个主机设置MAC地址&#x20;
* 连接软件交换机与控制器

注：simple\_switchl2/l3/l4/l5.py用不同的openflow协议版本实现同样的功能

Step 3：ovs-ofctl观察流表

在运行step2后你应该观察到如下输出\<connecting to remote controller at 6653>，证明你前面的环境配置均正确

<figure><img src="https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2FykkR26ZnXLVnik8ratlA%2Fimage.png?alt=media&#x26;token=a9cf1878-698e-496d-a0e9-85543cb24a92" alt=""><figcaption></figcaption></figure>

参考如下指示的顺序1\~3执行并观察现象

<figure><img src="https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2FlpEjgqovzZtcPdTWC1Uz%2Fimage.png?alt=media&#x26;token=2b1b36a4-022e-4f54-8b34-2142eab6e09a" alt=""><figcaption></figcaption></figure>

<mark style="color:red;">**请同学们尝试一下这个例子，来验证所需的软件已经成功安装且能正常运行**</mark>

### 3. Ryu组件介绍与代码分析

在以 example\_switch\_13.py 为主进行代码分析前，首先让我们来介绍一下ARP：

Question: 已知IP地址，如何确定接口的MAC地址?

<figure><img src="https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2FQs4jLlFT81AwegtIC7iK%2F1730899736291.png?alt=media&#x26;token=00795d07-9bd8-4684-811b-06358be6f8fc" alt="" width="328"><figcaption><p>接口的MAC地址</p></figcaption></figure>

* 在LAN上的每个IP节点都有一个ARP表&#x20;
* ARP表：包括一些LAN节点IP/MAC地址的映射 < IP address; MAC address; TTL>&#x20;
  * TTL时间是指地址映射失效的时间&#x20;
  * 典型是20min

ARP协议在同一个LAN中

* A要发送帧给B(B的IP地址已知)， 但B的MAC地址不在A的ARP表中&#x20;
* A广播包含B的IP地址的ARP查询包&#x20;
  * Dest MAC address =FF-FF-FF-FF-FF-FF&#x20;
  * LAN上的所有节点都会收到该查询包&#x20;
* B接收到ARP包，回复A自己的MAC地址&#x20;
  * 帧发送给A&#x20;
  * 用A的MAC地址（单播）
* A在自己的ARP表中，缓存IP-to-MAC地址映射关系，直到信息超时&#x20;
  * 软状态: 靠定期刷新维持的系统状态&#x20;
  * 定期刷新周期之间维护的状态信息可能和原有系统不一致&#x20;
* ARP是即插即用的&#x20;
  * 节点自己创建ARP的表项&#x20;
  * 无需网络管理员的干预

所谓的 learning switches 指的是A找B泛洪一次，B再找A不需要了。在A找B的时候同时在B的ARP表中记录A的端口。

现在以仓库main分支的ryu/app/example\_switch\_13.py为主分析，里面涉及到ARP

（1）初始化

<pre><code><strong>from ryu.base import app_manager
</strong>from ryu.ofproto import ofproto_v1_3


class ExampleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ExampleSwitch13, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}

</code></pre>

ryu.base.app\_manager：Ryu应用程序的中央管理

* 加载Ryu应用程序
* 为Ryu应用程序提供上下文
* 在Ryu应用程序之间路由消息
* app\_manager.RyuApp是所有Ryu Applications的基类，我们要实现一个控制器应用，必须继承该基类

OpenFlow wire protocol encoder and decoder

* ryu.ofproto.ofproto\_v1\_3    OpenFlow 1.3定义
* ryu.ofproto.ofproto\_v1\_3\_parser       实现OpenFlow 1.3的编码器和解码器
* 一直到v1\_5，类似

（2）controller处理收到的OpenFlow消息

```
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER) #装饰器 参数1：指定触发该函数的事件 参数2：协商
def _packet_in_handler(self, ev):

```

分析：

ryu.controller.controller：OpenFlow控制器的主要组件

* ryu.controller.ofp\_event OpenFlow事件类，描述了从已连接的交换机接收OpenFlow消息的过程
  * ofp\_event.EventOFPPacketIn
  * ofp\_event.EventOFPSwitchFeatures
* ryu.controller.handler.set\_ev\_cls(ev\_cls, dispatchers=None)
  * Ryu的OpenFlow控制器部分自动解码从交换机接收到的OpenFlow消息，并将这些事件发送到Ryu应用程序，该应用程序使用ryu.controller.handler.set\_ev\_cls进行下一步处理
* ryu.controller.handler.dispatcher 指定了在协商的哪个阶段生成事件传给处理器

  * 'CONFIG\_DISPATCHER’: 协商版本并发送功能请求消息
  * 'MAIN\_DISPATCHER’: 接收交换机功能信息并发送set-config消息

（3）处理未命中表项

```
@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER) 
def switch_features_handler(self, ev):    # handshake阶段
    datapath = ev.msg.datapath            # OpenFlow交换机实例
    ofproto = datapath.ofproto            #协商的openflow协议版本    
    parser = datapath.ofproto_parser    
    
    # install the table-miss flow entry.       
    match = parser.OFPMatch()             # 无参数意味着match任意一个包    
    actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]       
    self.add_flow(datapath, 0, match, actions) # 向流表下发一条表项

```

parser.OFPActionOutput(port, max\_len=65509, type\_=None, len\_=None)

用于指定Packet-Out and Flow Mod messages中的包转发

输出一个包到交换机的指定port，max\_len是能传到控制器的最大包长

除了指定的交换机端口，还可以是特定值：

* OFPP\_CONTROLLER      Sent to the controller as a Packet-In message
* OFPP\_FLOOD                    Flooded to all physical ports of the VLAN except blocked ports and receiving ports
* OFPP\_TABLE                     Perform actions in the flow table on the packet

（4）在流表中增加表项

<pre><code>def add_flow(self, datapath, priority, match, actions):  # 各协议版本传的参数有点不同，自行参考相应版本
<strong>    ofproto = datapath.ofproto    
</strong>    parser = datapath.ofproto_parser    
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)] # instruction是当包满足match时要执行的动作    
    mod = parser.OFPFlowMod(datapath=datapath, priority=priority,match=match, instructions=inst) # FlowMod可以让我们向switch内写入定义的flow entry    
    datapath.send_msg(mod) # 把flow entry发给交换机


</code></pre>

self.add\_flow(datapath, 0, match, actions) 任意匹配的优先级应该最低

parser.OFPInstructionActions(type\_, actions=None, len\_=None)

对动作本身维护，type指定操作类型

* OFPIT\_WRITE\_ACTIONS  Add an action that is specified in the current set of actions. If same type of action has been set already, it is replaced with the new action.
* OFPIT\_APPLY\_ACTIONS  Immediately apply the specified action without changing the action set.
* OFPIT\_CLEAR\_ACTIONS  Delete all actions in the current action set.

parser.OFPFlowMod(datapath, cookie=0, cookie\_mask=0, table\_id=0, command=0, idle\_timeout=0, hard\_timeout=0, priority=32768, buffer\_id=4294967295, out\_port=0, out\_group=0, flags=0, match=None, instructions=None)

修改流表项，控制器将该消息发出，以修改流表

（5）controller处理收到的OpenFlow消息

<pre><code><strong>@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
</strong><strong>def _packet_in_handler(self, ev):    
</strong><strong>  msg = ev.msg                   #switch送来的事件ev,ev.msg 是表示packet_in数据结构的一个对象  
</strong><strong>  datapath = msg.datapath        #msg.datapath是switch Datapath的一个对象，是哪个switch发来的消息  
</strong><strong>  ofproto = datapath.ofproto     #协商的版本  
</strong><strong>  parser = datapath.ofproto_parser
</strong><strong>  
</strong><strong>  dpid = datapath.id    
</strong>  self.mac_to_port.setdefault(dpid, {})    


<strong>  pkt = packet.Packet(msg.data)
</strong>    
  eth = pkt.get_protocol(ethernet.ethernet) # 获取二层包头信息    
  if eth.ethertype == ether_types.ETH_TYPE_LLDP: # ignore lldp packet        
    return   
  dst = eth.dst                   # 得到目的MAC地址
  src = eth.src                  # 得到源MAC地址  
  in_port = msg.match['in_port']
  self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)

</code></pre>

函数解释：get\_protocol(protocol): Returns the firstly found protocol that matches to the specified protocol.

\_ipv4 = pkt.get\_protocol(ipv4.ipv4)          arp\_pkt = pkt.get\_protocol(arp.arp) &#x20;

src\_ip = \_ipv4 .src                                          src\_ip = arp\_pkt.src\_ip\
dst\_ip = \_ipv4 .dst                                         dst\_ip = arp\_pkt.dst\_ip

```
# learn a mac address to avoid FLOOD next time.
self.mac_to_port[dpid][src] = in_port
if dst in self.mac_to_port[dpid]:
    out_port = self.mac_to_port[dpid][dst]
else:
    out_port = ofproto.OFPP_FLOOD
actions = [datapath.ofproto_parser.OFPActionOutput(out_port)] 
# install a flow to avoid packet_in next time
if out_port != ofproto.OFPP_FLOOD:
    match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
    self.add_flow(datapath, 1, match, actions)
# 还得把包送往该去的端口
out = parser.OFPPacketOut(datapath=datapath,buffer_id=ofproto.OFP_NO_BUFFER,in_port=in_port, actions=actions,data=msg.data)
datapath.send_msg(out)
```

## 二、实验任务

实验网络拓扑：

<figure><img src="https://4116762772-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FiTMk5wMcvy5JOiK7dkqh%2Fuploads%2FZUTafqp95rCgvWMfr9wa%2F%E4%BC%81%E4%B8%9A%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_17309838819251.png?alt=media&#x26;token=5ba897e2-dd1d-4e8b-8042-df259b0bf8fc" alt="" width="563"><figcaption><p>网络拓扑</p></figcaption></figure>

（1）要求下发流表实现以下路由算法：

* Left Path Routing (LPR)：所有的流都从最左边的路径到达目的地（注意这样路径选择的交换机的规律是什么？你可以参考下面提供的mininet代码里面怎么添加交换机的link），如H3到H8的路径为H3->S2->S9->S17->S11->S4->H8
* Random Selection Routing (RSR)：从可选路径中随机选择一条路径，选中之后随着流表失效，你选择的路径应当重新随机一条
* Least Loaded Routing (LLR): 该方案下，每个流应该选择**最大负载最小**的路径。例如H1->S1->S9->S2->H3的链路负载为(2Mbps, 2Mbps, 4Mpbs, 2Mbps) ，H1->S1->S10->S2->H3的链路负载为(3Mbps, 3Mbps, 3Mbps, 3Mbps) ，从H1到H3的路径应选择后者。如果存在多条最大负载最小值相同的路径，按照LPR原则在这多条等价路径中选择路径。（假设链路是全双工的）

实现为LPR.py，RSR.py，LLR.py，**运⾏ ryu-manager 时需要使用 --observe-links 参数**

（2）提供的通用代码：FatTree\_routing.py、parallel\_traffic\_generator.py、sequential\_traffic\_generator.py\
FatTree\_routing.py为写好的框架，需要在其中分别填充不同的策略，完成LPR,RSR,LLR三个文件。

parallel\_traffic\_generator.py、sequential\_traffic\_generator.py为mininet代码，功能如下

* 给定上述拓扑，并生成流，其中&#x20;
  * 每台host i (1<= i <=15)发送8条流，每流大小为1Mbps&#x20;
  * 其中四条流发给 (i+4)%16，另外四条流发给 (i+5)%16&#x20;
  * 所有的MAC地址给定&#x20;
* mininet启动时iperf会自动产生流&#x20;
* parallel\_traffic\_generator.py 流同时生成&#x20;
* sequential\_traffic\_generator.py 流间隔生成&#x20;
* 每个脚本持续100s

（3）实验任务提示：

你需要完成数据包的流表下发，其中对于每一跳，都应该根据你的路径选择下发如下的内容

* 下发的流表格式：具体含义可以参考文档 [match各项含义](https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#flow-match-structure)

IP包：

Match: eth\_type, in\_port, ipv4\_src, ipv4\_dst

Action: OFPActionOutput( outport )

ARP包：（由于FatTree\_routing里已经给出了一些已知条件，你可以不对arp做flooding）

Match: eth\_type, in\_port, arp\_spa, arp\_tpa

Action: OFPActionOutput( outport )

* 核心任务1：按要求计算路由
* 核心任务2：确定路由路径上每个交换机的in\_port值和out\_port值，以便写flow entry

## 三、实验要求

测试提示：测试方法参考章节2给出的运行方式，开启两个terminal，先开启ryu，后开启mininet，注意需要 **给ryu添加--observe-links 选项**

{% hint style="info" %}
在添加流表之后的一段时间内，你应该不会再见到同一个路径的数据包触发packet\_in\_handler。比如你为h1\~h7的路径添加了流表，则在一段时间内，你应该不会因为h1到h7的数据包触发packet\_in\_handler函数
{% endhint %}

* 使用parallel\_traffic\_generator.py 测试LPR.py, RSR.py

* 使用sequential\_traffic\_generator.py 测试LLR.py&#x20;

* 要求iperf流能正确建立，你需要在两个mininet文件中开启CLI，并且截取其中一条iperf的输出即可。

* LPR/RSR下输出H{x%16}→ H{(x+4)%16}及H{x%16} → H{(x+5)%16}的路径，其中x为学号的后两位 ，截图。输出没有格式限制，只需要能写明路径经过的交换机即可。一个参考格式为

  ```
  Path for 10.0.0.1 -> 10.0.0.7: [1, 9, 17, 11, 4]
  ```

* LLR下打印出前10条流的路径，截图

* 按照实验要求完成实验，提交实验报告与源码(LPR.py，RSR.py，LLR.py)，报告中需包含**算法设计分析与运行结果的截图**