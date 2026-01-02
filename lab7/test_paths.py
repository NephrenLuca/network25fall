#!/usr/bin/env python3

"""
测试路径计算的正确性
"""

class PathTester:
    def __init__(self):
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

    def get_lpr_path(self, src_dpid, dst_dpid):
        """获取Left Path Routing路径（最左边的路径）"""
        paths = self.get_all_paths(src_dpid, dst_dpid)
        if not paths:
            return None

        # 选择最左边的路径（按照交换机ID排序，选择最小的）
        return min(paths, key=lambda x: tuple(x))

    def test_paths(self):
        """测试几个关键路径"""
        test_cases = [
            (1, 2),  # 同一边缘交换机下的不同主机
            (1, 3),  # 不同边缘交换机
            (1, 5),  # 更远的边缘交换机
            (1, 8),  # 最远的边缘交换机
        ]

        print("测试路径计算:")
        for src, dst in test_cases:
            paths = self.get_all_paths(src, dst)
            lpr_path = self.get_lpr_path(src, dst)
            print(f"从交换机 {src} 到 {dst}:")
            print(f"  所有路径: {paths}")
            print(f"  LPR路径: {lpr_path}")
            print()


if __name__ == "__main__":
    tester = PathTester()
    tester.test_paths()
