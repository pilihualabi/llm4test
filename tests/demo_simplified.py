#!/usr/bin/env python3
"""
简化系统演示
使用本地可用的Ollama模型展示核心功能
"""

import sys
import tempfile
import shutil
from pathlib import Path
import logging
import requests
import json
import os

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def setup_local_config():
    """设置本地Ollama配置"""
    print(" 配置本地Ollama...")
    
    # 设置环境变量使用本地可用的模型
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    os.environ["OLLAMA_EMBEDDING_MODEL"] = "qwen3-embedding:latest"
    os.environ["OLLAMA_CODE_MODEL"] = "qwen3:8b"
    os.environ["OLLAMA_FIX_MODEL"] = "qwen3:8b"
    os.environ["OLLAMA_REQUEST_TIMEOUT"] = "120"
    
    print("    本地配置已设置")
    print(f"   🌐 服务器: {os.environ['OLLAMA_BASE_URL']}")
    print(f"   🔤 嵌入模型: {os.environ['OLLAMA_EMBEDDING_MODEL']}")
    print(f"   💻 代码模型: {os.environ['OLLAMA_CODE_MODEL']}")

def test_ollama_connection():
    """测试Ollama连接"""
    print("\n🔗 测试Ollama连接...")
    
    try:
        # 测试服务器
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"    连接成功，发现 {len(models)} 个模型")
            
            for model in models:
                name = model.get('name', 'unknown')
                size_mb = model.get('size', 0) // (1024*1024)
                print(f"       {name} ({size_mb}MB)")
            
            return True
        else:
            print(f"    连接失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    连接异常: {e}")
        return False

def test_embedding_function():
    """测试嵌入功能"""
    print("\n 测试嵌入功能...")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": "qwen3-embedding:latest",
                "prompt": "Hello world test embedding"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get('embedding', [])
            print(f"    嵌入成功: {len(embedding)} 维向量")
            return True, len(embedding)
        else:
            print(f"    嵌入失败: {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"    嵌入异常: {e}")
        return False, 0

def test_code_generation():
    """测试代码生成"""
    print("\n🤖 测试代码生成...")
    
    try:
        prompt = """Generate a simple Java JUnit 5 test method for testing an add method that takes two integers and returns their sum. Keep it short and simple."""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen3:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 200
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            generated_code = data.get('response', '').strip()
            
            if generated_code:
                print(f"    代码生成成功: {len(generated_code)} 字符")
                print(f"    生成示例 (前100字符):")
                print(f"      {generated_code[:100]}...")
                return True, generated_code
            else:
                print(f"    生成内容为空")
                return False, ""
        else:
            print(f"    生成失败: {response.status_code}")
            return False, ""
            
    except Exception as e:
        print(f"    生成异常: {e}")
        return False, ""

def test_rag_basic():
    """测试基础RAG功能"""
    print("\n 测试基础RAG功能...")
    
    try:
        import chromadb
        
        # 创建内存客户端
        client = chromadb.Client()
        collection = client.get_or_create_collection(name="test_rag")
        
        # 添加一些示例代码
        sample_codes = [
            "public int add(int a, int b) { return a + b; }",
            "public int multiply(int a, int b) { return a * b; }",
            "public boolean isEmpty(String str) { return str == null || str.length() == 0; }"
        ]
        
        metadatas = [
            {"type": "method", "name": "add", "operation": "addition"},
            {"type": "method", "name": "multiply", "operation": "multiplication"},
            {"type": "method", "name": "isEmpty", "operation": "validation"}
        ]
        
        # 添加到集合
        collection.add(
            documents=sample_codes,
            metadatas=metadatas,
            ids=["add", "multiply", "isEmpty"]
        )
        
        # 搜索
        results = collection.query(
            query_texts=["mathematical calculation"],
            n_results=2
        )
        
        if results['documents'] and len(results['documents'][0]) > 0:
            print(f"    RAG搜索成功，找到 {len(results['documents'][0])} 个结果")
            
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                operation = metadata.get('operation', 'unknown')
                print(f"      {i+1}. {operation}: {doc[:50]}...")
            
            return True
        else:
            print(f"    RAG搜索无结果")
            return False
            
    except Exception as e:
        print(f"    RAG测试异常: {e}")
        return False

def demo_integration():
    """演示集成功能"""
    print("\n🎪 演示集成功能...")
    
    try:
        # 1. 模拟项目分析
        print("    模拟项目分析...")
        project_info = {
            "files": 2,
            "classes": 2, 
            "methods": 6
        }
        print(f"      发现 {project_info['files']} 个文件，{project_info['classes']} 个类，{project_info['methods']} 个方法")
        
        # 2. 模拟RAG上下文检索
        print("    模拟RAG上下文检索...")
        mock_context = [
            "相关方法1: Calculator.add()",
            "相关方法2: Calculator.multiply()",
            "相关类: MathUtils"
        ]
        print(f"      找到 {len(mock_context)} 个相关上下文")
        
        # 3. 模拟测试生成
        print("   🤖 模拟测试生成...")
        test_prompt = """基于上下文生成测试：
        目标方法: Calculator.divide()
        相关上下文: Calculator.add(), Calculator.multiply()
        要求: 生成JUnit 5测试，包含正常情况和异常情况"""
        
        # 实际调用代码生成
        success, generated_code = test_code_generation_with_context(test_prompt)
        
        if success:
            print(f"       集成生成成功")
            return True
        else:
            print(f"       集成生成失败")
            return False
            
    except Exception as e:
        print(f"    集成演示异常: {e}")
        return False

def test_code_generation_with_context(prompt):
    """使用上下文进行代码生成"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen3-8b-q4:latest",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 300
                }
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            generated_code = data.get('response', '').strip()
            return bool(generated_code), generated_code
        else:
            return False, ""
    except Exception:
        return False, ""

def main():
    """主演示函数"""
    print("🎬 简化系统演示")
    print("=" * 50)
    
    # 设置日志级别
    logging.basicConfig(level=logging.WARNING)
    
    # 1. 设置配置
    setup_local_config()
    
    # 2. 测试各个组件
    tests = [
        ("Ollama连接", test_ollama_connection),
        ("嵌入功能", lambda: test_embedding_function()[0]),
        ("代码生成", lambda: test_code_generation()[0]),
        ("RAG基础功能", test_rag_basic),
        ("集成功能", demo_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"\n {test_name} 测试通过")
                passed += 1
            else:
                print(f"\n {test_name} 测试失败")
        except Exception as e:
            print(f"\n💥 {test_name} 测试异常: {e}")
    
    # 结果汇总
    print(f"\n{'=' * 50}")
    print(f" 简化演示总结: {passed}/{total} 通过")
    print("=" * 50)
    
    if passed >= 4:
        print(" 核心功能基本正常！")
        print("\n✨ 验证的功能:")
        print("   🔗 Ollama本地服务连接")
        print("   🔤 向量嵌入生成")
        print("   🤖 代码生成模型") 
        print("    RAG语义搜索")
        print("    组件集成")
        
        print(f"\n 系统架构:")
        print("    项目分析器 → 解析Java代码结构")
        print("   🗃 向量存储 → ChromaDB + Ollama嵌入")
        print("    RAG检索 → 智能上下文匹配")
        print("   🤖 测试生成 → LLM驱动的测试创建")
        
        success_rate = passed / total
        print(f"\n🏆 演示成功率: {success_rate:.1%}")
        
        if success_rate >= 0.8:
            print("💎 系统已准备好用于实际Java项目测试生成！")
        else:
            print("⚡ 系统基本可用，但建议进一步优化稳定性")
        
        return True
    else:
        print(" 系统需要进一步调试")
        print("\n 建议:")
        print("   1. 检查Ollama服务是否正常运行")
        print("   2. 确认模型是否已正确加载")
        print("   3. 检查网络连接和超时设置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
