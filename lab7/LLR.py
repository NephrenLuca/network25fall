from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types
from ryu.lib import mac, ip
from ryu.topology import event
from collections import defaultdict
import random


class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        # 交换机 datapath 缓存，每个switch的dpid：datapath
        self.datapath_list = {}
        # 已发现的交换机 ID 列表，用作unique，避免重复添加
        self.switches = []
        # 拓扑邻接矩阵：self.adjacency[u][v] = 从 u 到 v 的出端口号
        self.adjacency = defaultdict(dict)
        # 主机 IP -> (边缘switch dpid, 主机接入端口)
        self.hosts = {
            '10.0.0.1': (1, 1), '10.0.0.2': (1, 2),
            '10.0.0.3': (2, 1), '10.0.0.4': (2, 2),
            '10.0.0.5': (3, 1), '10.0.0.6': (3, 2),
            '10.0.0.7': (4, 1), '10.0.0.8': (4, 2),
            '10.0.0.9': (5, 1), '10.0.0.10': (5, 2),
            '10.0.0.11': (6, 1), '10.0.0.12': (6, 2),
            '10.0.0.13': (7, 1), '10.0.0.14': (7, 2),
            '10.0.0.15': (8, 1), '10.0.0.16': (8, 2),
        }
        # 链路负载跟踪：(switch1, switch2) -> flow_count
        # 假设每个流占用1Mbps带宽
        self.link_loads = defaultdict(int)
        # 已安装的流表缓存，避免重复计算路径
        self.installed_flows = set()

    def get_all_paths(self, src_dpid, dst_dpid):
        """获取两个交换机之间的所有可用路径"""
        if src_dpid == dst_dpid:
            return [[src_dpid]]

        # Fat Tree结构中的路径计算
        paths = []

        # 如果都是边缘交换机，需要通过聚合和核心层
        if src_dpid <= 8 and dst_dpid <= 8:
            # 找到连接到src和dst的聚合交换机
            src_aggs = []
            dst_aggs = []

            for agg in range(9, 17):
                if agg % 2 == 1:  # 奇数聚合交换机
                    edge1 = agg - 8
                    edge2 = agg - 7
                else:  # 偶数聚合交换机
                    edge1 = agg - 9
                    edge2 = agg - 8

                if src_dpid in [edge1, edge2]:
                    src_aggs.append(agg)
                if dst_dpid in [edge1, edge2]:
                    dst_aggs.append(agg)

            # 找到连接到这些聚合交换机的核心交换机
            for src_agg in src_aggs:
                for dst_agg in dst_aggs:
                    if src_agg == dst_agg:
                        # 同一聚合交换机，直接路径
                        paths.append([src_dpid, src_agg, dst_dpid])
                    else:
                        # 不同聚合交换机，需要通过核心层
                        src_cores = []
                        dst_cores = []

                        if src_agg % 2 == 1:
                            src_cores = [17, 18]
                        else:
                            src_cores = [19, 20]

                        if dst_agg % 2 == 1:
                            dst_cores = [17, 18]
                        else:
                            dst_cores = [19, 20]

                        # 寻找共同的核心交换机
                        for core in set(src_cores) & set(dst_cores):
                            paths.append([src_dpid, src_agg, core, dst_agg, dst_dpid])

        return paths

    def get_path_max_load(self, path):
        """计算路径的最大链路负载"""
        max_load = 0
        for i in range(len(path) - 1):
            link = tuple(sorted([path[i], path[i + 1]]))
            max_load = max(max_load, self.link_loads[link])
        return max_load

    def get_llr_path(self, src_dpid, dst_dpid):
        """获取Least Loaded Routing路径（选择最大负载最小的路径）"""
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

    def update_link_loads(self, path, increment=True):
        """更新路径上链路的负载"""
        delta = 1 if increment else -1
        for i in range(len(path) - 1):
            link = tuple(sorted([path[i], path[i + 1]]))
            self.link_loads[link] += delta
            # 确保负载不为负数
            if self.link_loads[link] < 0:
                self.link_loads[link] = 0

    def get_path_ports(self, path):
        """获取路径中每跳的入端口和出端口"""
        ports = []
        for i in range(len(path) - 1):
            current = path[i]
            next_hop = path[i + 1]
            if next_hop in self.adjacency[current]:
                out_port = self.adjacency[current][next_hop]
                # 对于下一跳，需要找到它连接回当前交换机的端口
                if current in self.adjacency[next_hop]:
                    in_port_next = self.adjacency[next_hop][current]
                    ports.append((current, out_port, next_hop, in_port_next))
                else:
                    ports.append((current, out_port, next_hop, None))
            else:
                return None
        return ports

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        print("switch_features_handler is called")
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        in_dpid = datapath.id

        # 解析报文
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # 忽略 LLDP 报文，这是因为我们打开了--observe-links参数，会用LLDP来发现拓扑
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        flow_type = None
        src_ip = None
        dst_ip = None

        if eth.ethertype == ether_types.ETH_TYPE_ARP and arp_pkt:
            flow_type = 'arp'
            src_ip = arp_pkt.src_ip
            dst_ip = arp_pkt.dst_ip
        elif eth.ethertype == ether_types.ETH_TYPE_IP and ip_pkt:
            flow_type = 'ipv4'
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
        else:
            # 只处理 ARP 与 IPv4
            return

        # 只处理映射表中已知主机
        if src_ip not in self.hosts or dst_ip not in self.hosts:
            return

        # 获取源和目的边缘交换机
        src_edge, src_port = self.hosts[src_ip]
        dst_edge, dst_port = self.hosts[dst_ip]

        # 检查是否已经为这个流安装了流表
        flow_key = (src_ip, dst_ip, flow_type)
        if flow_key in self.installed_flows:
            return

        # ---------- 路径计算：使用LLR算法 ----------
        path = self.get_llr_path(src_edge, dst_edge)
        if not path:
            print(f"No path found from {src_edge} to {dst_edge}")
            return

        # 更新链路负载
        self.update_link_loads(path, increment=True)

        print(f"LLR Path for {src_ip} -> {dst_ip}: {path} (max load: {self.get_path_max_load(path)})")

        # 记录已安装的流
        self.installed_flows.add(flow_key)

        # ---------- 在路径上安装流表 ----------
        ports_info = self.get_path_ports(path)
        if not ports_info:
            print(f"Cannot get port information for path {path}")
            return

        # 为路径上的每个交换机安装流表
        for i, (current_dpid, out_port, next_dpid, next_in_port) in enumerate(ports_info):
            current_datapath = self.datapath_list.get(current_dpid)
            if not current_datapath:
                continue

            # 确定这个交换机上的入端口
            if i == 0:  # 第一个交换机（源边缘交换机）
                flow_in_port = src_port
            else:  # 中间交换机
                flow_in_port = next_in_port

            # 创建匹配规则
            if flow_type == 'arp':
                match = parser.OFPMatch(
                    in_port=flow_in_port,
                    eth_type=ether_types.ETH_TYPE_ARP,
                    arp_spa=src_ip,
                    arp_tpa=dst_ip
                )
            else:  # ipv4
                match = parser.OFPMatch(
                    in_port=flow_in_port,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=src_ip,
                    ipv4_dst=dst_ip
                )

            # 创建动作
            actions = [parser.OFPActionOutput(out_port)]

            # 安装流表
            self.add_flow(current_datapath, 1, match, actions)

        # 发送数据包
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        print(ev)
        switch = ev.switch.dp
        if switch.id not in self.switches:
            self.switches.append(switch.id)
            self.datapath_list[switch.id] = switch

    @set_ev_cls(event.EventSwitchLeave, MAIN_DISPATCHER)
    def switch_leave_handler(self, ev):
        print(ev)
        switch = ev.switch.dp.id
        if switch in self.switches:
            self.switches.remove(switch)
            del self.datapath_list[switch]
            del self.adjacency[switch]

    #get adjacency matrix of fattree
    @set_ev_cls(event.EventLinkAdd, MAIN_DISPATCHER)
    def link_add_handler(self, ev):
        s1 = ev.link.src
        s2 = ev.link.dst
        self.adjacency[s1.dpid][s2.dpid] = s1.port_no
        self.adjacency[s2.dpid][s1.dpid] = s2.port_no

    @set_ev_cls(event.EventLinkDelete, MAIN_DISPATCHER)
    def link_delete_handler(self, ev):
        s1 = ev.link.src
        s2 = ev.link.dst
        # Exception handling if switch already deleted
        try:
            del self.adjacency[s1.dpid][s2.dpid]
            del self.adjacency[s2.dpid][s1.dpid]
        except KeyError:
            pass
