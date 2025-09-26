#!/usr/bin/env python3
"""
最终对比演示：RAG vs Context-Aware vs 混合模式
展示三种模式的实际效果和性能差异
"""

import subprocess
import time
import sys
from pathlib import Path

def run_test_generation(mode, class_name, method_name, output_dir, timeout=120):
    """运行测试生成并返回结果"""
    cmd = f"""python main_test_generator.py \
  --project ../pdfcompare \
  --class {class_name} \
  --method {method_name} \
  --generation-mode {mode} \
  --output {output_dir} \
  --max-attempts 3"""
    
    print(f"\n{'='*60}")
    print(f" 测试 {mode.upper()} 模式")
    print(f"{'='*60}")
    print(f" 目标: {class_name}.{method_name}")
    print(f" 输出: {output_dir}")
    print(f"⏱  超时: {timeout}秒")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 解析结果
        success = result.returncode == 0 and " 状态: 成功" in result.stdout
        
        # 提取关键信息
        lines = result.stdout.split('\n')
        total_time = None
        context_count = None
        
        for line in lines:
            if "⏱  总耗时:" in line:
                total_time = line.split("⏱  总耗时:")[1].strip()
            elif " 上下文数量:" in line:
                context_count = line.split(" 上下文数量:")[1].strip()
        
        return {
            'mode': mode,
            'success': success,
            'duration': duration,
            'total_time': total_time,
            'context_count': context_count,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        duration = end_time - start_time
        print(f" {mode.upper()}模式超时 ({timeout}秒)")
        return {
            'mode': mode,
            'success': False,
            'duration': duration,
            'total_time': f"{duration:.2f} 秒 (超时)",
            'context_count': "N/A",
            'error': 'timeout'
        }
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f" {mode.upper()}模式执行失败: {e}")
        return {
            'mode': mode,
            'success': False,
            'duration': duration,
            'total_time': f"{duration:.2f} 秒 (错误)",
            'context_count': "N/A",
            'error': str(e)
        }

def analyze_generated_code(output_dir, mode):
    """分析生成的代码质量"""
    test_files = list(Path(output_dir).glob("*.java"))
    
    if not test_files:
        return {
            'has_file': False,
            'file_size': 0,
            'line_count': 0,
            'has_mocks': False,
            'has_assertions': False,
            'test_method_count': 0
        }
    
    test_file = test_files[0]
    content = test_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # 分析代码质量
    has_mocks = '@Mock' in content
    has_assertions = 'assert' in content.lower()
    test_method_count = content.count('@Test')
    has_specific_logic = 'TODO' not in content  # 检查是否有具体实现
    
    return {
        'has_file': True,
        'file_size': len(content),
        'line_count': len(lines),
        'has_mocks': has_mocks,
        'has_assertions': has_assertions,
        'test_method_count': test_method_count,
        'has_specific_logic': has_specific_logic,
        'file_path': str(test_file)
    }

def main():
    """主对比函数"""
    print(" LLM4TestGen 最终模式对比演示")
    print("=" * 80)
    print("""
这个演示将对比三种生成模式的实际效果：
1. Context-Aware模式 - 新的上下文感知模式
2. 混合模式 - Context-Aware + RAG回退
3. RAG模式 - 传统的向量检索模式

我们将测试同一个方法，对比生成速度、代码质量和成功率。
    """)
    
    # 测试目标
    test_target = {
        'class_name': 'com.example.pdfcompare.util.ImageComparator',
        'method_name': 'compareImages'
    }
    
    print(f" 测试目标: {test_target['class_name']}.{test_target['method_name']}")
    
    input("\n按Enter键开始对比测试...")
    
    results = []
    
    # 1. Context-Aware模式
    print("\n 测试Context-Aware模式...")
    ca_result = run_test_generation(
        'context-aware', 
        test_target['class_name'], 
        test_target['method_name'],
        './comparison_context_aware',
        timeout=120
    )
    results.append(ca_result)
    
    # 2. 混合模式
    print("\n 测试混合模式...")
    hybrid_result = run_test_generation(
        'hybrid',
        test_target['class_name'], 
        test_target['method_name'],
        './comparison_hybrid',
        timeout=120
    )
    results.append(hybrid_result)
    
    # 3. RAG模式（快速版本）
    print("\n 测试RAG模式...")
    print("  注意: RAG模式通常较慢，设置较短超时时间")
    rag_result = run_test_generation(
        'rag',
        test_target['class_name'], 
        test_target['method_name'],
        './comparison_rag',
        timeout=90  # 较短的超时时间
    )
    results.append(rag_result)
    
    # 分析生成的代码
    print("\n 分析生成的代码质量...")
    for result in results:
        if result['success']:
            output_dir = f"./comparison_{result['mode'].replace('-', '_')}"
            code_analysis = analyze_generated_code(output_dir, result['mode'])
            result['code_analysis'] = code_analysis
        else:
            result['code_analysis'] = {'has_file': False}
    
    # 生成对比报告
    print("\n" + "="*80)
    print(" 最终对比报告")
    print("="*80)
    
    # 表格头
    print(f"{'模式':<15} {'成功':<6} {'耗时':<15} {'上下文':<8} {'文件':<6} {'行数':<6} {'Mock':<6} {'断言':<6} {'测试数':<6}")
    print("-" * 85)
    
    # 表格内容
    for result in results:
        mode = result['mode']
        success = "" if result['success'] else ""
        time_str = result['total_time'] or f"{result['duration']:.2f}秒"
        context = result['context_count'] or "N/A"
        
        if result['code_analysis']['has_file']:
            ca = result['code_analysis']
            file_exists = ""
            line_count = ca['line_count']
            has_mocks = "" if ca['has_mocks'] else ""
            has_assertions = "" if ca['has_assertions'] else ""
            test_count = ca['test_method_count']
        else:
            file_exists = ""
            line_count = 0
            has_mocks = ""
            has_assertions = ""
            test_count = 0
        
        print(f"{mode:<15} {success:<6} {time_str:<15} {context:<8} {file_exists:<6} {line_count:<6} {has_mocks:<6} {has_assertions:<6} {test_count:<6}")
    
    # 详细分析
    print(f"\n 详细分析:")
    
    successful_results = [r for r in results if r['success']]
    if successful_results:
        fastest = min(successful_results, key=lambda x: x['duration'])
        print(f"    最快模式: {fastest['mode']} ({fastest['duration']:.2f}秒)")
        
        # 代码质量分析
        best_quality = None
        best_score = 0
        
        for result in successful_results:
            if result['code_analysis']['has_file']:
                ca = result['code_analysis']
                score = (
                    (1 if ca['has_mocks'] else 0) +
                    (1 if ca['has_assertions'] else 0) +
                    (1 if ca['has_specific_logic'] else 0) +
                    min(ca['test_method_count'] / 3, 1)  # 标准化测试方法数
                )
                
                if score > best_score:
                    best_score = score
                    best_quality = result
        
        if best_quality:
            print(f"   🏆 最佳质量: {best_quality['mode']} (评分: {best_score:.1f}/4)")
    
    # 推荐
    print(f"\n 推荐使用:")
    context_aware_success = any(r['mode'] == 'context-aware' and r['success'] for r in results)
    hybrid_success = any(r['mode'] == 'hybrid' and r['success'] for r in results)
    
    if hybrid_success:
        print(f"   🥇 混合模式 - 最高成功率和稳定性")
    elif context_aware_success:
        print(f"   🥈 Context-Aware模式 - 速度最快")
    else:
        print(f"   🥉 RAG模式 - 传统模式，适合复杂场景")
    
    # 显示生成的代码示例
    print(f"\n 生成的代码示例:")
    for result in results:
        if result['success'] and result['code_analysis']['has_file']:
            print(f"\n{result['mode'].upper()}模式生成的代码:")
            file_path = result['code_analysis']['file_path']
            try:
                content = Path(file_path).read_text(encoding='utf-8')
                lines = content.split('\n')[:15]  # 显示前15行
                for i, line in enumerate(lines, 1):
                    print(f"   {i:2d}: {line}")
                if len(content.split('\n')) > 15:
                    print(f"   ... 还有 {len(content.split('\n')) - 15} 行")
            except Exception as e:
                print(f"    读取文件失败: {e}")
    
    print(f"\n" + "="*80)
    print(" 对比测试完成！")
    print(f"📚 查看详细文档: docs/context_aware_guide.md")

if __name__ == "__main__":
    main()
