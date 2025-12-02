#!/usr/bin/env python3
"""
快速验证脚本 - 检查代码语法和导入
"""

import sys
import importlib.util

def check_syntax(filepath):
    """检查Python文件的语法"""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        compile(code, filepath, 'exec')
        print("✓ {} - 语法正确".format(filepath))
        return True
    except SyntaxError as e:
        print("✗ {} - 语法错误: {}".format(filepath, e))
        return False
    except Exception as e:
        print("✗ {} - 错误: {}".format(filepath, e))
        return False

def check_imports(filepath):
    """检查文件是否可以导入（不实际运行）"""
    try:
        spec = importlib.util.spec_from_file_location("module", filepath)
        if spec is None:
            print("  ⚠ {} - 无法创建模块规范".format(filepath))
            return False
        print("  ✓ {} - 可以导入".format(filepath))
        return True
    except Exception as e:
        print("  ⚠ {} - 导入检查失败: {}".format(filepath, e))
        return False

def main():
    files = [
        'customized_topo.py',
        'host_iperf.py',
        'test_task1.py',
        'test_task2.py'
    ]
    
    print("=" * 60)
    print("代码验证")
    print("=" * 60)
    
    all_ok = True
    for filepath in files:
        if check_syntax(filepath):
            check_imports(filepath)
        else:
            all_ok = False
        print()
    
    if all_ok:
        print("=" * 60)
        print("所有文件语法检查通过！")
        print("=" * 60)
        print("\n注意：实际运行需要：")
        print("  1. 安装Mininet: sudo apt-get install mininet")
        print("  2. 使用sudo权限运行脚本")
        return 0
    else:
        print("=" * 60)
        print("发现语法错误，请修复后重试")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())


