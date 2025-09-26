#!/usr/bin/env python3
"""
改进版使用示例
演示如何使用最新的ImprovedTestGenerator
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from improved_test_generator import ImprovedTestGenerator

def basic_example():
    """基础使用示例"""
    print(" LLM4TestGen 改进版基础示例")
    print("=" * 50)
    
    # 项目路径（请修改为你的Java项目路径）
    project_path = Path("../pdfcompare")  # 示例项目
    output_dir = Path("./improved_test_output")
    
    if not project_path.exists():
        print(f" 项目路径不存在: {project_path}")
        print(" 请修改 project_path 为你的Java项目路径")
        return
    
    try:
        # 1. 创建测试生成器
        print(" 步骤1: 初始化测试生成器")
        generator = ImprovedTestGenerator(
            project_path=project_path,
            output_dir=output_dir,
            debug=False  # 设置为True查看详细调试信息
        )
        
        # 2. 生成单个方法的测试
        print(" 步骤2: 生成测试代码")
        result = generator.generate_test_for_method(
            class_name="com.example.pdfcompare.util.HashUtilityClass",
            method_name="hashBytes",
            use_rag=True,  # 启用RAG上下文检索
            test_style="comprehensive",  # 全面测试风格
            max_fix_attempts=2
        )
        
        # 3. 检查结果
        print(" 步骤3: 检查生成结果")
        if result['success']:
            print(f" 测试生成成功！")
            print(f" 测试文件: {result.get('test_file_path')}")
            print(f"⏱  耗时: {result.get('total_duration', 0):.2f} 秒")
            print(f" 使用上下文: {result.get('context_used', 0)} 个")
            print(f" 方法签名: {result.get('method_signature')}")
            
            # 显示生成的测试代码片段
            test_file = result.get('test_file_path')
            if test_file and Path(test_file).exists():
                content = Path(test_file).read_text(encoding='utf-8')
                lines = content.split('\n')
                print(f"\n 生成的测试代码预览:")
                print("```java")
                for i, line in enumerate(lines[:15], 1):  # 显示前15行
                    print(f"{i:2d}: {line}")
                if len(lines) > 15:
                    print(f"... 还有 {len(lines) - 15} 行")
                print("```")
        else:
            print(f" 测试生成失败: {result.get('error')}")
            print(f" 编译尝试: {result.get('attempts', 'N/A')} 次")
        
        # 4. 查看统计信息
        stats = generator.get_statistics()
        print(f"\n 统计信息:")
        print(f"   分析的方法: {stats['generator_stats']['analyzed_methods']}")
        print(f"   生成的测试: {stats['generator_stats']['generated_tests']}")
        print(f"   失败的生成: {stats['generator_stats']['failed_generations']}")
        print(f"   上下文检索: {stats['generator_stats']['context_retrievals']}")
        print(f"   修复尝试: {stats['generator_stats']['fix_attempts']}")
        
        # 计算成功率
        total_attempts = stats['generator_stats']['generated_tests'] + stats['generator_stats']['failed_generations']
        if total_attempts > 0:
            success_rate = (stats['generator_stats']['generated_tests'] / total_attempts) * 100
            print(f"   成功率: {success_rate:.1f}%")
        
        # 5. 清理资源
        generator.cleanup()
        
    except Exception as e:
        print(f" 运行失败: {e}")
        import traceback
        traceback.print_exc()

def debug_example():
    """调试模式示例"""
    print("\n 调试模式示例")
    print("=" * 50)
    
    project_path = Path("../pdfcompare")
    output_dir = Path("./debug_test_output")
    
    if not project_path.exists():
        print(f" 项目路径不存在: {project_path}")
        return
    
    # 启用调试模式
    generator = ImprovedTestGenerator(
        project_path=project_path,
        output_dir=output_dir,
        debug=True  # 启用详细调试信息
    )
    
    print(" 启用调试模式，将显示详细的生成过程...")
    
    result = generator.generate_test_for_method(
        class_name="com.example.pdfcompare.util.HashUtilityClass",
        method_name="hashBytes",
        use_rag=True,
        test_style="comprehensive",
        max_fix_attempts=1  # 减少尝试次数以节省时间
    )
    
    print(f"\n 调试模式结果:")
    print(f"   成功: {result['success']}")
    print(f"   方法签名: {result.get('method_signature')}")
    print(f"   RAG上下文: {result.get('context_used', 0)} 个")
    
    generator.cleanup()

def different_styles_example():
    """不同测试风格示例"""
    print("\n 不同测试风格示例")
    print("=" * 50)
    
    project_path = Path("../pdfcompare")
    output_dir = Path("./styles_test_output")
    
    if not project_path.exists():
        print(f" 项目路径不存在: {project_path}")
        return
    
    generator = ImprovedTestGenerator(project_path, output_dir)
    
    # 测试不同风格
    styles = ["comprehensive", "minimal", "edge-case"]
    
    for style in styles:
        print(f" 测试风格: {style}")
        
        result = generator.generate_test_for_method(
            class_name="com.example.pdfcompare.util.HashUtilityClass",
            method_name="hashBytes",
            use_rag=True,
            test_style=style,
            max_fix_attempts=1
        )
        
        status = "" if result['success'] else ""
        print(f"   {status} {style} 风格 - 耗时: {result.get('total_duration', 0):.2f}s")
    
    generator.cleanup()

def performance_example():
    """性能测试示例"""
    print("\n⚡ 性能测试示例")
    print("=" * 50)
    
    project_path = Path("../pdfcompare")
    output_dir = Path("./performance_test_output")
    
    if not project_path.exists():
        print(f" 项目路径不存在: {project_path}")
        return
    
    import time
    
    # 测试不同配置的性能
    configs = [
        {"use_rag": False, "name": "无RAG"},
        {"use_rag": True, "name": "启用RAG"},
    ]
    
    for config in configs:
        print(f" 测试配置: {config['name']}")
        
        generator = ImprovedTestGenerator(project_path, output_dir)
        
        start_time = time.time()
        result = generator.generate_test_for_method(
            class_name="com.example.pdfcompare.util.HashUtilityClass",
            method_name="hashBytes",
            use_rag=config["use_rag"],
            test_style="minimal",
            max_fix_attempts=1
        )
        end_time = time.time()
        
        duration = end_time - start_time
        status = "" if result['success'] else ""
        print(f"   {status} {config['name']} - 总耗时: {duration:.2f}s")
        
        generator.cleanup()

def main():
    """主函数"""
    print(" LLM4TestGen 改进版使用示例集合")
    print("=" * 60)
    
    # 运行基础示例
    basic_example()
    
    # 可以取消注释运行其他示例
    # debug_example()
    # different_styles_example()
    # performance_example()
    
    print("\n 示例运行完成！")
    print("\n 使用提示:")
    print("   1. 修改 project_path 为你的Java项目路径")
    print("   2. 确保Ollama服务正在运行")
    print("   3. 启用debug=True查看详细过程")
    print("   4. 尝试不同的test_style: comprehensive, minimal, edge-case")
    print("   5. 调整max_fix_attempts控制修复尝试次数")

if __name__ == "__main__":
    main()
