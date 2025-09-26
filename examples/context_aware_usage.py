#!/usr/bin/env python3
"""
Context-Aware Code Generation 使用示例
展示新的上下文感知模式的各种用法
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from improved_test_generator import ConversationAwareTestGenerator
from context_aware import ContextAwareTestGenerator

def example_context_aware_basic():
    """Context-Aware基本用法"""
    print(" Context-Aware基本用法示例")
    print("=" * 50)
    
    # 创建Context-Aware生成器
    generator = ContextAwareTestGenerator(
        project_path="../pdfcompare",
        output_dir="./context_aware_basic"
    )
    
    # 生成测试
    result = generator.generate_test(
        target_class_fqn="com.example.pdfcompare.util.ImageComparator",
        target_method_name="compareImages",
        force_reindex=True,
        max_fix_attempts=3
    )
    
    print(f"生成结果: {'成功' if result['success'] else '失败'}")
    print(f"依赖上下文: {len(result.get('context', {}).get('dependency_contexts', []))} 个")
    print(f"修复应用: {len(result.get('fixes_applied', []))} 个")
    
    if result['fixes_applied']:
        print("应用的修复:")
        for fix in result['fixes_applied']:
            print(f"  • {fix}")
    
    return result

def example_mode_comparison():
    """生成模式对比"""
    print("\n⚖  RAG vs Context-Aware 对比")
    print("=" * 50)
    
    test_target = {
        'class_name': 'com.example.pdfcompare.util.HashUtilityClass',
        'method_name': 'hashBytes'
    }
    
    results = {}
    
    # 1. RAG模式
    print("1⃣ 测试RAG模式...")
    rag_generator = ConversationAwareTestGenerator(
        project_path=Path("../pdfcompare"),
        output_dir=Path("./comparison_rag"),
        debug=False
    )
    
    rag_result = rag_generator.generate_test_for_method(
        class_name=test_target['class_name'],
        method_name=test_target['method_name'],
        use_rag=True,
        test_style="comprehensive"
    )
    results['rag'] = rag_result
    
    # 2. Context-Aware模式
    print("2⃣ 测试Context-Aware模式...")
    ca_generator = ContextAwareTestGenerator(
        project_path="../pdfcompare",
        output_dir="./comparison_context_aware"
    )
    
    ca_result = ca_generator.generate_test(
        target_class_fqn=test_target['class_name'],
        target_method_name=test_target['method_name'],
        force_reindex=False,
        max_fix_attempts=3
    )
    results['context_aware'] = ca_result
    
    # 对比结果
    print("\n 对比结果:")
    print(f"{'模式':<15} {'成功':<6} {'上下文':<8} {'修复':<6}")
    print("-" * 40)
    
    rag_success = "" if rag_result['success'] else ""
    rag_context = rag_result.get('context_used', 0)
    print(f"{'RAG':<15} {rag_success:<6} {rag_context:<8} {'N/A':<6}")
    
    ca_success = "" if ca_result['success'] else ""
    ca_context = len(ca_result.get('context', {}).get('dependency_contexts', []))
    ca_fixes = len(ca_result.get('fixes_applied', []))
    print(f"{'Context-Aware':<15} {ca_success:<6} {ca_context:<8} {ca_fixes:<6}")
    
    return results

def example_hybrid_simulation():
    """混合模式模拟"""
    print("\n 混合模式模拟")
    print("=" * 50)
    
    class_name = "com.example.pdfcompare.util.PDFComparator"
    method_name = "comparePDFs"
    
    print(f"目标: {class_name}.{method_name}")
    
    # 1. 先尝试Context-Aware
    print("\n1⃣ 尝试Context-Aware模式...")
    ca_generator = ContextAwareTestGenerator(
        project_path="../pdfcompare",
        output_dir="./hybrid_test"
    )
    
    ca_result = ca_generator.generate_test(
        target_class_fqn=class_name,
        target_method_name=method_name,
        force_reindex=False,
        max_fix_attempts=2
    )
    
    if ca_result['success']:
        print(" Context-Aware模式成功")
        return ca_result
    else:
        print(" Context-Aware模式失败，尝试RAG回退...")
        
        # 2. 回退到RAG
        print("\n2⃣ 回退到RAG模式...")
        rag_generator = ConversationAwareTestGenerator(
            project_path=Path("../pdfcompare"),
            output_dir=Path("./hybrid_test"),
            debug=True
        )
        
        rag_result = rag_generator.generate_test_for_method(
            class_name=class_name,
            method_name=method_name,
            use_rag=True,
            test_style="comprehensive",
            max_fix_attempts=3
        )
        
        if rag_result['success']:
            print(" RAG回退成功")
            rag_result['hybrid_mode'] = True
            return rag_result
        else:
            print(" 两种模式都失败")
            return {'success': False, 'hybrid_mode': True}

def example_batch_context_aware():
    """批量Context-Aware生成"""
    print("\n 批量Context-Aware生成")
    print("=" * 50)
    
    # 要测试的方法列表
    test_targets = [
        ("com.example.pdfcompare.util.HashUtilityClass", "hashBytes"),
        ("com.example.pdfcompare.util.ImageComparator", "compareImages"),
        ("com.example.pdfcompare.util.PDFComparator", "comparePDFs"),
    ]
    
    generator = ContextAwareTestGenerator(
        project_path="../pdfcompare",
        output_dir="./batch_context_aware"
    )
    
    results = []
    
    for i, (class_name, method_name) in enumerate(test_targets):
        print(f"\n生成测试 {i+1}: {class_name}.{method_name}")
        
        result = generator.generate_test(
            target_class_fqn=class_name,
            target_method_name=method_name,
            force_reindex=(i == 0),  # 只在第一次强制重新索引
            max_fix_attempts=3
        )
        
        results.append({
            'target': f"{class_name}.{method_name}",
            'success': result['success'],
            'dependencies': len(result.get('context', {}).get('dependency_contexts', [])),
            'fixes': len(result.get('fixes_applied', []))
        })
        
        print(f"  状态: {' 成功' if result['success'] else ' 失败'}")
        print(f"  依赖: {results[-1]['dependencies']} 个")
        print(f"  修复: {results[-1]['fixes']} 个")
    
    # 统计结果
    successful = sum(1 for r in results if r['success'])
    total_deps = sum(r['dependencies'] for r in results)
    total_fixes = sum(r['fixes'] for r in results)
    
    print(f"\n 批量生成统计:")
    print(f"  总数: {len(results)}")
    print(f"  成功: {successful}")
    print(f"  成功率: {successful/len(results)*100:.1f}%")
    print(f"  总依赖: {total_deps}")
    print(f"  总修复: {total_fixes}")
    
    return results

def example_project_analysis():
    """项目分析示例"""
    print("\n 项目分析示例")
    print("=" * 50)
    
    generator = ContextAwareTestGenerator(
        project_path="../pdfcompare",
        output_dir="./analysis_test"
    )
    
    # 获取项目统计
    stats = generator.get_project_statistics()
    
    print("项目统计信息:")
    print(f"   类数量: {stats['classes']}")
    print(f"    方法数量: {stats['methods']}")
    print(f"    构造器数量: {stats['constructors']}")
    print(f"   字段数量: {stats['fields']}")
    
    return stats

def main():
    """主函数"""
    print(" Context-Aware Code Generation 使用示例")
    print("=" * 80)
    
    try:
        # 1. Context-Aware基本用法
        example_context_aware_basic()
        
        # 2. 模式对比
        example_mode_comparison()
        
        # 3. 混合模式模拟
        example_hybrid_simulation()
        
        # 4. 批量生成
        example_batch_context_aware()
        
        # 5. 项目分析
        example_project_analysis()
        
        print("\n" + "=" * 80)
        print(" 所有Context-Aware示例执行完成")
        
    except Exception as e:
        print(f"\n 示例执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
