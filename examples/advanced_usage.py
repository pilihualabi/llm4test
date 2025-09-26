#!/usr/bin/env python3
"""
高级使用示例
展示LLM4TestGen的高级功能和自定义用法
"""

import sys
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def example_custom_vector_store():
    """示例1: 自定义向量存储"""
    print("示例1: 自定义向量存储配置")
    print("=" * 50)
    
    from rag.vector_store import CodeVectorStore
    from rag.project_analyzer import SmartProjectAnalyzer
    
    # 创建自定义向量存储
    custom_vector_store = CodeVectorStore(
        collection_name="my_custom_project",
        persist_directory="./custom_chroma_db"
    )
    
    # 手动添加代码片段
    code_snippets = [
        {
            'code': '''
            public class CustomCalculator {
                public double power(double base, double exponent) {
                    return Math.pow(base, exponent);
                }
            }
            ''',
            'metadata': {
                'type': 'class',
                'class_name': 'CustomCalculator',
                'file_path': 'custom/Calculator.java',
                'language': 'java'
            }
        },
        {
            'code': '''
            public double sqrt(double number) {
                if (number < 0) {
                    throw new IllegalArgumentException("Cannot compute square root of negative number");
                }
                return Math.sqrt(number);
            }
            ''',
            'metadata': {
                'type': 'method',
                'method_name': 'sqrt',
                'class_name': 'MathUtils',
                'language': 'java'
            }
        }
    ]
    
    # 批量添加
    codes = [snippet['code'] for snippet in code_snippets]
    metadatas = [snippet['metadata'] for snippet in code_snippets]
    
    doc_ids = custom_vector_store.add_batch_code_snippets(codes, metadatas)
    print(f" 添加了 {len(doc_ids)} 个代码片段")
    
    # 搜索测试
    results = custom_vector_store.search_similar_code(
        query="mathematical calculation power function",
        top_k=3
    )
    
    print(f" 搜索结果: {len(results)} 个匹配项")
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        similarity = 1 - result.get('distance', 1.0)
        print(f"   {i}. {metadata.get('class_name', 'Unknown')} (相似度: {similarity:.3f})")
    
    return len(results) > 0

def example_parallel_generation():
    """示例2: 并行测试生成"""
    print("\n示例2: 并行测试生成")
    print("=" * 50)
    
    from enhanced_test_generator import EnhancedTestGenerator
    
    # 要测试的方法列表
    methods_to_test = [
        ("com.example.Calculator", "add"),
        ("com.example.Calculator", "subtract"), 
        ("com.example.Calculator", "multiply"),
        ("com.example.MathUtils", "factorial"),
        ("com.example.StringUtils", "reverse"),
    ]
    
    project_path = Path("./sample-java-project")
    generator = EnhancedTestGenerator(project_path)
    
    def generate_single_test(class_name, method_name):
        """生成单个测试的函数"""
        start_time = time.time()
        result = generator.generate_test_for_method(
            class_name=class_name,
            method_name=method_name,
            use_rag=True
        )
        end_time = time.time()
        
        return {
            'class_name': class_name,
            'method_name': method_name,
            'result': result,
            'duration': end_time - start_time
        }
    
    print(f" 开始并行生成 {len(methods_to_test)} 个测试...")
    
    # 并行执行
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任务
        future_to_method = {
            executor.submit(generate_single_test, class_name, method_name): (class_name, method_name)
            for class_name, method_name in methods_to_test
        }
        
        results = []
        completed = 0
        
        # 收集结果
        for future in as_completed(future_to_method):
            completed += 1
            class_name, method_name = future_to_method[future]
            
            try:
                result_data = future.result()
                results.append(result_data)
                
                success = result_data['result']['success']
                duration = result_data['duration']
                status = "" if success else ""
                
                print(f"   [{completed}/{len(methods_to_test)}] {status} {class_name}.{method_name} ({duration:.1f}s)")
                
            except Exception as e:
                print(f"   [{completed}/{len(methods_to_test)}]  {class_name}.{method_name} 异常: {e}")
    
    # 统计结果
    successful = sum(1 for r in results if r['result']['success'])
    total_time = sum(r['duration'] for r in results)
    avg_time = total_time / len(results) if results else 0
    
    print(f"\n 并行生成统计:")
    print(f"   成功: {successful}/{len(results)}")
    print(f"   总耗时: {total_time:.1f}s")
    print(f"   平均耗时: {avg_time:.1f}s")
    print(f"   成功率: {successful/len(results):.1%}")
    
    return successful > 0

def example_custom_prompts():
    """示例3: 自定义提示工程"""
    print("\n示例3: 自定义提示工程")
    print("=" * 50)
    
    def create_advanced_test_prompt(method_info, context_info, test_style="comprehensive"):
        """创建高级测试提示"""
        
        base_prompt = f"""Generate JUnit 5 test methods for: {method_info['signature']}

Test Style: {test_style.upper()}
"""
        
        if test_style == "comprehensive":
            base_prompt += """
Requirements:
1. Test normal/happy path scenarios
2. Test edge cases and boundary conditions  
3. Test error conditions with proper exception handling
4. Use parameterized tests where appropriate
5. Include performance considerations if relevant
6. Add detailed documentation for each test case
"""
        elif test_style == "minimal":
            base_prompt += """
Requirements:
1. Test basic functionality only
2. Keep tests simple and focused
3. Minimal assertions
"""
        elif test_style == "bdd":
            base_prompt += """
Requirements:
1. Use BDD-style test naming (given_when_then)
2. Structure tests with Given/When/Then comments
3. Focus on behavior specification
4. Use descriptive test method names
"""
        
        # 添加上下文
        if context_info:
            base_prompt += f"\nRelevant Context from Codebase:\n"
            for i, context in enumerate(context_info[:3], 1):
                metadata = context.get('metadata', {})
                code_snippet = context.get('code', '')[:150]
                base_prompt += f"\n{i}. Related: {metadata.get('class_name', 'Unknown')}.{metadata.get('method_name', 'Unknown')}\n"
                base_prompt += f"   Code: {code_snippet}...\n"
        
        base_prompt += "\nGenerate the complete test class with proper imports:"
        
        return base_prompt
    
    # 示例方法信息
    method_info = {
        'signature': 'public int divide(int dividend, int divisor)',
        'class_name': 'Calculator',
        'method_name': 'divide'
    }
    
    # 模拟上下文信息
    mock_context = [
        {
            'metadata': {'class_name': 'Calculator', 'method_name': 'multiply'},
            'code': 'public int multiply(int a, int b) { return a * b; }'
        }
    ]
    
    # 不同风格的提示
    styles = ["comprehensive", "minimal", "bdd"]
    
    for style in styles:
        print(f"\n {style.upper()} 风格提示:")
        prompt = create_advanced_test_prompt(method_info, mock_context, style)
        print(f"   提示长度: {len(prompt)} 字符")
        print(f"   前100字符: {prompt[:100]}...")
    
    return True

def example_quality_metrics():
    """示例4: 测试质量评估"""
    print("\n示例4: 测试质量评估")
    print("=" * 50)
    
    def analyze_test_quality(generated_test_code):
        """分析生成测试的质量"""
        quality_metrics = {
            'has_imports': False,
            'has_test_annotation': False,
            'has_assertions': False,
            'has_exception_tests': False,
            'has_setup_teardown': False,
            'test_method_count': 0,
            'assertion_count': 0,
            'line_count': 0
        }
        
        lines = generated_test_code.split('\n')
        quality_metrics['line_count'] = len(lines)
        
        for line in lines:
            line = line.strip()
            
            # 检查导入
            if line.startswith('import'):
                quality_metrics['has_imports'] = True
            
            # 检查测试注解
            if '@Test' in line:
                quality_metrics['has_test_annotation'] = True
                quality_metrics['test_method_count'] += 1
            
            # 检查断言
            if 'assert' in line.lower():
                quality_metrics['has_assertions'] = True
                quality_metrics['assertion_count'] += 1
            
            # 检查异常测试
            if 'assertThrows' in line or 'expectedException' in line:
                quality_metrics['has_exception_tests'] = True
            
            # 检查Setup/Teardown
            if '@BeforeEach' in line or '@AfterEach' in line:
                quality_metrics['has_setup_teardown'] = True
        
        return quality_metrics
    
    def calculate_quality_score(metrics):
        """计算质量分数 (0-100)"""
        score = 0
        
        # 基础结构 (40分)
        if metrics['has_imports']: score += 10
        if metrics['has_test_annotation']: score += 15
        if metrics['has_assertions']: score += 15
        
        # 测试完整性 (40分)
        score += min(metrics['test_method_count'] * 5, 20)  # 最多20分
        score += min(metrics['assertion_count'] * 2, 20)    # 最多20分
        
        # 高级特性 (20分)
        if metrics['has_exception_tests']: score += 10
        if metrics['has_setup_teardown']: score += 10
        
        return min(score, 100)
    
    # 示例测试代码
    sample_test_code = '''
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

public class CalculatorTest {
    
    private Calculator calculator;
    
    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }
    
    @Test
    void testAdd() {
        assertEquals(5, calculator.add(2, 3));
        assertEquals(0, calculator.add(0, 0));
        assertEquals(-1, calculator.add(-3, 2));
    }
    
    @Test
    void testDivideByZero() {
        assertThrows(IllegalArgumentException.class, 
            () -> calculator.divide(10, 0));
    }
}
'''
    
    # 分析质量
    metrics = analyze_test_quality(sample_test_code)
    score = calculate_quality_score(metrics)
    
    print(f" 测试质量分析:")
    print(f"   代码行数: {metrics['line_count']}")
    print(f"   测试方法数: {metrics['test_method_count']}")
    print(f"   断言数量: {metrics['assertion_count']}")
    print(f"   包含导入: {'' if metrics['has_imports'] else ''}")
    print(f"   包含@Test注解: {'' if metrics['has_test_annotation'] else ''}")
    print(f"   包含断言: {'' if metrics['has_assertions'] else ''}")
    print(f"   包含异常测试: {'' if metrics['has_exception_tests'] else ''}")
    print(f"   包含Setup/Teardown: {'' if metrics['has_setup_teardown'] else ''}")
    
    print(f"\n🏆 质量分数: {score}/100")
    
    if score >= 80:
        print("   评级: 优秀 ⭐⭐⭐")
    elif score >= 60:
        print("   评级: 良好 ⭐⭐")
    elif score >= 40:
        print("   评级: 一般 ⭐")
    else:
        print("   评级: 需要改进")
    
    return score >= 60

def example_custom_filters():
    """示例5: 自定义代码过滤"""
    print("\n示例5: 自定义代码过滤和检索")
    print("=" * 50)
    
    from rag.vector_store import CodeVectorStore
    
    # 创建向量存储
    vector_store = CodeVectorStore("filtered_search_demo")
    
    # 添加多样化的代码示例
    diverse_code_samples = [
        {
            'code': 'public void setUp() { /* initialization */ }',
            'metadata': {
                'type': 'method',
                'method_name': 'setUp',
                'access_modifier': 'public',
                'category': 'test_setup',
                'complexity': 'simple',
                'language': 'java'
            }
        },
        {
            'code': 'private boolean validateInput(String input) { return input != null && !input.isEmpty(); }',
            'metadata': {
                'type': 'method', 
                'method_name': 'validateInput',
                'access_modifier': 'private',
                'category': 'validation',
                'complexity': 'simple',
                'language': 'java'
            }
        },
        {
            'code': 'public List<Integer> complexAlgorithm(int[] data) { /* complex logic */ }',
            'metadata': {
                'type': 'method',
                'method_name': 'complexAlgorithm', 
                'access_modifier': 'public',
                'category': 'algorithm',
                'complexity': 'complex',
                'language': 'java'
            }
        }
    ]
    
    # 添加样本
    for sample in diverse_code_samples:
        vector_store.add_code_snippet(sample['code'], sample['metadata'])
    
    print(f" 添加了 {len(diverse_code_samples)} 个代码样本")
    
    # 不同的过滤查询
    filter_queries = [
        {
            'name': '只查找public方法',
            'query': 'method implementation',
            'filter': {'access_modifier': 'public'}
        },
        {
            'name': '只查找验证相关方法',
            'query': 'validation logic',
            'filter': {'category': 'validation'}
        },
        {
            'name': '只查找简单方法',
            'query': 'simple function',
            'filter': {'complexity': 'simple'}
        },
        {
            'name': '复合过滤：public + simple',
            'query': 'method',
            'filter': {'access_modifier': 'public', 'complexity': 'simple'}
        }
    ]
    
    # 执行过滤查询
    for query_info in filter_queries:
        print(f"\n {query_info['name']}:")
        
        results = vector_store.search_similar_code(
            query=query_info['query'],
            top_k=5,
            filter_metadata=query_info['filter']
        )
        
        if results:
            print(f"   找到 {len(results)} 个结果:")
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                method_name = metadata.get('method_name', 'unknown')
                access_mod = metadata.get('access_modifier', 'unknown')
                category = metadata.get('category', 'unknown')
                print(f"      {i}. {access_mod} {method_name} ({category})")
        else:
            print("   没有找到匹配的结果")
    
    return True

def example_monitoring_and_logging():
    """示例6: 监控和日志"""
    print("\n示例6: 监控和日志系统")
    print("=" * 50)
    
    import logging
    from datetime import datetime
    
    # 设置详细日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('llm4testgen.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('LLM4TestGen')
    
    class GenerationMonitor:
        """生成过程监控器"""
        
        def __init__(self):
            self.stats = {
                'total_attempts': 0,
                'successful_generations': 0,
                'failed_generations': 0,
                'total_time': 0,
                'context_retrievals': 0,
                'avg_context_size': 0
            }
            self.start_time = None
        
        def start_generation(self, class_name, method_name):
            """开始生成监控"""
            self.start_time = time.time()
            self.stats['total_attempts'] += 1
            logger.info(f"开始生成测试: {class_name}.{method_name}")
        
        def end_generation(self, success, context_count=0):
            """结束生成监控"""
            if self.start_time:
                duration = time.time() - self.start_time
                self.stats['total_time'] += duration
                
                if success:
                    self.stats['successful_generations'] += 1
                    logger.info(f"生成成功，耗时 {duration:.2f}s，使用 {context_count} 个上下文")
                else:
                    self.stats['failed_generations'] += 1
                    logger.warning(f"生成失败，耗时 {duration:.2f}s")
                
                if context_count > 0:
                    self.stats['context_retrievals'] += 1
                    # 更新平均上下文大小
                    current_avg = self.stats['avg_context_size']
                    retrievals = self.stats['context_retrievals']
                    self.stats['avg_context_size'] = (current_avg * (retrievals - 1) + context_count) / retrievals
        
        def get_summary(self):
            """获取监控摘要"""
            if self.stats['total_attempts'] > 0:
                success_rate = self.stats['successful_generations'] / self.stats['total_attempts']
                avg_time = self.stats['total_time'] / self.stats['total_attempts']
            else:
                success_rate = 0
                avg_time = 0
            
            return {
                'success_rate': success_rate,
                'avg_generation_time': avg_time,
                'total_attempts': self.stats['total_attempts'],
                'avg_context_size': self.stats['avg_context_size']
            }
    
    # 使用监控器
    monitor = GenerationMonitor()
    
    # 模拟几次生成
    test_methods = [
        ("Calculator", "add", True, 3),
        ("Calculator", "divide", False, 2),
        ("StringUtils", "reverse", True, 1),
    ]
    
    for class_name, method_name, success, context_count in test_methods:
        monitor.start_generation(class_name, method_name)
        time.sleep(0.1)  # 模拟生成时间
        monitor.end_generation(success, context_count)
    
    # 生成报告
    summary = monitor.get_summary()
    
    print(f" 生成监控报告:")
    print(f"   总尝试次数: {summary['total_attempts']}")
    print(f"   成功率: {summary['success_rate']:.1%}")
    print(f"   平均生成时间: {summary['avg_generation_time']:.3f}s")
    print(f"   平均上下文大小: {summary['avg_context_size']:.1f}")
    
    # 日志文件信息
    log_file = Path('llm4testgen.log')
    if log_file.exists():
        print(f"\n 日志文件: {log_file}")
        print(f"   文件大小: {log_file.stat().st_size} 字节")
    
    return True

def main():
    """主函数 - 运行所有高级示例"""
    print(" LLM4TestGen 高级使用示例")
    print("=" * 70)
    
    examples = [
        ("自定义向量存储", example_custom_vector_store),
        ("并行测试生成", example_parallel_generation),
        ("自定义提示工程", example_custom_prompts),
        ("测试质量评估", example_quality_metrics),
        ("自定义代码过滤", example_custom_filters),
        ("监控和日志", example_monitoring_and_logging),
    ]
    
    results = []
    
    for name, func in examples:
        try:
            print(f"\n 运行高级示例: {name}")
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
    print(f"\n{'=' * 70}")
    print(" 高级示例运行总结:")
    print("=" * 70)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "" if success else ""
        print(f"   {status} {name}")
    
    print(f"\n 成功率: {successful}/{total} ({successful/total:.1%})")
    
    print(f"\n 高级功能特点:")
    print("    并行生成提升效率")
    print("    自定义提示工程")
    print("    质量评估和监控")
    print("    智能过滤和检索")
    print("    详细日志记录")
    
    print(f"\n 进阶使用建议:")
    print("   1. 根据项目需求自定义配置")
    print("   2. 使用并行生成提升大项目效率")
    print("   3. 建立质量评估标准")
    print("   4. 监控系统性能指标")

if __name__ == "__main__":
    main()
