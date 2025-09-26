#!/usr/bin/env python3
"""
修复嵌入维度不匹配问题的脚本
清理旧的向量数据库并重新创建
"""

import sys
import os
import shutil
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_chroma_db():
    """清理ChromaDB数据库"""
    
    print("🧹 清理ChromaDB数据库")
    print("=" * 60)
    
    # 可能的ChromaDB目录
    chroma_dirs = [
        "chroma_db",
        "./chroma_db", 
        "../chroma_db",
        "rag/chroma_db"
    ]
    
    cleaned_count = 0
    
    for chroma_dir in chroma_dirs:
        chroma_path = Path(chroma_dir)
        if chroma_path.exists():
            try:
                print(f"🗑  删除目录: {chroma_path.absolute()}")
                shutil.rmtree(chroma_path)
                cleaned_count += 1
                print(f" 成功删除: {chroma_path}")
            except Exception as e:
                print(f" 删除失败: {chroma_path} - {e}")
        else:
            print(f"  目录不存在: {chroma_path}")
    
    if cleaned_count > 0:
        print(f"\n 成功清理了 {cleaned_count} 个ChromaDB目录")
    else:
        print("\n 没有找到需要清理的ChromaDB目录")
    
    return cleaned_count > 0

def check_ollama_models():
    """检查Ollama模型"""
    
    print("\n 检查Ollama模型")
    print("=" * 60)
    
    try:
        import subprocess
        
        # 检查Ollama服务状态
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(" Ollama服务正常运行")
                print("\n 可用模型:")
                print(result.stdout)
                
                # 检查嵌入模型
                if 'qwen3-embedding' in result.stdout:
                    print(" 嵌入模型 qwen3-embedding 可用")
                else:
                    print("  嵌入模型 qwen3-embedding 不可用")
                    print(" 请运行: ollama pull qwen3-embedding:latest")
                
                return True
            else:
                print(" Ollama服务异常")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Ollama命令超时")
            return False
        except FileNotFoundError:
            print(" 未找到Ollama命令")
            print(" 请确保Ollama已正确安装")
            return False
            
    except Exception as e:
        print(f" 检查Ollama模型失败: {e}")
        return False

def test_embedding_function():
    """测试嵌入函数"""
    
    print("\n 测试嵌入函数")
    print("=" * 60)
    
    try:
        # 添加当前目录到路径
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from rag.vector_store import OllamaEmbeddingFunction
        
        # 创建嵌入函数
        embedding_func = OllamaEmbeddingFunction()
        print(f" 嵌入模型: {embedding_func.model_name}")
        print(f"🌐 服务地址: {embedding_func.base_url}")
        
        # 测试嵌入生成
        test_text = ["这是一个测试文本"]
        print(f" 测试文本: {test_text[0]}")
        
        embeddings = embedding_func(test_text)
        
        if embeddings and len(embeddings) > 0:
            dimension = len(embeddings[0])
            print(f" 嵌入生成成功")
            print(f"📏 嵌入维度: {dimension}")
            print(f" 嵌入向量前5个值: {embeddings[0][:5]}")
            return True
        else:
            print(" 嵌入生成失败：返回空结果")
            return False
            
    except Exception as e:
        print(f" 测试嵌入函数失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_store():
    """测试向量存储"""
    
    print("\n🗄  测试向量存储")
    print("=" * 60)
    
    try:
        from rag.vector_store import CodeVectorStore

        # 创建测试向量存储
        test_collection = "test_dimension_fix"
        vector_store = CodeVectorStore(collection_name=test_collection, persist_directory="test_chroma_db")
        
        print(f" 测试集合: {test_collection}")
        
        # 添加测试文档
        test_code = "public void testMethod() { System.out.println(\"test\"); }"
        test_metadata = {
            "type": "method",
            "class_name": "TestClass",
            "method_name": "testMethod"
        }
        
        doc_id = vector_store.add_code_snippet(test_code, test_metadata)
        
        if doc_id:
            print(f" 添加测试文档成功: {doc_id}")
            
            # 测试搜索
            results = vector_store.search_similar_code("test method", top_k=1)
            
            if results and len(results) > 0:
                print(f" 搜索测试成功，找到 {len(results)} 个结果")
                print(f" 第一个结果: {results[0]['content'][:50]}...")
                
                # 清理测试数据
                vector_store.clear_collection()
                print("🧹 清理测试数据完成")
                
                # 删除测试目录
                test_dir = Path("test_chroma_db")
                if test_dir.exists():
                    shutil.rmtree(test_dir)
                    print("🗑  删除测试目录完成")
                
                return True
            else:
                print(" 搜索测试失败：未找到结果")
                return False
        else:
            print(" 添加测试文档失败")
            return False
            
    except Exception as e:
        print(f" 测试向量存储失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    
    print(" 修复嵌入维度不匹配问题")
    print("=" * 80)
    print("这个脚本将清理旧的向量数据库并测试新的嵌入功能")
    print("=" * 80)
    
    # 步骤1：清理ChromaDB
    step1_success = clean_chroma_db()
    
    # 步骤2：检查Ollama模型
    step2_success = check_ollama_models()
    
    # 步骤3：测试嵌入函数
    step3_success = test_embedding_function()
    
    # 步骤4：测试向量存储
    step4_success = test_vector_store()
    
    # 总结
    print("\n" + "=" * 80)
    print(" 修复结果总结")
    print("=" * 80)
    
    steps = [
        ("清理ChromaDB数据库", step1_success),
        ("检查Ollama模型", step2_success),
        ("测试嵌入函数", step3_success),
        ("测试向量存储", step4_success),
    ]
    
    passed = 0
    for step_name, success in steps:
        status = " 成功" if success else " 失败"
        print(f"{step_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{len(steps)} 步骤成功")
    
    if passed == len(steps):
        print("\n 所有修复步骤都成功了！")
        print(" 现在可以重新运行测试生成命令:")
        print("   python main_test_generator.py --project ../pdfcompare --class com.example.pdfcompare.util.HashUtilityClass --method hashBytes --output ./test_fixed --fix-strategy compile-only --max-attempts 3 --force-reindex")
        return True
    else:
        print("\n  部分修复步骤失败")
        print(" 请检查上述错误信息并解决问题")
        
        if not step2_success:
            print("\n Ollama问题解决建议:")
            print("   1. 启动Ollama服务: ollama serve")
            print("   2. 拉取嵌入模型: ollama pull qwen3-embedding:latest")
            print("   3. 检查模型列表: ollama list")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
