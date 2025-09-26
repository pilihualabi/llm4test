#!/usr/bin/env python3
"""
Java专项快速开始脚本
快速验证Java解析和RAG基础功能
"""

import subprocess
import sys
from pathlib import Path

def check_requirements():
    """检查基本要求"""
    print(" 检查基本要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("    需要Python 3.7或更高版本")
        return False
    else:
        print(f"    Python版本: {sys.version.split()[0]}")
    
    # 检查Java
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("    Java已安装")
        else:
            print("    Java未安装或不可用")
            return False
    except FileNotFoundError:
        print("    Java未安装")
        return False
    
    # 检查Ollama（可选）
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print("    Ollama正在运行")
        else:
            print("    Ollama未响应")
    except:
        print("    Ollama未运行（稍后可启动）")
    
    return True

def install_dependencies():
    """安装依赖"""
    print(" 安装Python依赖...")
    
    try:
        # 只安装核心依赖
        core_deps = [
            "javalang>=0.13.0",
            "requests>=2.31.0", 
            "pydantic>=2.0.0"
        ]
        
        for dep in core_deps:
            print(f"   → 安装 {dep}")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"    安装失败: {dep}")
                return False
        
        print("    核心依赖安装完成")
        return True
        
    except Exception as e:
        print(f"    安装异常: {e}")
        return False

def test_basic_java_parsing():
    """测试基础Java解析"""
    print("☕ 测试Java解析功能...")
    
    # 创建简单的Java类
    java_code = '''
package com.example;

public class SimpleCalculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
}
'''
    
    try:
        # 使用javalang直接解析（不依赖新的解析器）
        import javalang
        
        tree = javalang.parse.parse(java_code)
        
        # 提取类信息
        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            print(f"    成功解析类: {class_node.name}")
            print(f"    方法数量: {len(class_node.methods)}")
            
            for method in class_node.methods:
                print(f"      - {method.name}")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"    解析失败: {e}")
        return False

def test_ollama_connection():
    """测试Ollama连接"""
    print("🤖 测试Ollama连接...")
    
    try:
        import requests
        
        # 测试基本连接
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("    Ollama未运行，请启动: ollama serve")
            return False
        
        # 检查嵌入模型
        models = response.json().get('models', [])
        embed_model_available = any('nomic-embed-text' in model.get('name', '') for model in models)
        
        if embed_model_available:
            print("    nomic-embed-text模型可用")
        else:
            print("    请下载嵌入模型: ollama pull nomic-embed-text")
        
        # 测试嵌入功能
        if embed_model_available:
            embed_request = {
                "model": "nomic-embed-text", 
                "prompt": "public int add(int a, int b) { return a + b; }"
            }
            
            embed_response = requests.post(
                "http://localhost:11434/api/embeddings",
                json=embed_request,
                timeout=10
            )
            
            if embed_response.status_code == 200:
                embed_data = embed_response.json()
                if 'embedding' in embed_data:
                    print(f"    嵌入向量生成成功: {len(embed_data['embedding'])} 维")
                    return True
        
        return False
        
    except Exception as e:
        print(f"    Ollama测试失败: {e}")
        return False

def main():
    """主函数"""
    print(" Java专项快速开始检查...\n")
    
    # 检查步骤
    steps = [
        ("基本要求检查", check_requirements),
        ("安装核心依赖", install_dependencies), 
        ("Java解析测试", test_basic_java_parsing),
        ("Ollama连接测试", test_ollama_connection),
    ]
    
    passed = 0
    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"步骤: {step_name}")
        print('='*50)
        
        try:
            if step_func():
                print(f" {step_name} 完成")
                passed += 1
            else:
                print(f" {step_name} 失败")
                
                # Ollama测试失败不算致命错误
                if "Ollama" not in step_name:
                    break
        except Exception as e:
            print(f"💥 {step_name} 异常: {e}")
            if "Ollama" not in step_name:
                break
    
    print(f"\n{'='*50}")
    print("总结")
    print('='*50)
    
    if passed >= 3:  # 允许Ollama失败
        print(" Java基础环境检查通过！")
        print("\n 下一步:")
        print("1. 如果Ollama未运行，请启动: ollama serve")
        print("2. 下载嵌入模型: ollama pull nomic-embed-text")
        print("3. 运行完整测试: python test_java_only.py")
        print("4. 一切就绪后，我们开始RAG系统开发")
        return True
    else:
        print(" 基础环境检查失败，请解决上述问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
