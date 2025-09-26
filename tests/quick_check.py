#!/usr/bin/env python3
"""
快速环境检查脚本
检查Java开发环境和Ollama连接
"""

import sys
import subprocess
from pathlib import Path

def check_python_packages():
    """检查Python包"""
    print(" 检查Python包...")
    
    required_packages = [
        'javalang',
        'requests', 
        'pydantic'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"    {package}")
        except ImportError:
            print(f"    {package}")
            missing.append(package)
    
    if missing:
        print(f"\n 安装缺失的包:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def check_java():
    """检查Java环境"""
    print("\n☕ 检查Java环境...")
    
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Java输出通常在stderr
            version_info = result.stderr.split('\n')[0]
            print(f"    {version_info}")
            return True
        else:
            print(f"    Java未安装或不可用")
            return False
    except FileNotFoundError:
        print(f"    Java未安装")
        return False

def check_ollama():
    """检查Ollama连接"""
    print("\n🤖 检查Ollama连接...")
    
    try:
        import requests
        import os
        
        # 检查环境变量
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"    Ollama连接成功 ({base_url})")
            print(f"    可用模型: {len(models)} 个")
            return True
        else:
            print(f"    Ollama响应错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    Ollama连接失败: {e}")
        print(f"    请确保:")
        print(f"      1. Ollama正在运行")
        print(f"      2. 配置环境变量: source *_env.sh")
        return False

def check_project_files():
    """检查项目文件"""
    print("\n 检查项目文件...")
    
    key_files = [
        'source_analysis/dependency_extractor.py',
        'source_analysis/test_scaffold.py',
        'config/remote_ollama_config.py'
    ]
    
    all_exist = True
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"    {file_path}")
        else:
            print(f"    {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """主检查函数"""
    print(" 快速环境检查")
    print("="*40)
    
    checks = [
        ("Python包", check_python_packages),
        ("Java环境", check_java),
        ("项目文件", check_project_files),
        ("Ollama连接", check_ollama),
    ]
    
    passed = 0
    for check_name, check_func in checks:
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"   💥 {check_name} 检查异常: {e}")
    
    print(f"\n{'='*40}")
    print(f"检查结果: {passed}/{len(checks)} 通过")
    
    if passed >= 3:  # 允许Ollama检查失败
        print(" 环境基本正常")
        print("\n 建议:")
        print("1. python test_java_simple.py  # 运行简化测试")
        print("2. 如果Ollama未连接，请配置: python setup_remote_optimized.py")
        return True
    else:
        print(" 环境有问题，请解决后继续")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
