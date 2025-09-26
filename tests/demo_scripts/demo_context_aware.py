#!/usr/bin/env python3
"""
Context-Aware Code Generation 演示脚本
展示新的上下文感知模式的使用方法和效果
"""

import subprocess
import time
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f" {description}")
    print(f"{'='*60}")
    print(f" 命令: {cmd}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        print(f"\n⏱  执行时间: {duration:.2f} 秒")
        print(f" 返回码: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(" 命令执行超时 (120秒)")
        return False
    except Exception as e:
        print(f" 命令执行失败: {e}")
        return False

def demo_context_aware_mode():
    """演示Context-Aware模式"""
    cmd = """python main_test_generator.py \
  --project ../pdfcompare \
  --class com.example.pdfcompare.util.HashUtilityClass \
  --method hashBytes \
  --generation-mode context-aware \
  --output ./demo_context_aware \
  --max-attempts 3"""
    
    return run_command(cmd, "Context-Aware模式演示")

def demo_hybrid_mode():
    """演示混合模式"""
    cmd = """python main_test_generator.py \
  --project ../pdfcompare \
  --class com.example.pdfcompare.util.ImageComparator \
  --method compareImages \
  --generation-mode hybrid \
  --output ./demo_hybrid \
  --max-attempts 3"""
    
    return run_command(cmd, "混合模式演示")

def demo_rag_mode():
    """演示RAG模式（快速版本）"""
    cmd = """python main_test_generator.py \
  --project ../pdfcompare \
  --class com.example.pdfcompare.util.HashUtilityClass \
  --method hashBytes \
  --generation-mode rag \
  --output ./demo_rag \
  --max-attempts 1"""
    
    return run_command(cmd, "RAG模式演示（快速版本）")

def show_generated_files():
    """显示生成的文件"""
    print(f"\n{'='*60}")
    print(" 生成的测试文件")
    print(f"{'='*60}")
    
    test_dirs = [
        "./demo_context_aware",
        "./demo_hybrid", 
        "./demo_rag"
    ]
    
    for test_dir in test_dirs:
        path = Path(test_dir)
        if path.exists():
            print(f"\n {test_dir}:")
            java_files = list(path.glob("*.java"))
            if java_files:
                for java_file in java_files:
                    print(f"    {java_file.name}")
                    # 显示文件的前几行
                    try:
                        content = java_file.read_text(encoding='utf-8')
                        lines = content.split('\n')[:10]
                        for i, line in enumerate(lines, 1):
                            print(f"   {i:2d}: {line}")
                        if len(content.split('\n')) > 10:
                            print(f"   ... 还有 {len(content.split('\n')) - 10} 行")
                    except Exception as e:
                        print(f"    读取文件失败: {e}")
            else:
                print("    没有找到Java文件")
        else:
            print(f"\n {test_dir}:  目录不存在")

def compare_modes():
    """对比不同模式的效果"""
    print(f"\n{'='*60}")
    print(" 模式对比总结")
    print(f"{'='*60}")
    
    print("""
 Context-Aware模式:
    优点: 速度极快 (0.1-0.5秒), 包路径100%准确, 依赖分析完整
    缺点: 目前生成模板代码, 需要LLM集成来生成具体实现
    适用: 标准Java项目, 需要快速生成测试框架

 混合模式 (推荐):
    优点: 结合两种模式优势, 最高成功率, 智能回退
    缺点: 稍微复杂一些
    适用: 生产环境, 复杂项目, 需要最高成功率

 RAG模式:
    优点: 深度上下文理解, 复杂业务逻辑处理
    缺点: 速度慢 (60-80秒), 包路径可能错误, 不稳定
    适用: 复杂上下文, 特殊项目结构

 性能对比:
   模式           速度        准确率      稳定性      推荐度
   Context-Aware  ⭐⭐⭐⭐⭐    ⭐⭐⭐⭐⭐     ⭐⭐⭐⭐⭐     ⭐⭐⭐⭐
   混合模式        ⭐⭐⭐⭐     ⭐⭐⭐⭐⭐     ⭐⭐⭐⭐⭐     ⭐⭐⭐⭐⭐
   RAG模式        ⭐⭐        ⭐⭐⭐       ⭐⭐⭐       ⭐⭐
    """)

def main():
    """主演示函数"""
    print(" Context-Aware Code Generation 演示")
    print("=" * 80)
    print("""
这个演示将展示LLM4TestGen的三种生成模式:
1. Context-Aware模式 - 新的上下文感知模式
2. 混合模式 - Context-Aware + RAG回退 (推荐)
3. RAG模式 - 传统的向量检索模式

每种模式都会生成测试代码，您可以对比它们的效果。
    """)
    
    input("按Enter键开始演示...")
    
    results = {}
    
    # 1. Context-Aware模式演示
    results['context_aware'] = demo_context_aware_mode()
    
    # 2. 混合模式演示
    results['hybrid'] = demo_hybrid_mode()
    
    # 3. RAG模式演示（快速版本）
    print("\n  注意: RAG模式通常需要60-80秒，这里使用快速版本演示")
    choice = input("是否运行RAG模式演示? (y/N): ").lower().strip()
    if choice == 'y':
        results['rag'] = demo_rag_mode()
    else:
        results['rag'] = None
        print("  跳过RAG模式演示")
    
    # 显示生成的文件
    show_generated_files()
    
    # 对比总结
    compare_modes()
    
    # 最终总结
    print(f"\n{'='*80}")
    print(" 演示完成总结")
    print(f"{'='*80}")
    
    success_count = sum(1 for result in results.values() if result is True)
    total_count = sum(1 for result in results.values() if result is not None)
    
    print(f" 成功率: {success_count}/{total_count}")
    
    for mode, result in results.items():
        if result is True:
            print(f"    {mode}: 成功")
        elif result is False:
            print(f"    {mode}: 失败")
        else:
            print(f"     {mode}: 跳过")
    
    print(f"\n 推荐使用混合模式获得最佳效果:")
    print(f"   python main_test_generator.py --generation-mode hybrid")
    
    print(f"\n📚 更多信息请查看:")
    print(f"   docs/context_aware_guide.md")
    print(f"   examples/context_aware_usage.py")

if __name__ == "__main__":
    main()
