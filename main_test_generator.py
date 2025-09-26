#!/usr/bin/env python3
"""
LLM4TestGen 主程序入口
完整的命令行测试生成工具，支持参数配置和详细输出
"""

import sys
import argparse
import logging
from pathlib import Path
import time
import json
import uuid
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from improved_test_generator import ImprovedTestGenerator

class ConversationLogger:
    """对话记录器，保存与大模型的对话内容"""

    def __init__(self, project_name, class_name, method_name, test_style, output_dir):
        self.conversation_id = str(uuid.uuid4())[:8]
        self.project_name = project_name
        self.class_name = class_name.split('.')[-1]  # 只取类名，不要包名
        self.method_name = method_name
        self.test_style = test_style
        self.start_time = datetime.now().isoformat()
        self.messages = []
        self.rag_contexts = []
        self.error_enhanced_contexts = []  # 新增：错误驱动增强的上下文
        self.metadata = {
            "total_tokens": 0,
            "total_duration": 0.0,
            "success": False,
            "error": None
        }

        # 创建对话保存目录
        self.conversations_dir = Path(output_dir) / "conversations" / project_name
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_test_generation_{self.class_name}_{self.method_name}_{self.conversation_id}.json"
        self.conversation_file = self.conversations_dir / filename

    def add_rag_context(self, contexts):
        """添加RAG检索上下文"""
        if contexts:
            self.rag_contexts = []
            for i, context in enumerate(contexts, 1):
                # RAG系统返回的字段名是'code'，需要转换为'content'
                content = context.get('code', context.get('content', ''))
                self.rag_contexts.append({
                    "index": i,
                    "content": content,
                    "metadata": context.get('metadata', {}),
                    "distance": context.get('distance', 0.0)
                })

    def add_error_enhanced_context(self, contexts, error_type="compilation"):
        """添加错误驱动增强的上下文"""
        if contexts:
            for i, context in enumerate(contexts, 1):
                enhanced_context = {
                    "index": len(self.error_enhanced_contexts) + 1,
                    "content": context.get('content', ''),
                    "metadata": context.get('metadata', {}),
                    "distance": context.get('distance', 0.0),
                    "error_type": error_type,
                    "enhancement_source": "error_driven"
                }
                self.error_enhanced_contexts.append(enhanced_context)

    def add_message(self, role, content, model=None, duration=None, tokens=None, metadata=None):
        """添加对话消息"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "model": model,
            "duration": duration,
            "tokens": tokens,
            "metadata": metadata or {}
        }
        self.messages.append(message)

    def update_metadata(self, success=None, error=None, total_duration=None, total_tokens=None):
        """更新元数据"""
        if success is not None:
            self.metadata["success"] = success
        if error is not None:
            self.metadata["error"] = error
        if total_duration is not None:
            self.metadata["total_duration"] = total_duration
        if total_tokens is not None:
            self.metadata["total_tokens"] = total_tokens

    def save_conversation(self):
        """保存对话到文件"""
        conversation_data = {
            "conversation_id": self.conversation_id,
            "conversation_type": "test_generation",
            "project_name": self.project_name,
            "target_class": self.class_name,
            "target_method": self.method_name,
            "test_style": self.test_style,
            "start_time": self.start_time,
            "rag_contexts": self.rag_contexts,
            "error_enhanced_contexts": self.error_enhanced_contexts,  # 新增：错误增强上下文
            "messages": self.messages,
            "metadata": self.metadata,
            "end_time": datetime.now().isoformat()
        }

        try:
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            return str(self.conversation_file)
        except Exception as e:
            print(f"保存对话失败: {e}")
            return None

class ConversationAwareTestGenerator:
    """带对话记录功能的测试生成器包装类"""

    def __init__(self, project_path, output_dir, debug=False, quiet=False):
        self.generator = ImprovedTestGenerator(project_path, output_dir, debug)
        self.project_path = project_path
        self.output_dir = output_dir
        self.debug = debug
        self.quiet = quiet  # 新增：控制输出的静默模式
        self.conversation_logger = None

    def generate_test_for_method(self, class_name, method_name, use_rag=True, test_style="comprehensive", max_fix_attempts=3, fix_strategy="both", force_reindex=False):
        """生成测试并记录对话"""
        # 提取项目名
        project_name = Path(self.project_path).name

        # 初始化对话记录器
        self.conversation_logger = ConversationLogger(
            project_name=project_name,
            class_name=class_name,
            method_name=method_name,
            test_style=test_style,
            output_dir=self.output_dir
        )

        start_time = time.time()

        try:
            # 设置错误上下文回调函数
            self.generator.set_error_context_callback(self.conversation_logger.add_error_enhanced_context)

            # 调用原始生成器，但拦截大模型调用
            result = self._generate_with_logging(class_name, method_name, use_rag, test_style, max_fix_attempts, fix_strategy, force_reindex)

            end_time = time.time()
            total_duration = end_time - start_time

            # 更新元数据
            self.conversation_logger.update_metadata(
                success=result.get('success', False),
                error=result.get('error'),
                total_duration=total_duration
            )

            # 保存对话
            conversation_file = self.conversation_logger.save_conversation()
            if conversation_file:
                if not self.quiet:
                    print(f"对话已保存: {Path(conversation_file).name}")
                # 在结果中添加对话文件路径
                result['conversation_file'] = conversation_file

            return result

        except Exception as e:
            # 记录异常
            self.conversation_logger.update_metadata(
                success=False,
                error=str(e),
                total_duration=time.time() - start_time
            )
            self.conversation_logger.save_conversation()
            raise

    def _generate_with_logging(self, class_name, method_name, use_rag, test_style, max_fix_attempts, fix_strategy, force_reindex=False):
        """带日志记录的生成过程"""
        # 保存原始的Ollama客户端方法
        original_call_unstructured = self.generator.ollama_client.call_unstructured

        def logged_call_unstructured(messages, model=None, is_code_task=True):
            """记录大模型调用的包装函数"""
            start_time = time.time()

            # 提取用户消息内容
            user_content = ""
            if messages and len(messages) > 0:
                user_content = messages[0].get('content', '')

            # 确定使用的模型
            actual_model = model or (self.generator.ollama_client.code_model if is_code_task else self.generator.ollama_client.non_code_model)

            # 记录用户消息
            self.conversation_logger.add_message(
                role="user",
                content=user_content,
                model=actual_model,
                duration=None,
                tokens=None,
                metadata={"is_code_task": is_code_task}
            )

            # 调用原始方法
            response = original_call_unstructured(messages, model, is_code_task)

            duration = time.time() - start_time

            # 记录助手响应
            self.conversation_logger.add_message(
                role="assistant",
                content=response,
                model=actual_model,
                duration=duration,
                tokens=None,
                metadata={}
            )

            return response

        # 保存原始的RAG方法
        original_get_rag_context = self.generator._get_rag_context_with_progress

        def logged_get_rag_context(*args, **kwargs):
            """记录RAG上下文的包装函数"""
            # 如果force_reindex没有在kwargs中，则添加它
            # 如果已经在args中（位置参数），则不要重复添加
            if len(args) < 4 and 'force_reindex' not in kwargs:
                kwargs['force_reindex'] = force_reindex
            result = original_get_rag_context(*args, **kwargs)
            # 立即记录RAG上下文
            if result and hasattr(self.generator, 'last_rag_contexts'):
                self.conversation_logger.add_rag_context(self.generator.last_rag_contexts)
            return result

        try:
            # 替换生成方法和RAG方法
            self.generator.ollama_client.call_unstructured = logged_call_unstructured
            self.generator._get_rag_context_with_progress = logged_get_rag_context

            # 执行原始生成过程
            result = self.generator.generate_test_for_method(
                class_name=class_name,
                method_name=method_name,
                use_rag=use_rag,
                test_style=test_style,
                max_fix_attempts=max_fix_attempts,
                fix_strategy=fix_strategy
            )

            return result

        finally:
            # 恢复原始方法
            self.generator.ollama_client.call_unstructured = original_call_unstructured
            self.generator._get_rag_context_with_progress = original_get_rag_context

    def get_statistics(self):
        """获取统计信息"""
        return self.generator.get_statistics()

    def cleanup(self):
        """清理资源"""
        return self.generator.cleanup()

def setup_logging(debug=False):
    """设置日志级别"""
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='LLM4TestGen - 智能测试生成系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本使用
  python main_test_generator.py --project ../pdfcompare --class com.example.Calculator --method add

  # 启用RAG和调试模式
  python main_test_generator.py -p ../myproject -c com.util.StringHelper -m isEmpty --rag --debug

  # 指定输出目录
  python main_test_generator.py --project ../pdfcompare --class com.example.pdfcompare.util.HashUtilityClass --method hashBytes --output ./my_tests

  # 不同的修复策略
  python main_test_generator.py --project ../pdfcompare --class com.example.Calculator --method add --fix-strategy compile-only
  python main_test_generator.py --project ../pdfcompare --class com.example.Calculator --method add --fix-strategy runtime-only
  python main_test_generator.py --project ../pdfcompare --class com.example.Calculator --method add --fix-strategy both

  # 不同的生成模式
  python main_test_generator.py --project ../pdfcompare --class com.example.Calculator --method add --generation-mode rag
  python main_test_generator.py --project ../pdfcompare --class com.example.Calculator --method add --generation-mode context-aware
  python main_test_generator.py --project ../pdfcompare --class com.example.Calculator --method add --generation-mode hybrid
        """
    )
    
    # 必需参数
    parser.add_argument(
        '--project', '-p',
        type=str,
        required=True,
        help='Java项目路径 (必需)'
    )
    
    parser.add_argument(
        '--class', '-c',
        type=str,
        required=True,
        dest='class_name',
        help='目标类的完全限定名 (必需)'
    )
    
    parser.add_argument(
        '--method', '-m',
        type=str,
        required=True,
        help='目标方法名 (必需)'
    )
    
    # 可选参数
    parser.add_argument(
        '--rag',
        action='store_true',
        default=True,
        help='启用RAG上下文检索 (默认: 启用)'
    )
    
    parser.add_argument(
        '--no-rag',
        action='store_true',
        help='禁用RAG上下文检索'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./generated_tests',
        help='测试输出目录 (默认: ./generated_tests)'
    )
    
    parser.add_argument(
        '--style', '-s',
        type=str,
        choices=['comprehensive', 'minimal', 'edge-case'],
        default='comprehensive',
        help='测试风格 (默认: comprehensive)'
    )
    
    parser.add_argument(
        '--max-attempts',
        type=int,
        default=3,
        help='最大修复尝试次数 (默认: 3)'
    )

    parser.add_argument(
        '--fix-strategy',
        type=str,
        choices=['compile-only', 'runtime-only', 'both'],
        default='both',
        help='修复策略: compile-only(仅修复编译错误), runtime-only(仅修复运行错误), both(两者都修复) (默认: both)'
    )

    parser.add_argument(
        '--generation-mode',
        type=str,
        choices=['rag', 'context-aware', 'hybrid'],
        default='rag',
        help='生成模式: rag(传统RAG模式), context-aware(上下文感知模式), hybrid(混合模式) (默认: rag)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式，显示详细信息'
    )

    parser.add_argument(
        '--force-reindex',
        action='store_true',
        help='强制重新索引项目（用于RAG上下文检索）'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，只显示结果'
    )
    
    return parser.parse_args()

def validate_arguments(args):
    """验证参数有效性"""
    errors = []
    
    # 检查项目路径
    project_path = Path(args.project)
    if not project_path.exists():
        errors.append(f"项目路径不存在: {project_path}")
    elif not project_path.is_dir():
        errors.append(f"项目路径不是目录: {project_path}")
    
    # 检查类名格式
    if not args.class_name or '.' not in args.class_name:
        errors.append(f"类名格式无效，需要完全限定名: {args.class_name}")
    
    # 检查方法名
    if not args.method or not args.method.isidentifier():
        errors.append(f"方法名格式无效: {args.method}")
    
    return errors

def print_header(args):
    """打印程序头部信息"""
    print("LLM4TestGen - 智能测试生成系统")
    print("=" * 60)
    print(f"项目路径: {args.project}")
    print(f"目标类: {args.class_name}")
    print(f"目标方法: {args.method}")
    print(f"RAG检索: {'启用' if (args.rag and not args.no_rag) else '禁用'}")
    print(f"生成模式: {args.generation_mode}")
    print(f"测试风格: {args.style}")
    print(f"输出目录: {args.output}")
    print(f"最大尝试: {args.max_attempts}")
    print(f"修复策略: {args.fix_strategy}")
    print(f"调试模式: {'启用' if args.debug else '禁用'}")
    print("=" * 60)

def check_method_body_extraction(generator, class_name, method_name):
    """检查是否成功提取了完整的方法体"""
    print("检查方法体提取...")

    try:
        # 导入解析器
        from source_analysis.simple_tree_sitter_parser import SimpleTreeSitterParser
        parser = SimpleTreeSitterParser()

        # 查找类文件
        class_file = None
        class_simple_name = class_name.split('.')[-1]

        for java_file in generator.project_path.rglob("*.java"):
            try:
                content = java_file.read_text(encoding='utf-8')
                # 更精确的类名匹配
                if (f"class {class_simple_name}" in content or
                    f"public class {class_simple_name}" in content or
                    f"final class {class_simple_name}" in content):
                    class_file = java_file
                    break
            except:
                continue

        if not class_file:
            print(f"   未找到类文件: {class_name}")
            return False

        print(f"   找到类文件: {class_file.name}")

        # 解析类文件
        parsed_class = parser.parse_java_file(str(class_file))
        if not parsed_class:
            print(f"   解析类文件失败: {class_file}")
            return False

        # 查找目标方法
        target_method = None
        for method in parsed_class.methods:
            if method.name == method_name:
                target_method = method
                break

        if not target_method:
            print(f"   未找到方法: {method_name}")
            available_methods = [m.name for m in parsed_class.methods]
            print(f"   可用方法: {', '.join(available_methods[:5])}")
            return False

        # 检查方法体
        method_body = target_method.body
        if not method_body or len(method_body.strip()) < 10:
            print(f"   方法体为空或过短: {len(method_body) if method_body else 0} 字符")
            return False

        print(f"   方法体提取成功: {len(method_body)} 字符")
        print(f"   方法签名: {target_method.signature}")
        print(f"   访问修饰符: {target_method.access_modifier}")

        # 显示方法体预览
        if not args.quiet:
            lines = method_body.split('\n')
            print(f"   方法体预览 (前5行):")
            for i, line in enumerate(lines[:5], 1):
                print(f"      {i:2d}: {line}")
            if len(lines) > 5:
                print(f"      ... 还有 {len(lines) - 5} 行")

        return True

    except Exception as e:
        print(f"   检查方法体时出错: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return False

def analyze_test_errors(result):
    """分析测试运行错误类型"""
    print("测试错误分析:")

    if result.get('success'):
        print("   测试生成成功，无错误")
        return

    error_msg = result.get('error', 'Unknown error')
    attempts = result.get('attempts', 0)

    # 分析错误类型
    error_types = []

    if "编译" in error_msg or "compilation" in error_msg.lower():
        error_types.append("编译错误")

    if "依赖" in error_msg or "dependency" in error_msg.lower():
        error_types.append("依赖问题")

    if "Maven" in error_msg or "maven" in error_msg.lower():
        error_types.append("Maven配置问题")

    if "JUnit" in error_msg or "junit" in error_msg.lower():
        error_types.append("JUnit依赖问题")

    if "类路径" in error_msg or "classpath" in error_msg.lower():
        error_types.append("类路径问题")

    if "方法体" in error_msg or "method body" in error_msg.lower():
        error_types.append("方法体提取问题")

    if "RAG" in error_msg or "上下文" in error_msg:
        error_types.append("RAG上下文问题")

    if "大模型" in error_msg or "LLM" in error_msg or "model" in error_msg.lower():
        error_types.append("大模型调用问题")

    if "超时" in error_msg or "timeout" in error_msg.lower():
        error_types.append("超时问题")

    if "运行时" in error_msg or "runtime" in error_msg.lower():
        error_types.append("运行时错误")

    if "断言" in error_msg or "assertion" in error_msg.lower():
        error_types.append("测试断言失败")

    if "空指针" in error_msg or "nullpointer" in error_msg.lower():
        error_types.append("空指针异常")

    if not error_types:
        error_types.append("未知错误类型")

    print(f"   错误类型: {', '.join(error_types)}")
    print(f"   尝试次数: {attempts}")
    print(f"   错误详情: {error_msg}")

    # 提供解决建议
    print("   解决建议:")
    if "编译错误" in error_types:
        print("      - 检查Java项目是否可以正常编译")
        print("      - 确认JUnit 5依赖已正确配置")

    if "依赖问题" in error_types or "Maven配置问题" in error_types:
        print("      - 运行 'mvn clean compile test-compile' 检查项目状态")
        print("      - 确认pom.xml中包含JUnit 5依赖")

    if "方法体提取问题" in error_types:
        print("      - 检查类名和方法名是否正确")
        print("      - 确认方法是public且非abstract")

    if "RAG上下文问题" in error_types:
        print("      - 尝试使用 --no-rag 禁用RAG功能")
        print("      - 检查项目结构是否完整")

    if "大模型调用问题" in error_types:
        print("      - 确认Ollama服务正在运行")
        print("      - 检查模型是否已正确安装")

    if "超时问题" in error_types:
        print("      - 增加 --max-attempts 参数值")
        print("      - 检查网络连接和系统性能")

    if "运行时错误" in error_types:
        print("      - 尝试使用 --fix-strategy runtime-only 专门修复运行时问题")
        print("      - 检查测试逻辑和业务代码的匹配性")

    if "测试断言失败" in error_types:
        print("      - 检查测试的期望值是否正确")
        print("      - 使用 --fix-strategy runtime-only 修复断言问题")

    if "空指针异常" in error_types:
        print("      - 检查mock对象的初始化")
        print("      - 确保所有依赖都正确注入")

    if "未知错误类型" in error_types:
        print("      - 启用调试模式查看详细信息: --debug")
        print("      - 检查系统日志和错误堆栈")
        print("      - 尝试不同的修复策略: --fix-strategy both")

def generate_with_context_aware(generator, args):
    """使用Context-Aware生成器生成测试"""
    try:
        # 调用Context-Aware生成器
        ca_result = generator.generate_test(
            target_class_fqn=args.class_name,
            target_method_name=args.method,
            force_reindex=getattr(args, 'force_reindex', False),
            max_fix_attempts=args.max_attempts
        )

        # 转换结果格式以兼容原有的结果处理逻辑
        context_data = ca_result.get('context', {})
        if hasattr(context_data, 'dependency_contexts'):
            context_count = len(context_data.dependency_contexts)
        else:
            context_count = len(context_data.get('dependency_contexts', []))

        result = {
            'success': ca_result['success'],
            'method_signature': f"{args.class_name}.{args.method}",
            'context_used': context_count,
            'attempts': args.max_attempts,
            'test_file_path': None,
            'conversation_file': None
        }

        # 查找生成的测试文件
        output_dir = Path(args.output)
        if output_dir.exists():
            class_simple_name = args.class_name.split('.')[-1]
            test_files = list(output_dir.glob(f"{class_simple_name}_{args.method}_Test.java"))
            if test_files:
                result['test_file_path'] = str(test_files[0])

        # 如果是混合模式且Context-Aware失败，回退到RAG
        if args.generation_mode == 'hybrid' and not ca_result['success']:
            if not args.quiet:
                print("Context-Aware模式失败，回退到RAG模式...")

            # 创建RAG生成器
            rag_generator = ConversationAwareTestGenerator(
                project_path=Path(args.project),
                output_dir=Path(args.output),
                debug=args.debug
            )

            # 使用RAG模式重新生成
            use_rag = args.rag and not args.no_rag
            rag_result = rag_generator.generate_test_for_method(
                class_name=args.class_name,
                method_name=args.method,
                use_rag=use_rag,
                test_style=args.style,
                max_fix_attempts=args.max_attempts,
                fix_strategy=args.fix_strategy,
                force_reindex=getattr(args, 'force_reindex', False)
            )

            # 如果RAG成功，使用RAG结果
            if rag_result['success']:
                result = rag_result
                result['generation_mode_used'] = 'rag_fallback'
            else:
                result['generation_mode_used'] = 'hybrid_failed'
        else:
            result['generation_mode_used'] = 'context_aware'

        return result

    except Exception as e:
        if not args.quiet:
            print(f"Context-Aware生成失败: {e}")

        # 如果是混合模式，尝试RAG回退
        if args.generation_mode == 'hybrid':
            if not args.quiet:
                print("尝试RAG模式回退...")

            try:
                rag_generator = ConversationAwareTestGenerator(
                    project_path=Path(args.project),
                    output_dir=Path(args.output),
                    debug=args.debug
                )

                use_rag = args.rag and not args.no_rag
                return rag_generator.generate_test_for_method(
                    class_name=args.class_name,
                    method_name=args.method,
                    use_rag=use_rag,
                    test_style=args.style,
                    max_fix_attempts=args.max_attempts,
                    fix_strategy=args.fix_strategy,
                    force_reindex=getattr(args, 'force_reindex', False)
                )
            except Exception as rag_e:
                if not args.quiet:
                    print(f"RAG回退也失败: {rag_e}")

        # 返回失败结果
        return {
            'success': False,
            'method_signature': f"{args.class_name}.{args.method}",
            'context_used': 0,
            'attempts': 0,
            'error': str(e),
            'generation_mode_used': 'failed'
        }

def main():
    """主函数"""
    global args  # 让其他函数可以访问args
    
    # 解析参数
    args = parse_arguments()
    
    # 设置日志
    setup_logging(args.debug)
    
    # 验证参数
    errors = validate_arguments(args)
    if errors:
        print("参数验证失败:")
        for error in errors:
            print(f"   {error}")
        sys.exit(1)
    
    # 打印头部信息
    if not args.quiet:
        print_header(args)
    
    # 确定RAG设置
    use_rag = args.rag and not args.no_rag
    
    try:
        # 根据生成模式选择生成器
        if not args.quiet:
            print("初始化组件...")

        # 统一使用ImprovedTestGenerator，通过context_mode参数控制上下文获取方式
        generator = ImprovedTestGenerator(
            project_path=Path(args.project),
            output_dir=Path(args.output),
            debug=args.debug
        )

        if args.generation_mode == 'context-aware':
            generator_type = "Context-Aware"
        elif args.generation_mode == 'hybrid':
            generator_type = "Hybrid (Context-Aware + RAG)"
        else:
            generator_type = "RAG"

        if not args.quiet:
            print("组件初始化完成")
            print(f"生成器配置:")
            print(f"   生成器类型: {generator_type}")
            print(f"   Tree-sitter: 可用")
            print(f"   编译管理器: 改进版Maven支持")
            print(f"   RAG系统: {'启用' if use_rag else '禁用'}")
            print(f"   调试模式: {'启用' if args.debug else '禁用'}")
            print(f"   输出目录: {args.output}")

        # 检查方法体提取（仅对RAG模式）
        if args.generation_mode == 'rag' and not args.quiet:
            method_body_ok = check_method_body_extraction(generator, args.class_name, args.method)
            if not method_body_ok:
                print("方法体提取可能存在问题，但继续执行...")

        # 执行测试生成
        if not args.quiet:
            print(f"\n" + "="*60)
            print("开始生成测试")

        start_time = time.time()

        # 根据生成模式设置context_mode
        if args.generation_mode == 'context-aware':
            context_mode = 'context-aware'
        elif args.generation_mode == 'hybrid':
            # 混合模式：先尝试context-aware，失败时在内部回退到rag
            context_mode = 'context-aware'
        else:
            context_mode = 'rag'

        # 统一调用ImprovedTestGenerator
        result = generator.generate_test_for_method(
            class_name=args.class_name,
            method_name=args.method,
            use_rag=use_rag,
            test_style=args.style,
            max_fix_attempts=args.max_attempts,
            fix_strategy=args.fix_strategy,
            force_reindex=getattr(args, 'force_reindex', False),
            context_mode=context_mode
        )
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 显示结果摘要
        if not args.quiet:
            print(f"\n" + "="*60)
            print("生成结果摘要")

        success_icon = "" if result['success'] else ""
        print(f"{success_icon} 状态: {'成功' if result['success'] else '失败'}")
        print(f"总耗时: {total_duration:.2f} 秒")
        print(f"生成模式: {args.generation_mode}")

        # 显示实际使用的生成模式
        if 'actual_mode_used' in result:
            actual_mode = result['actual_mode_used']
            if args.generation_mode == 'hybrid':
                if actual_mode == 'context-aware':
                    print(f"实际使用: Context-Aware模式")
                elif actual_mode == 'rag':
                    print(f"实际使用: RAG模式 (Context-Aware回退)")
            elif args.generation_mode == 'context-aware':
                if actual_mode == 'context-aware':
                    print(f"实际使用: Context-Aware模式")
                elif actual_mode == 'rag':
                    print(f"实际使用: RAG模式 (回退)")
            else:
                print(f"实际使用: RAG模式")
        elif 'generation_mode_used' in result:
            # 兼容旧版本
            mode_used = result['generation_mode_used']
            if mode_used == 'rag_fallback':
                print(f"实际使用: RAG模式 (Context-Aware回退)")
            elif mode_used == 'context_aware':
                print(f"实际使用: Context-Aware模式")
            elif mode_used == 'hybrid_failed':
                print(f"混合模式: 两种模式都失败")

        print(f"上下文数量: {result.get('context_used', 0)} 个")
        print(f"方法签名: {result.get('method_signature', 'N/A')}")

        # 获取测试文件路径（无论成功失败都可能存在）
        test_file = result.get('test_file_path')

        if result['success']:
            print(f"测试文件: {Path(test_file).name if test_file else 'N/A'}")
            print(f"编译尝试: {result.get('attempts', 'N/A')} 次")

        # 显示对话文件信息
        conversation_file = result.get('conversation_file')
        if conversation_file:
            print(f"对话记录: {Path(conversation_file).name}")

            # 显示生成的测试代码片段（只在成功且有文件时显示）
            if result['success'] and test_file and Path(test_file).exists() and not args.quiet:
                content = Path(test_file).read_text(encoding='utf-8')
                lines = content.split('\n')
                print(f"\n生成的测试代码预览:")
                print("```java")
                for i, line in enumerate(lines[:15], 1):  # 显示前15行
                    print(f"{i:2d}: {line}")
                if len(lines) > 15:
                    print(f"... 还有 {len(lines) - 15} 行")
                print("```")
        
        # 分析错误类型
        if not result['success']:
            analyze_test_errors(result)
        
        # 显示统计信息
        if not args.quiet:
            try:
                if hasattr(generator, 'get_statistics'):
                    stats = generator.get_statistics()['generator_stats']
                    print(f"\n统计信息:")
                    print(f"   分析的方法: {stats['analyzed_methods']}")
                    print(f"   成功生成: {stats['generated_tests']}")
                    print(f"   失败生成: {stats['failed_generations']}")
                    print(f"   上下文检索: {stats['context_retrievals']}")
                elif hasattr(generator, 'get_project_statistics'):
                    stats = generator.get_project_statistics()
                    print(f"\n项目统计:")
                    print(f"   类数量: {stats['classes']}")
                    print(f"   方法数量: {stats['methods']}")
                    print(f"   构造器数量: {stats['constructors']}")
                    print(f"   字段数量: {stats['fields']}")
                    if 'fix_attempts' in stats:
                        print(f"   修复尝试: {stats['fix_attempts']}")
            except Exception as e:
                if args.debug:
                    print(f"统计信息获取失败: {e}")

        # 清理
        if hasattr(generator, 'cleanup'):
            generator.cleanup()

        # 最终状态
        if not args.quiet:
            print(f"\n" + "="*60)

        if result['success']:
            print("测试生成成功完成！")
            if not args.quiet:
                print(f"测试文件已保存到: {args.output}")
            sys.exit(0)
        else:
            print("测试生成未完全成功")
            if not args.quiet:
                print("请检查上述错误分析和建议")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"运行失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
