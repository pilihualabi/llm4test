#!/usr/bin/env python3
"""
基础使用示例
演示LLM4TestGen的基本功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def example_single_method():
    """示例1: 为单个方法生成测试"""
    print("示例1: 单个方法测试生成")
    print("=" * 50)
    
    from enhanced_test_generator import EnhancedTestGenerator
    
    # 假设项目路径
    project_path = Path("./sample-java-project")
    
    # 初始化生成器
    generator = EnhancedTestGenerator(
        project_path=project_path,
        output_dir=Path("./generated_tests")
    )
    
    # 生成测试（启用RAG）
    result = generator.generate_test_for_method(
        class_name="com.example.Calculator",
        method_name="add",
        use_rag=True
    )
    
    if result['success']:
        print(f" 测试生成成功!")
        print(f" 文件: {result['test_file_path']}")
        print(f" 使用上下文: {result['context_used']} 个")
        print(f" 代码长度: {len(result['generated_test'])} 字符")
    else:
        print(f" 生成失败: {result.get('error', 'Unknown error')}")
    
    return result['success']

def example_batch_generation():
    """示例2: 批量生成测试"""
    print("\n示例2: 批量测试生成")
    print("=" * 50)
    
    from enhanced_test_generator import EnhancedTestGenerator
    
    project_path = Path("./sample-java-project")
    generator = EnhancedTestGenerator(project_path)
    
    # 分析项目并生成所有测试
    summary = generator.analyze_and_generate_all(force_reindex=True)
    
    print(f" 项目分析结果:")
    stats = summary['project_analysis']['stats']
    print(f"   文件数: {stats['total_files']}")
    print(f"   类数: {stats['total_classes']}")
    print(f"   方法数: {stats['total_methods']}")
    
    print(f"\n 生成结果:")
    gen_stats = summary['statistics']
    print(f"   成功生成: {gen_stats['generated_tests']}")
    print(f"   生成失败: {gen_stats['failed_generations']}")
    print(f"   成功率: {summary['success_rate']:.1%}")
    
    return summary['success_rate'] > 0.5

def example_rag_context():
    """示例3: RAG上下文检索"""
    print("\n示例3: RAG上下文检索")
    print("=" * 50)
    
    from rag.project_analyzer import SmartProjectAnalyzer
    
    project_path = Path("./sample-java-project")
    analyzer = SmartProjectAnalyzer(project_path)
    
    # 分析项目
    analysis = analyzer.analyze_project()
    print(f"📚 项目索引完成: {analysis['stats']['total_methods']} 个方法")
    
    # 查找相关上下文
    context_results = analyzer.find_relevant_context(
        target_method="com.example.Calculator#divide",
        query_description="mathematical division with error handling",
        top_k=5
    )
    
    print(f"\n 找到 {len(context_results)} 个相关上下文:")
    for i, context in enumerate(context_results[:3], 1):
        metadata = context['metadata']
        method_name = metadata.get('method_name', 'unknown')
        class_name = metadata.get('class_name', 'unknown')
        similarity = 1 - context.get('distance', 1.0)
        
        print(f"   {i}. {class_name}.{method_name}")
        print(f"      相似度: {similarity:.3f}")
        print(f"      代码片段: {context['code'][:60]}...")
    
    return len(context_results) > 0

def example_custom_config():
    """示例4: 自定义配置"""
    print("\n示例4: 自定义配置")
    print("=" * 50)
    
    import os
    from config.remote_ollama_config import remote_config
    
    # 显示当前配置
    print(" 当前Ollama配置:")
    print(f"   服务器: {remote_config.get_base_url()}")
    print(f"   代码模型: {remote_config.get_code_model()}")
    print(f"   嵌入模型: {remote_config.get_embedding_model()}")
    print(f"   修复模型: {remote_config.get_fix_model()}")
    
    # 自定义配置示例
    print("\n 自定义配置示例:")
    
    # 方式1: 环境变量
    print("   方式1 - 环境变量:")
    print("   export OLLAMA_BASE_URL='http://remote-server:11434'")
    print("   export OLLAMA_CODE_MODEL='custom-model'")
    
    # 方式2: 代码设置
    print("   方式2 - 代码设置:")
    print("   remote_config.set_remote_config(...)")
    
    return True

def example_error_handling():
    """示例5: 错误处理"""
    print("\n示例5: 错误处理和重试")
    print("=" * 50)
    
    from enhanced_test_generator import EnhancedTestGenerator
    import time
    
    def generate_with_retry(generator, class_name, method_name, max_retries=3):
        """带重试的生成函数"""
        for attempt in range(max_retries):
            try:
                print(f"   尝试 {attempt + 1}/{max_retries}...")
                
                result = generator.generate_test_for_method(
                    class_name=class_name,
                    method_name=method_name,
                    use_rag=True
                )
                
                if result['success']:
                    print(f"    第 {attempt + 1} 次尝试成功!")
                    return result
                else:
                    print(f"    第 {attempt + 1} 次尝试失败: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"   💥 第 {attempt + 1} 次尝试异常: {e}")
            
            # 指数退避
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"   ⏱ 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    # 模拟使用
    project_path = Path("./sample-java-project")
    generator = EnhancedTestGenerator(project_path)
    
    result = generate_with_retry(
        generator,
        "com.example.Calculator", 
        "divide"
    )
    
    success = result['success']
    print(f"\n 最终结果: {'成功' if success else '失败'}")
    
    return success

def example_performance_monitoring():
    """示例6: 性能监控"""
    print("\n示例6: 性能监控")
    print("=" * 50)
    
    import time
    from enhanced_test_generator import EnhancedTestGenerator
    
    project_path = Path("./sample-java-project")
    generator = EnhancedTestGenerator(project_path)
    
    # 监控单个方法生成
    start_time = time.time()
    
    result = generator.generate_test_for_method(
        "com.example.Calculator",
        "multiply",
        use_rag=True
    )
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    print(f"⏱ 生成耗时: {generation_time:.2f} 秒")
    
    if result['success']:
        print(f" 性能指标:")
        print(f"   代码长度: {len(result['generated_test'])} 字符")
        print(f"   上下文数量: {result['context_used']} 个")
        print(f"   平均生成速度: {len(result['generated_test']) / generation_time:.0f} 字符/秒")
    
    # 获取统计信息
    stats = generator.get_statistics()
    print(f"\n 系统统计:")
    gen_stats = stats['generator_stats']
    for key, value in gen_stats.items():
        print(f"   {key}: {value}")
    
    return True

def main():
    """主函数 - 运行所有示例"""
    print(" LLM4TestGen 基础使用示例")
    print("=" * 60)
    
    examples = [
        ("单个方法生成", example_single_method),
        ("批量生成", example_batch_generation),
        ("RAG上下文检索", example_rag_context),
        ("自定义配置", example_custom_config),
        ("错误处理", example_error_handling),
        ("性能监控", example_performance_monitoring),
    ]
    
    results = []
    
    for name, func in examples:
        try:
            print(f"\n 运行示例: {name}")
            success = func()
            results.append((name, success))
            
            if success:
                print(f" {name} 示例完成")
            else:
                print(f" {name} 示例部分成功")
                
        except Exception as e:
            print(f" {name} 示例异常: {e}")
            results.append((name, False))
    
    # 总结
    print(f"\n{'=' * 60}")
    print(" 示例运行总结:")
    print("=" * 60)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "" if success else ""
        print(f"   {status} {name}")
    
    print(f"\n 成功率: {successful}/{total} ({successful/total:.1%})")
    
    if successful >= total * 0.7:
        print(" 大部分示例运行成功！系统基本正常。")
    else:
        print(" 部分示例失败，请检查环境配置。")
    
    print(f"\n 提示:")
    print("   1. 确保Ollama服务正在运行")
    print("   2. 确保Java项目路径正确")
    print("   3. 查看详细日志进行调试")

if __name__ == "__main__":
    main()
