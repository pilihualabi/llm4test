#!/usr/bin/env python3
"""
最终版测试生成器
修复了所有已知问题，包含完整的方法体、进度显示和调试信息
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from improved_test_generator import ImprovedTestGenerator

def main():
    """主函数 - 演示最终版本"""
    print(" 最终版测试生成器")
    print("=" * 60)
    
    # 设置日志级别
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    
    # 项目路径
    project_path = Path("../pdfcompare")
    output_dir = Path("./final_test_output")
    
    if not project_path.exists():
        print(f" 项目路径不存在: {project_path}")
        return
    
    try:
        # 初始化生成器（启用调试模式）
        generator = ImprovedTestGenerator(project_path, output_dir, debug=True)
        
        # 显示配置
        print(f" 生成器配置:")
        print(f"    Tree-sitter: 可用")
        print(f"    编译管理器: 改进版Maven支持")
        print(f"    RAG系统: 启用")
        print(f"    调试模式: 启用")
        print(f"    输出目录: {output_dir}")
        
        # 执行测试生成
        print(f"\n" + "="*60)
        print(" 开始生成测试")
        
        result = generator.generate_test_for_method(
            class_name="com.example.pdfcompare.util.HashUtilityClass",
            method_name="hashBytes",
            use_rag=True,
            test_style="comprehensive",
            max_fix_attempts=2  # 减少尝试次数以节省时间
        )
        
        # 显示结果摘要
        print(f"\n" + "="*60)
        print(" 生成结果摘要")
        
        success_icon = "" if result['success'] else ""
        print(f"{success_icon} 状态: {result['success']}")
        print(f"⏱  总耗时: {result.get('total_duration', 0):.2f} 秒")
        print(f" RAG上下文: {result.get('context_used', 0)} 个")
        print(f" 方法签名: {result['method_signature']}")
        
        if result['success']:
            test_file = result.get('test_file_path')
            print(f" 测试文件: {Path(test_file).name if test_file else 'N/A'}")
            print(f" 编译尝试: {result.get('attempts', 'N/A')} 次")
            
            # 显示生成的测试代码片段
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
            print(f" 错误: {result.get('error', 'Unknown error')}")
            print(f" 编译尝试: {result.get('attempts', 'N/A')} 次")
        
        # 显示统计信息
        stats = generator.get_statistics()['generator_stats']
        print(f"\n 统计信息:")
        print(f"    分析的方法: {stats['analyzed_methods']}")
        print(f"    成功生成: {stats['generated_tests']}")
        print(f"    失败生成: {stats['failed_generations']}")
        print(f"    上下文检索: {stats['context_retrievals']}")
        print(f"    修复尝试: {stats['fix_attempts']}")
        
        # 成功率计算
        total_attempts = stats['generated_tests'] + stats['failed_generations']
        if total_attempts > 0:
            success_rate = (stats['generated_tests'] / total_attempts) * 100
            print(f"    成功率: {success_rate:.1f}%")
        
        # 清理
        generator.cleanup()
        
        print(f"\n" + "="*60)
        if result['success']:
            print(" 测试生成成功完成！")
            print(f" 测试文件已保存到: {output_dir}")
        else:
            print("  测试生成未完全成功，但系统运行正常")
            print(" 建议检查编译环境和依赖配置")
        
    except Exception as e:
        print(f" 运行失败: {e}")
        import traceback
        traceback.print_exc()

def show_improvements():
    """显示改进点"""
    print(f"\n" + "="*60)
    print(" 主要改进点")
    print(f"="*60)
    
    improvements = [
        " 完整方法体提取 - 使用Tree-sitter解析完整的方法实现",
        " RAG上下文增强 - 传递相关代码上下文给大模型",
        " 进度显示优化 - 清晰的步骤划分和实时状态更新",
        " 调试信息丰富 - 显示与大模型的详细交互信息",
        " 提示模板改进 - 包含方法体和上下文的增强提示",
        " 修复流程优化 - 简化的修复提示，避免冗余信息",
        " Maven项目支持 - 改进的依赖管理和编译流程",
        " 多语言架构 - 基于Tree-sitter的可扩展解析框架"
    ]
    
    for improvement in improvements:
        print(f"  {improvement}")
    
    print(f"\n 使用建议:")
    print(f"  1. 确保Maven项目已正确配置JUnit 5依赖")
    print(f"  2. 启用调试模式查看详细的生成过程")
    print(f"  3. 根据项目特点调整RAG上下文数量")
    print(f"  4. 可以扩展Tree-sitter解析器支持更多语言")

if __name__ == "__main__":
    main()
    show_improvements()
