#!/usr/bin/env python3
"""
完整系统演示
展示从项目分析到智能测试生成的完整流程
"""

import sys
import tempfile
import shutil
from pathlib import Path
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def create_demo_project() -> Path:
    """创建演示项目"""
    print(" 创建演示Java项目...")
    
    # 创建临时目录
    demo_dir = Path("./demo_java_project")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    
    demo_dir.mkdir()
    
    # 创建项目结构
    src_dir = demo_dir / "src" / "main" / "java" / "com" / "example"
    src_dir.mkdir(parents=True)
    
    # 创建Calculator类 - 专注于数学计算
    calculator_content = '''package com.example;

/**
 * 简单的计算器类，用于演示测试生成
 */
public class Calculator {
    
    /**
     * 计算两个整数的和
     * @param a 第一个数
     * @param b 第二个数
     * @return 两数之和
     */
    public int add(int a, int b) {
        return a + b;
    }
    
    /**
     * 计算两个整数的乘积
     * @param a 第一个数
     * @param b 第二个数  
     * @return 两数之积
     */
    public int multiply(int a, int b) {
        return a * b;
    }
    
    /**
     * 计算整数除法，包含异常处理
     * @param dividend 被除数
     * @param divisor 除数
     * @return 商
     * @throws IllegalArgumentException 当除数为0时
     */
    public int divide(int dividend, int divisor) {
        if (divisor == 0) {
            throw new IllegalArgumentException("除数不能为零");
        }
        return dividend / divisor;
    }
}'''
    
    # 创建StringUtils类 - 专注于字符串操作
    stringutils_content = '''package com.example;

/**
 * 字符串工具类
 */
public class StringUtils {
    
    /**
     * 检查字符串是否为空或null
     * @param str 要检查的字符串
     * @return 如果字符串为null或空则返回true
     */
    public boolean isEmpty(String str) {
        return str == null || str.length() == 0;
    }
    
    /**
     * 反转字符串
     * @param str 要反转的字符串
     * @return 反转后的字符串，如果输入为null则返回null
     */
    public String reverse(String str) {
        if (str == null) {
            return null;
        }
        return new StringBuilder(str).reverse().toString();
    }
    
    /**
     * 统计字符串中指定字符的出现次数
     * @param str 目标字符串
     * @param ch 要统计的字符
     * @return 字符出现的次数
     */
    public int countChar(String str, char ch) {
        if (str == null) {
            return 0;
        }
        int count = 0;
        for (char c : str.toCharArray()) {
            if (c == ch) {
                count++;
            }
        }
        return count;
    }
}'''
    
    # 写入文件
    (src_dir / "Calculator.java").write_text(calculator_content)
    (src_dir / "StringUtils.java").write_text(stringutils_content)
    
    print(f"    演示项目已创建: {demo_dir}")
    print(f"    包含2个Java类，6个方法")
    
    return demo_dir

def test_enhanced_generator(project_path: Path):
    """测试增强版生成器"""
    print("\n 测试增强版测试生成器...")
    
    try:
        from enhanced_test_generator import EnhancedTestGenerator
        
        # 初始化生成器
        generator = EnhancedTestGenerator(project_path)
        
        # 1. 测试单个方法生成（使用RAG）
        print("\n 测试1: 单个方法生成 (启用RAG)")
        rag_result = generator.generate_test_for_method(
            "com.example.Calculator", 
            "divide", 
            use_rag=True
        )
        
        if rag_result['success']:
            print(f"    RAG模式生成成功")
            print(f"    文件: {Path(rag_result['test_file_path']).name}")
            print(f"    上下文数: {rag_result['context_used']}")
        else:
            print(f"    RAG模式失败: {rag_result.get('error')}")
        
        # 2. 测试单个方法生成（不使用RAG）
        print("\n 测试2: 单个方法生成 (不使用RAG)")
        no_rag_result = generator.generate_test_for_method(
            "com.example.StringUtils", 
            "reverse", 
            use_rag=False
        )
        
        if no_rag_result['success']:
            print(f"    普通模式生成成功")
            print(f"    文件: {Path(no_rag_result['test_file_path']).name}")
        else:
            print(f"    普通模式失败: {no_rag_result.get('error')}")
        
        # 3. 显示生成的测试代码片段
        if rag_result['success']:
            print(f"\n 生成的测试代码示例 (前200字符):")
            test_code = rag_result['generated_test'][:200]
            print(f"   {test_code}...")
        
        # 4. 显示统计信息
        print(f"\n 生成器统计:")
        stats = generator.get_statistics()
        gen_stats = stats['generator_stats']
        print(f"    已分析方法: {gen_stats['analyzed_methods']}")
        print(f"    成功生成: {gen_stats['generated_tests']}")
        print(f"    生成失败: {gen_stats['failed_generations']}")
        print(f"    RAG检索: {gen_stats['context_retrievals']}")
        
        return rag_result['success'] or no_rag_result['success']
        
    except Exception as e:
        print(f"    增强生成器测试异常: {e}")
        return False

def compare_with_without_rag(project_path: Path):
    """对比使用和不使用RAG的效果"""
    print("\n🔬 RAG效果对比测试...")
    
    try:
        from enhanced_test_generator import EnhancedTestGenerator
        
        generator = EnhancedTestGenerator(project_path)
        
        test_method = ("com.example.Calculator", "add")
        
        # 1. 使用RAG生成
        print("    使用RAG技术生成...")
        rag_result = generator.generate_test_for_method(
            test_method[0], test_method[1], use_rag=True
        )
        
        # 2. 不使用RAG生成  
        print("    普通模式生成...")
        normal_result = generator.generate_test_for_method(
            test_method[0], test_method[1], use_rag=False
        )
        
        # 3. 对比结果
        print(f"\n 对比结果:")
        if rag_result['success'] and normal_result['success']:
            print(f"    两种模式都成功生成测试")
            print(f"    RAG模式使用上下文: {rag_result.get('context_used', 0)} 个")
            print(f"   📏 RAG生成代码长度: {len(rag_result['generated_test'])} 字符")
            print(f"   📏 普通生成代码长度: {len(normal_result['generated_test'])} 字符")
            
            # 保存对比文件
            output_dir = Path(generator.output_dir)
            (output_dir / "comparison_rag.java").write_text(rag_result['generated_test'])
            (output_dir / "comparison_normal.java").write_text(normal_result['generated_test'])
            print(f"    对比文件已保存到: {output_dir}")
            
            return True
        else:
            print(f"    生成对比失败")
            return False
            
    except Exception as e:
        print(f"    RAG对比测试异常: {e}")
        return False

def test_project_analysis_integration(project_path: Path):
    """测试项目分析集成"""
    print("\n 测试项目分析集成...")
    
    try:
        from rag.project_analyzer import SmartProjectAnalyzer
        
        # 初始化项目分析器
        analyzer = SmartProjectAnalyzer(project_path)
        
        # 分析项目
        analysis_result = analyzer.analyze_project(force_reindex=True)
        
        print(f"    项目分析完成:")
        print(f"       文件数: {analysis_result['stats']['total_files']}")
        print(f"      📚 类数: {analysis_result['stats']['total_classes']}")
        print(f"       方法数: {analysis_result['stats']['total_methods']}")
        
        # 测试上下文检索
        context_results = analyzer.find_relevant_context(
            "com.example.Calculator#add",
            "mathematical addition operation",
            top_k=3
        )
        
        print(f"    为Calculator.add找到 {len(context_results)} 个相关上下文")
        
        # 显示相关上下文
        for i, context in enumerate(context_results[:2], 1):
            metadata = context['metadata']
            method_name = metadata.get('method_name', 'unknown')
            class_name = metadata.get('class_name', 'unknown')
            similarity = 1 - context.get('distance', 1.0)
            print(f"      {i}. {class_name}.{method_name} (相似度: {similarity:.3f})")
        
        return len(context_results) > 0
        
    except Exception as e:
        print(f"    项目分析集成测试异常: {e}")
        return False

def cleanup_demo(project_path: Path):
    """清理演示项目"""
    print("\n🧹 清理演示数据...")
    
    try:
        cleanup_paths = [
            project_path,
            Path("./chroma_db"),
            Path("./generated_tests")
        ]
        
        for path in cleanup_paths:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"    删除: {path}")
        
        return True
    except Exception as e:
        print(f"    清理失败: {e}")
        return False

def main():
    """主演示函数"""
    print("🎬 完整系统演示开始...")
    print("=" * 60)
    
    # 设置日志级别
    logging.basicConfig(level=logging.WARNING)
    
    try:
        # 1. 创建演示项目
        demo_project = create_demo_project()
        
        # 2. 测试项目分析集成
        analysis_success = test_project_analysis_integration(demo_project)
        
        # 3. 测试增强生成器
        generator_success = test_enhanced_generator(demo_project)
        
        # 4. RAG效果对比
        comparison_success = compare_with_without_rag(demo_project)
        
        # 5. 汇总结果
        total_tests = 3
        passed_tests = sum([analysis_success, generator_success, comparison_success])
        
        print(f"\n{'=' * 60}")
        print(f" 完整系统演示总结: {passed_tests}/{total_tests} 通过")
        print("=" * 60)
        
        if passed_tests >= 2:
            print(" 系统基本功能正常!")
            print("\n✨ 新系统特性:")
            print("    智能项目分析 - 自动索引代码库")
            print("    RAG增强上下文 - 智能检索相关代码")
            print("   🤖 多模型支持 - 代码生成 + 修复模型")
            print("    向量化存储 - ChromaDB + Ollama嵌入")
            print("    语义搜索 - 基于代码语义匹配")
            
            print(f"\n 查看生成的测试文件:")
            output_dir = demo_project / "generated_tests"
            if output_dir.exists():
                for test_file in output_dir.glob("*.java"):
                    print(f"    {test_file.name}")
        else:
            print(" 系统存在问题，需要进一步调试")
        
        # 6. 清理（询问用户）
        print(f"\n🤔 是否保留演示文件以供查看? (y/n): ", end="")
        try:
            keep_files = input().lower().startswith('y')
            if not keep_files:
                cleanup_demo(demo_project)
            else:
                print(f" 演示文件保留在: {demo_project}")
        except:
            # 如果无法获取用户输入，默认保留文件
            print(f" 演示文件保留在: {demo_project}")
        
        return passed_tests >= 2
        
    except KeyboardInterrupt:
        print(f"\n 用户中断演示")
        return False
    except Exception as e:
        print(f" 演示运行异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
