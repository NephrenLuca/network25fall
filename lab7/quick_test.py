#!/usr/bin/env python3
"""
快速环境检查和测试脚本
用于验证实验环境配置是否正确
"""

import subprocess
import sys
import time

def run_command(cmd, description):
    """运行命令并返回结果"""
    print(f"\n🔍 检查: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {description} - 正常")
            return True, result.stdout.strip()
        else:
            print(f"❌ {description} - 失败")
            print(f"   错误信息: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"❌ {description} - 异常: {str(e)}")
        return False, str(e)

def check_environment():
    """检查实验环境"""
    print("🚀 Lab 7 实验环境检查")
    print("=" * 50)

    # 检查可能的ryu路径
    ryu_paths = [
        "ryu-manager --version",
        "~/miniconda3/envs/myenv3_8/bin/ryu-manager --version",
        "/home/ling/miniconda3/envs/myenv3_8/bin/ryu-manager --version"
    ]

    ryu_check = False
    for ryu_cmd in ryu_paths:
        success, output = run_command(ryu_cmd, "Ryu Controller 版本")
        if success:
            ryu_check = True
            break

    if not ryu_check:
        print("❌ Ryu Controller - 未找到")
        print("   提示: 请激活正确的conda环境: conda activate myenv3_8")

    checks = [
        ("python --version", "Python 版本 (应为 3.8)"),
        ("mn --version", "Mininet 版本"),
    ]

    all_passed = True
    for cmd, desc in checks:
        success, output = run_command(cmd, desc)
        if not success:
            all_passed = False

    return all_passed

def check_code_syntax():
    """检查代码语法"""
    print("\n📝 代码语法检查")
    print("=" * 30)

    files_to_check = ["LPR.py", "RSR.py", "LLR.py"]
    all_passed = True

    for filename in files_to_check:
        success, output = run_command(f"python -m py_compile {filename}", f"{filename} 语法")
        if not success:
            all_passed = False

    return all_passed

def test_path_calculation():
    """测试路径计算"""
    print("\n🛣️  路径计算测试")
    print("=" * 25)

    success, output = run_command("python test_paths.py", "路径计算功能")
    if success:
        print("路径计算结果:")
        print(output)
    return success

def quick_integration_test():
    """快速集成测试"""
    print("\n🔗 快速集成测试")
    print("=" * 30)
    print("注意: 此测试需要手动验证输出")

    print("\n步骤 1: 启动 Ryu 控制器 (在新终端中运行)")
    print("ryu-manager LPR.py --observe-links --verbose")

    print("\n步骤 2: 等待控制器启动，然后在新终端中运行 Mininet")
    print("sudo python parallel_traffic_generator.py")

    print("\n预期输出:")
    print("- Ryu终端: 'switch_features_handler is called'")
    print("- Ryu终端: 'LPR Path for 10.0.0.X -> 10.0.0.Y: [path]'")
    print("- Mininet终端: 成功创建拓扑并运行iperf测试")

def show_usage_guide():
    """显示使用指南"""
    print("\n📋 使用指南")
    print("=" * 20)
    print("1. 环境检查通过后，按照 TEST_GUIDE.md 进行详细测试")
    print("2. LPR/RSR 使用 parallel_traffic_generator.py")
    print("3. LLR 使用 sequential_traffic_generator.py")
    print("4. 详细测试步骤请参考 TEST_GUIDE.md")

def main():
    """主函数"""
    print("Lab 7: 网络层控制平面流表下发 - 环境检查工具")
    print("时间:", time.strftime("%Y-%m-%d %H:%M:%S"))

    # 环境检查
    env_ok = check_environment()

    # 代码检查
    code_ok = check_code_syntax()

    # 路径计算测试
    path_ok = test_path_calculation()

    # 总结
    print("\n📊 检查总结")
    print("=" * 20)
    print(f"环境检查: {'✅ 通过' if env_ok else '❌ 失败'}")
    print(f"代码检查: {'✅ 通过' if code_ok else '❌ 失败'}")
    print(f"路径测试: {'✅ 通过' if path_ok else '❌ 失败'}")

    if env_ok and code_ok and path_ok:
        print("\n🎉 所有检查通过！可以开始实验测试")
        quick_integration_test()
    else:
        print("\n⚠️  发现问题，请根据上述错误信息修复后重试")

    show_usage_guide()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
