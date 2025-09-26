#!/usr/bin/env python3
"""
改进的测试生成器
包含完整方法体提取、进度显示和调试信息
"""

import sys
import logging
import time
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config.remote_ollama_config import remote_config
from rag.project_analyzer import SmartProjectAnalyzer
from source_analysis.simple_tree_sitter_parser import SimpleTreeSitterParser
from utils.improved_compilation_manager import ImprovedCompilationManager
from utils.execution_manager import ExecutionManager
from llm.ollama_client import OllamaClient
from prompting.enhanced_test_prompt import EnhancedTestPrompt

logger = logging.getLogger(__name__)

class ImprovedTestGenerator:
    """改进的测试生成器"""
    
    def __init__(self, project_path: Path, output_dir: Path = None, debug: bool = False):
        """
        初始化改进测试生成器
        
        Args:
            project_path: 项目根路径
            output_dir: 输出目录
            debug: 是否启用调试模式
        """
        self.project_path = Path(project_path)
        self.output_dir = Path(output_dir) if output_dir else self.project_path / "generated_tests"
        self.output_dir.mkdir(exist_ok=True)
        self.debug = debug
        
        # 初始化组件
        print("初始化组件...")
        self.project_analyzer = SmartProjectAnalyzer(self.project_path)
        self.tree_sitter_parser = SimpleTreeSitterParser()
        self.compilation_manager = ImprovedCompilationManager(self.project_path)

        # 初始化Context-Aware生成器（用于错误驱动的上下文增强）
        from context_aware.context_generator import ContextAwareGenerator
        self.context_generator = ContextAwareGenerator(str(self.project_path))

        # 初始化执行管理器
        self.execution_manager = ExecutionManager(
            project_path=self.project_path,
            is_maven_project=self.compilation_manager.is_maven_project
        )
        
        # 初始化Ollama客户端
        self.ollama_client = OllamaClient(
            base_url=remote_config.get_base_url(),
            code_model=remote_config.get_code_model(),
            non_code_model=remote_config.get_fix_model(),
            timeout=remote_config.get_request_timeout()
        )
        
        # 统计信息
        self.stats = {
            'analyzed_methods': 0,
            'generated_tests': 0,
            'failed_generations': 0,
            'compilation_successes': 0,
            'compilation_failures': 0,
            'runtime_successes': 0,
            'runtime_failures': 0,
            'context_retrievals': 0,
            'fix_attempts': 0
        }

        # 存储最后一次的RAG上下文，用于对话记录
        self.last_rag_contexts = []

        # 存储错误增强的上下文，用于对话记录
        self.error_enhanced_contexts = []

        # 错误增强上下文回调函数
        self.error_context_callback = None
        
        print("组件初始化完成")

    def set_error_context_callback(self, callback):
        """设置错误增强上下文回调函数"""
        self.error_context_callback = callback
    
    def generate_test_for_method(self, class_name: str, method_name: str,
                               use_rag: bool = True, test_style: str = "comprehensive",
                               max_fix_attempts: int = 3, fix_strategy: str = "both",
                               force_reindex: bool = False,
                               context_mode: str = "rag") -> Dict[str, Any]:
        """
        为指定方法生成测试

        Args:
            class_name: 类名 (如 com.example.Calculator)
            method_name: 方法名
            use_rag: 是否使用RAG技术增强上下文
            test_style: 测试风格
            max_fix_attempts: 最大修复尝试次数
            fix_strategy: 修复策略 ('compile-only', 'runtime-only', 'both')
            context_mode: 上下文模式 ('rag', 'context-aware')

        Returns:
            生成结果
        """
        start_time = time.time()
        method_signature = f"{class_name}#{method_name}"

        # 初始化完整会话记录
        session_id = str(uuid.uuid4())[:8]
        session_record = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "target_class": class_name,
            "target_method": method_name,
            "method_signature": method_signature,
            "generation_mode": context_mode,
            "config": {
                "use_rag": use_rag,
                "test_style": test_style,
                "max_fix_attempts": max_fix_attempts,
                "fix_strategy": fix_strategy,
                "force_reindex": force_reindex
            },
            "steps": [],
            "context_data": {},  # 存储检索到的上下文
            "llm_conversations": [],  # 存储所有LLM对话
            "conversation_files": [],  # 保持向后兼容
            "errors": [],
            "final_result": None
        }

        # 初始化会话级别的对话收集器
        self.current_session_conversations = []

        print(f"\n开始为 {method_signature} 生成测试")
        print(f"配置: RAG={use_rag}, 风格={test_style}, 最大修复次数={max_fix_attempts}")
        print(f"会话ID: {session_id}")

        try:
            # 步骤1: 分析目标方法
            print("步骤1: 分析目标方法...")
            method_info = self._analyze_target_method_with_body(class_name, method_name)
            if not method_info:
                return self._create_error_result(method_signature, "无法分析目标方法", start_time)

            print(f"   找到方法: {method_info['signature']}")
            print(f"   方法体长度: {len(method_info.get('method_body', ''))} 字符")
            
            # 步骤2: 获取上下文（RAG或Context-Aware）
            context_info = []
            actual_mode_used = context_mode

            if context_mode == "context-aware":
                print(" 步骤2: 获取Context-Aware上下文...")
                step_start = time.time()
                context_info = self._get_context_aware_context(class_name, method_name, method_info, force_reindex)
                if context_info:
                    self.stats['context_retrievals'] += 1
                    print(f"    构建Context-Aware上下文完成")
                    session_record["steps"].append({
                        "step": "context_retrieval",
                        "mode": "context-aware",
                        "success": True,
                        "context_count": len(context_info),
                        "duration": time.time() - step_start
                    })
                else:
                    print("     Context-Aware上下文获取失败，回退到RAG模式...")
                    actual_mode_used = "rag"
                    session_record["steps"].append({
                        "step": "context_retrieval",
                        "mode": "context-aware",
                        "success": False,
                        "fallback_to": "rag",
                        "duration": time.time() - step_start
                    })
                    if use_rag:
                        context_info = self._get_rag_context_with_progress(method_signature, method_name, method_info, force_reindex)
                        self.stats['context_retrievals'] += 1
                        print(f"    RAG回退成功，找到 {len(context_info)} 个相关上下文")
                        session_record["steps"].append({
                            "step": "context_retrieval_fallback",
                            "mode": "rag",
                            "success": True,
                            "context_count": len(context_info),
                            "duration": time.time() - step_start
                        })
            elif use_rag:
                print(" 步骤2: 获取RAG上下文...")
                step_start = time.time()
                context_info = self._get_rag_context_with_progress(method_signature, method_name, method_info, force_reindex)
                self.stats['context_retrievals'] += 1
                print(f"    找到 {len(context_info)} 个相关上下文")
                session_record["steps"].append({
                    "step": "context_retrieval",
                    "mode": "rag",
                    "success": True,
                    "context_count": len(context_info),
                    "duration": time.time() - step_start
                })
            else:
                print("  步骤2: 跳过上下文获取")
                session_record["steps"].append({
                    "step": "context_retrieval",
                    "mode": "none",
                    "success": True,
                    "context_count": 0,
                    "duration": 0
                })
            
            # 步骤3: 生成初始测试代码
            print(" 步骤3: 生成初始测试代码...")
            initial_test = self._generate_initial_test_with_debug(method_info, context_info, test_style)
            if not initial_test:
                return self._create_error_result(method_signature, "初始测试代码生成失败", start_time)
            
            print(f"    生成测试代码，长度: {len(initial_test)} 字符")
            
            # 步骤4: 编译和修复循环
            print(" 步骤4: 编译和修复循环...")
            final_result = self._compile_and_fix_loop_with_progress(
                initial_test, method_info, context_info, max_fix_attempts, fix_strategy
            )
            
            # 步骤5: 保存结果
            if final_result['success']:
                print(" 步骤5: 保存测试文件...")
                test_file_path = self._save_test_file(class_name, method_name, final_result['code'])
                final_result['test_file_path'] = str(test_file_path)
                self.stats['generated_tests'] += 1
                self.stats['compilation_successes'] += 1
                print(f"    测试文件已保存: {test_file_path.name}")
            else:
                self.stats['failed_generations'] += 1
                self.stats['compilation_failures'] += 1
                print(f"    测试生成失败: {final_result.get('error', 'Unknown error')}")
            
            final_result.update({
                'method_signature': method_signature,
                'context_used': len(context_info),
                'rag_enabled': use_rag,
                'context_mode': context_mode,
                'actual_mode_used': actual_mode_used,
                'total_duration': time.time() - start_time
            })

            # 完成会话记录并保存
            session_record["end_time"] = datetime.now().isoformat()
            session_record["total_duration"] = time.time() - start_time
            session_record["final_result"] = final_result
            session_record["success"] = final_result.get('success', False)

            # 添加上下文数据
            if context_info:
                session_record["context_data"] = {
                    "context_type": actual_mode_used,
                    "context_count": len(context_info),
                    "contexts": context_info
                }

            # 添加所有LLM对话
            if hasattr(self, 'current_session_conversations'):
                session_record["llm_conversations"] = self.current_session_conversations

            self._save_complete_session(session_record, class_name, method_name)

            self.stats['analyzed_methods'] += 1
            return final_result
            
        except Exception as e:
            logger.error(f"测试生成异常: {e}")
            self.stats['failed_generations'] += 1
            return self._create_error_result(method_signature, str(e), start_time, use_rag)
    
    def _analyze_target_method_with_body(self, class_name: str, method_name: str) -> Optional[Dict[str, Any]]:
        """分析目标方法并提取完整方法体"""
        try:
            # 查找类文件
            class_file = self._find_class_file(class_name)
            if not class_file:
                print(f"    未找到类文件: {class_name}")
                return None
            
            print(f"   找到类文件: {class_file.name}")
            
            # 使用Tree-sitter解析
            if self.tree_sitter_parser.is_available():
                parsed_class = self.tree_sitter_parser.parse_java_file(class_file)
                if parsed_class:
                    # 查找目标方法
                    for method in parsed_class.methods:
                        if method.name == method_name:
                            return {
                                'name': method.name,
                                'signature': method.signature,
                                'access_modifier': method.access_modifier,
                                'return_type': self._extract_return_type(method.signature),
                                'parameters': self._extract_parameters(method.signature),
                                'class_name': class_name.split('.')[-1],
                                'package': parsed_class.package,
                                'method_body': method.body  # 完整的方法体
                            }
            
            # 回退到简单分析
            print(f"     使用简单分析模式")
            return {
                'name': method_name,
                'signature': f"public String {method_name}()",
                'class_name': class_name.split('.')[-1],
                'package': '.'.join(class_name.split('.')[:-1]) if '.' in class_name else None,
                'method_body': 'Method body not available'
            }
            
        except Exception as e:
            print(f"    分析方法失败: {e}")
            return None

    def _get_context_aware_context(self, class_name: str, method_name: str, method_info: Dict, force_reindex: bool = False) -> List[Dict]:
        """获取Context-Aware上下文"""
        try:
            # 导入Context-Aware组件
            from context_aware.static_analyzer import JavaStaticAnalyzer
            from context_aware.project_index import ProjectIndexDatabase
            from context_aware.context_generator import ContextAwareGenerator

            # 初始化组件
            analyzer = JavaStaticAnalyzer(str(self.project_path))
            # context_generator 已在 __init__ 中初始化
            db = self.context_generator.db

            # 分析项目（如果需要）
            if force_reindex or not db.has_data():
                print("    分析项目结构...")
                try:
                    analysis_result = analyzer.analyze_project(str(self.project_path))
                    print(f"    项目统计: {analysis_result['files_processed']} 个文件, {analysis_result['methods_found']} 个方法")
                except Exception as e:
                    print(f"    项目分析失败: {e}")
                    return []

            # 生成Context-Aware上下文
            print("    生成Context-Aware上下文...")
            try:
                # 确保使用完全限定类名
                target_class_fqn = class_name if '.' in class_name else f"com.example.{class_name}"
                context = self.context_generator.generate_context(target_class_fqn, method_name)
                # 使用新的格式化方法
                context_info = self.context_generator.format_for_prompt(context)
            except Exception as e:
                print(f"    Context-Aware上下文生成失败: {e}")
                print(f"    调试信息: class_name={class_name}, method_name={method_name}")
                return []

            # 不再单独保存Context-Aware上下文，只在完整会话中保存

            return context_info

        except Exception as e:
            logger.error(f"Context-Aware上下文生成失败: {e}")
            print(f"    Context-Aware上下文生成失败: {e}")
            return []

    def _save_context_aware_context(self, class_name: str, method_name: str, context, context_info: List[Dict]):
        """保存Context-Aware上下文到JSON文件（匹配RAG格式）"""
        try:
            # 显示检索到的上下文
            print(f"    检索到的Context-Aware上下文:")
            for i, ctx in enumerate(context_info, 1):
                ctx_type = ctx['metadata'].get('type', 'unknown')
                print(f"      {i}. {ctx_type}")
                if ctx_type == 'core_context':
                    print(f"         - 目标类: {ctx['metadata'].get('class_name', 'N/A')}")
                    print(f"         - 目标方法: {ctx['metadata'].get('method_name', 'N/A')}")
                elif ctx_type == 'dependency_context':
                    print(f"         - 依赖类: {ctx['metadata'].get('dependency_fqn', 'N/A')}")
                    print(f"         - 依赖类型: {ctx['metadata'].get('dependency_type', 'N/A')}")
                elif ctx_type == 'imports':
                    print(f"         - 导入数量: {ctx['metadata'].get('import_count', 0)}")

            # 创建conversations目录结构（匹配RAG格式）
            conversations_dir = self.output_dir / "conversations" / "pdfcompare"
            conversations_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名（匹配RAG格式）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conversation_id = str(uuid.uuid4())[:8]
            safe_class_name = class_name.split('.')[-1]
            filename = f"{timestamp}_context_aware_context_{safe_class_name}_{method_name}_{conversation_id}.json"
            context_path = conversations_dir / filename

            # 转换Context-Aware上下文为RAG格式
            context_aware_contexts = []
            for i, ctx in enumerate(context_info, 1):
                context_aware_contexts.append({
                    "index": i,
                    "content": ctx.get('content', ''),
                    "metadata": ctx.get('metadata', {}),
                    "distance": ctx.get('distance', 0.0)
                })

            # 构建JSON数据（匹配RAG格式）
            context_data = {
                "conversation_id": conversation_id,
                "conversation_type": "context_aware_context",
                "project_name": "pdfcompare",
                "target_class": safe_class_name,
                "target_method": method_name,
                "generation_mode": "context-aware",
                "start_time": datetime.now().isoformat(),
                "context_aware_contexts": context_aware_contexts,
                "context_summary": {
                    "target_class_fqn": getattr(context.core_context, 'target_class_fqn', class_name),
                    "target_method_signature": getattr(context.core_context, 'target_method_signature', method_name),
                    "project_group_id": getattr(context, 'project_group_id', 'N/A'),
                    "available_constructors": getattr(context.core_context, 'target_class_constructors', []),
                    "related_fields": getattr(context.core_context, 'target_class_fields', []),
                    "called_internal_methods": getattr(context.core_context, 'called_internal_methods', []),
                    "dependency_contexts": [
                        {
                            "dependency_fqn": getattr(dep, 'dependency_fqn', 'N/A'),
                            "dependency_type": getattr(dep, 'dependency_type', 'N/A'),
                            "instantiation_guide": getattr(dep, 'instantiation_guide', 'N/A')
                        } for dep in getattr(context, 'dependency_contexts', [])
                    ],
                    "import_statements": getattr(context, 'import_statements', [])
                },
                "metadata": {
                    "total_contexts": len(context_info),
                    "context_types": [ctx['metadata'].get('type', 'unknown') for ctx in context_info],
                    "total_content_length": sum(len(ctx.get('content', '')) for ctx in context_info)
                },
                "end_time": datetime.now().isoformat()
            }

            # 保存JSON文件
            with open(context_path, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)

            print(f"    Context-Aware上下文已保存: {filename}")

            # 同时保存到会话记录中
            if hasattr(self, 'current_session_conversations'):
                self.current_session_conversations.append(context_data)

        except Exception as e:
            logger.warning(f"保存Context-Aware上下文失败: {e}")
            print(f"     保存Context-Aware上下文失败: {e}")

    def _save_llm_conversation(self, method_info: Dict, prompt: str, response: str,
                              conversation_type: str, context_info: List[Dict] = None,
                              original_context_count: int = 4):
        """保存与大模型的对话到JSON文件（匹配RAG格式）"""
        try:
            # 创建conversations目录结构（匹配RAG格式）
            conversations_dir = self.output_dir / "conversations" / "pdfcompare"
            conversations_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名（匹配RAG格式）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conversation_id = str(uuid.uuid4())[:8]
            safe_class_name = method_info['class_name'].split('.')[-1]
            method_name = method_info['name']
            filename = f"{timestamp}_{conversation_type}_{safe_class_name}_{method_name}_{conversation_id}.json"
            conversation_path = conversations_dir / filename

            # 转换Context-Aware上下文为RAG格式，并标记错误增强上下文
            context_aware_contexts = []
            error_enhanced_contexts = []
            if context_info:
                for i, ctx in enumerate(context_info, 1):
                    context_entry = {
                        "index": i,
                        "content": ctx.get('content', ''),
                        "metadata": ctx.get('metadata', {}),
                        "distance": ctx.get('distance', 0.0)
                    }
                    context_aware_contexts.append(context_entry)

                    # 如果这是错误增强的上下文（索引超过原始上下文数量）
                    if i > original_context_count:
                        enhanced_context = context_entry.copy()
                        enhanced_context.update({
                            "error_type": "compilation" if "compile" in conversation_type else "runtime",
                            "enhancement_source": "error_driven"
                        })
                        error_enhanced_contexts.append(enhanced_context)

            # 构建对话消息
            messages = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "role": "user",
                    "content": prompt,
                    "model": None,
                    "duration": None,
                    "tokens": None,
                    "metadata": {}
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "role": "assistant",
                    "content": response,
                    "model": "qwen3:8b",
                    "duration": None,
                    "tokens": None,
                    "metadata": {}
                }
            ]

            # 构建JSON数据（匹配RAG格式，包含错误增强上下文）
            conversation_data = {
                "conversation_id": conversation_id,
                "conversation_type": conversation_type,
                "project_name": "pdfcompare",
                "target_class": safe_class_name,
                "target_method": method_name,
                "test_style": "comprehensive",
                "generation_mode": "context-aware",
                "start_time": datetime.now().isoformat(),
                "context_aware_contexts": context_aware_contexts,
                "error_enhanced_contexts": error_enhanced_contexts,  # 新增：错误增强上下文
                "messages": messages,
                "metadata": {
                    "total_tokens": 0,
                    "total_duration": 0.0,
                    "success": True,
                    "error": None,
                    "prompt_length": len(prompt),
                    "response_length": len(response),
                    "context_count": len(context_info) if context_info else 0,
                    "error_enhanced_count": len(error_enhanced_contexts)  # 新增：错误增强上下文数量
                },
                "end_time": datetime.now().isoformat()
            }

            # 保存JSON文件
            with open(conversation_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            print(f"    LLM对话已保存: {filename}")

            # 同时保存到会话记录中
            if hasattr(self, 'current_session_conversations'):
                self.current_session_conversations.append(conversation_data)

        except Exception as e:
            logger.warning(f"保存LLM对话失败: {e}")
            print(f"     保存LLM对话失败: {e}")

    def _save_complete_session(self, session_record: Dict, class_name: str, method_name: str):
        """保存完整的会话记录到JSON文件，包含失败分析"""
        try:
            # 添加失败分析
            if not session_record.get('success', True):
                session_record['failure_analysis'] = self._analyze_failure_reasons(session_record)

            # 创建sessions目录结构
            sessions_dir = self.output_dir / "sessions" / "pdfcompare"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_class_name = class_name.split('.')[-1]
            filename = f"{timestamp}_complete_session_{safe_class_name}_{method_name}_{session_record['session_id']}.json"
            session_path = sessions_dir / filename

            # 保存JSON文件
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_record, f, indent=2, ensure_ascii=False)

            print(f"    完整会话已保存: {filename}")

        except Exception as e:
            logger.warning(f"保存完整会话失败: {e}")
            print(f"     保存完整会话失败: {e}")

    def _analyze_failure_reasons(self, session_record: Dict) -> Dict:
        """分析失败原因"""
        analysis = {
            "context_issues": [],
            "prompt_issues": [],
            "llm_response_issues": [],
            "compilation_issues": [],
            "recommendations": []
        }

        # 分析上下文问题
        context_data = session_record.get("context_data", {})
        if context_data and context_data.get("contexts"):
            contexts = context_data["contexts"]

            # 检查@UtilityClass检测
            utility_class_detected = False
            component_annotation_found = False

            for ctx in contexts:
                content = ctx.get("content", "")
                if "@UtilityClass" in content:
                    utility_class_detected = True
                if "@Component" in content or "@RequiredArgsConstructor" in content:
                    component_annotation_found = True

            if utility_class_detected and component_annotation_found:
                analysis["context_issues"].append("矛盾的类注解信息：同时检测到@UtilityClass和@Component/@RequiredArgsConstructor")
                analysis["recommendations"].append("修复类注解检测逻辑，确保正确识别@UtilityClass")

            # 检查格式化标记
            for ctx in contexts:
                content = ctx.get("content", "")
                if "## 核心代码区" in content or "## 类注解信息" in content:
                    analysis["context_issues"].append("上下文包含格式化标记，应该使用简洁格式")
                    analysis["recommendations"].append("移除上下文中的格式化标记，使用与RAG模式一致的简洁格式")
                    break

        # 分析LLM响应问题
        llm_conversations = session_record.get("llm_conversations", [])
        for conv in llm_conversations:
            if conv.get("conversation_type") == "initial_generation":
                messages = conv.get("messages", [])
                for msg in messages:
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "")
                        if "new ImageComparator()" in content:
                            analysis["llm_response_issues"].append("LLM生成了@UtilityClass的实例化代码")
                            analysis["recommendations"].append("增强prompt中@UtilityClass的指导信息")
                        if "import com.example.pdfcompare.util.ImageChunk;" in content:
                            analysis["llm_response_issues"].append("LLM使用了错误的导入路径")
                            analysis["recommendations"].append("提供正确的导入语句信息")

        # 分析编译问题
        final_result = session_record.get("final_result", {})
        if final_result.get("last_error"):
            error_msg = final_result["last_error"]
            if "找不到符号" in error_msg:
                analysis["compilation_issues"].append("编译错误：找不到符号，可能是导入路径错误")
                analysis["recommendations"].append("检查并修复导入语句的包路径")
            if "非法的表达式开始" in error_msg:
                analysis["compilation_issues"].append("编译错误：语法错误，可能是代码生成不完整")
                analysis["recommendations"].append("改进LLM代码生成的完整性检查")

        return analysis

    def _get_rag_context_with_progress(self, method_signature: str, method_name: str, method_info: Dict,
                                     force_reindex: bool = False) -> List[Dict]:
        """获取RAG上下文并显示进度"""
        try:
            print("    分析项目结构...")
            print(f"    调试: method_info类型: {type(method_info)}")
            print(f"    调试: method_info内容: {method_info}")

            # 确保项目已索引
            if force_reindex:
                print("    强制重新索引项目...")
                analysis_result = self.project_analyzer.analyze_project(force_reindex=True)
            else:
                analysis_result = self.project_analyzer.analyze_project(force_reindex=False)
                if not analysis_result.get('success', False):
                    print("     项目索引失败，尝试重新索引...")
                    analysis_result = self.project_analyzer.analyze_project(force_reindex=True)

            if analysis_result.get('success', False):
                stats = analysis_result.get('stats', {})
                print(f"   项目统计: {stats.get('indexed_files', 0)} 个文件, {stats.get('total_methods', 0)} 个方法")

                print("   检索相关上下文...")
                # 查找相关上下文，传递完整的方法签名用于参数类型检索
                full_method_signature = method_info.get('signature', '') if method_info else ''
                print(f"   调试: full_method_signature: {full_method_signature}")

                context_results = self.project_analyzer.find_relevant_context(
                    target_method=method_signature,
                    query_description=f"Java method {method_name} implementation and related code",
                    top_k=5,
                    method_signature=full_method_signature,  #  新增：传递完整方法签名
                    force_reindex=force_reindex  # 新增：传递强制重新索引参数
                )
                
                if self.debug and context_results:
                    print("    调试: 找到的上下文:")
                    for i, ctx in enumerate(context_results[:2], 1):
                        metadata = ctx.get('metadata', {})
                        print(f"      {i}. {metadata.get('class_name', 'Unknown')}.{metadata.get('method_name', 'Unknown')}")
                        print(f"         距离: {ctx.get('distance', 'Unknown'):.4f}")

                # 保存RAG上下文用于对话记录
                self.last_rag_contexts = context_results

                return context_results
            else:
                print("    项目索引失败，无法获取RAG上下文")
                return []
                
        except Exception as e:
            print(f"    获取RAG上下文失败: {e}")
            return []
    
    def _generate_initial_test_with_debug(self, method_info: Dict[str, Any], 
                                        context_info: List[Dict], test_style: str) -> Optional[str]:
        """生成初始测试代码并显示调试信息"""
        try:
            # 构建类信息和方法信息
            class_info = {
                'name': method_info['class_name'],
                'package': method_info.get('package')
            }
            
            # 生成提示
            prompt = EnhancedTestPrompt.create_method_test_prompt(
                class_info, method_info, context_info, test_style
            )
            
            if self.debug:
                print(f"    调试: 生成的提示长度: {len(prompt)} 字符")
                print(f"    调试: 提示前100字符: {prompt[:100]}...")
            
            print("   调用大模型生成测试代码...")
            # 调用LLM生成代码
            messages = [{"role": "user", "content": prompt}]
            response = self.ollama_client.call_unstructured(
                messages=messages,
                is_code_task=True
            )
            
            if self.debug:
                print(f"    调试: 大模型响应类型: {type(response)}")
                if isinstance(response, str):
                    print(f"    调试: 响应长度: {len(response)} 字符")
                    print(f"    调试: 响应前100字符: {response[:100]}...")
            
            if response and isinstance(response, str):
                # 保存与大模型的对话
                self._save_llm_conversation(method_info, prompt, response, "initial_generation",
                                           context_info, len(context_info))

                # 清理大模型响应，移除非Java代码内容
                cleaned_response = self._clean_llm_response(response)
                return cleaned_response
            else:
                print("    大模型返回了无效的响应")
                return None
                
        except Exception as e:
            print(f"    生成初始测试代码失败: {e}")
            return None

    def _compile_and_fix_loop_with_progress(self, initial_test: str, method_info: Dict[str, Any],
                                          context_info: List[Dict], max_attempts: int, fix_strategy: str = "both") -> Dict[str, Any]:
        """编译和修复循环并显示进度"""
        current_code = initial_test
        attempt = 0

        # 根据修复策略决定执行流程
        print(f"     修复策略: {fix_strategy}")

        # 阶段1: 编译修复（如果策略包含编译修复）
        if fix_strategy in ["compile-only", "both"]:
            print(f"    阶段1: 编译修复")
            compile_result = self._compile_fix_phase(current_code, method_info, context_info, max_attempts)

            if not compile_result['success'] and fix_strategy == "compile-only":
                return compile_result

            current_code = compile_result.get('code', current_code)
            attempt = compile_result.get('attempts', 0)

            if compile_result['success']:
                print(f"    编译修复成功！")
            else:
                print(f"     编译修复未完全成功，继续下一阶段...")

        # 阶段2: 运行时修复（如果策略包含运行时修复）
        if fix_strategy in ["runtime-only", "both"]:
            print(f"    阶段2: 运行时修复")

            # 如果是 runtime-only 策略，先检查编译状态
            if fix_strategy == "runtime-only":
                compile_success, compile_error, class_file = self.compilation_manager.compile_test(
                    current_code, method_info['class_name'], method_info.get('package')
                )
                if not compile_success:
                    print(f"     检测到编译错误，将先进行编译修复...")
                    # 先尝试编译修复，然后再进行运行时修复
                    compile_result = self._compile_fix_phase(current_code, method_info, context_info, max_attempts)

                    if compile_result['success']:
                        print(f"    编译修复成功，继续运行时修复...")
                        current_code = compile_result.get('code', current_code)
                        attempt = compile_result.get('attempts', 0)
                    else:
                        print(f"    编译修复失败，但继续尝试运行时修复...")
                        # 即使编译修复失败，也继续尝试运行时修复，因为LLM可能能够同时修复编译和运行时问题
                        attempt = compile_result.get('attempts', 0)

            runtime_result = self._runtime_fix_phase(current_code, method_info, context_info, max_attempts - attempt)

            if runtime_result['success']:
                return {
                    'success': True,
                    'code': runtime_result['code'],
                    'attempts': attempt + runtime_result['attempts'],
                    'class_file': runtime_result.get('class_file'),
                    'phases': ['compile', 'runtime'] if fix_strategy == "both" else ['runtime']
                }
            else:
                return {
                    'success': False,
                    'error': runtime_result['error'],
                    'attempts': attempt + runtime_result['attempts'],
                    'phases': ['compile', 'runtime'] if fix_strategy == "both" else ['runtime']
                }

        # 如果只是编译修复，返回编译结果
        if fix_strategy == "compile-only":
            return compile_result

        # 默认返回失败
        return {
            'success': False,
            'error': f"修复策略 {fix_strategy} 执行失败",
            'attempts': attempt
        }

    def _compile_fix_phase(self, initial_code: str, method_info: Dict[str, Any],
                          context_info: List[Dict], max_attempts: int) -> Dict[str, Any]:
        """编译修复阶段"""
        current_code = initial_code
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"      编译尝试 {attempt}/{max_attempts}...")

            # 尝试编译
            success, error, class_file = self.compilation_manager.compile_test(
                current_code,
                method_info['class_name'],
                method_info.get('package')
            )

            if success:
                print(f"      编译成功！")
                return {
                    'success': True,
                    'code': current_code,
                    'attempts': attempt,
                    'class_file': str(class_file) if class_file else None
                }

            print(f"      编译失败，准备修复...")
            if self.debug:
                print(f"      调试: 编译错误前200字符: {error[:200]}...")

            self.stats['fix_attempts'] += 1

            # 生成修复代码
            print(f"      生成编译修复代码...")
            fixed_code = self._fix_compilation_error_with_debug(current_code, error, method_info, context_info)
            if not fixed_code:
                print(f"      编译修复代码生成失败")
                break

            current_code = fixed_code
            print(f"      编译修复代码已生成，长度: {len(current_code)} 字符")

        return {
            'success': False,
            'error': f"编译修复达到最大尝试次数 ({max_attempts})",
            'attempts': attempt,
            'last_error': error if 'error' in locals() else 'Unknown error'
        }

    def _runtime_fix_phase(self, initial_code: str, method_info: Dict[str, Any],
                          context_info: List[Dict], max_attempts: int) -> Dict[str, Any]:
        """运行时修复阶段"""
        current_code = initial_code
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"      运行尝试 {attempt}/{max_attempts}...")

            # 先确保编译成功
            compile_success, compile_error, class_file = self.compilation_manager.compile_test(
                current_code, method_info['class_name'], method_info.get('package')
            )

            if not compile_success:
                print(f"      运行前编译失败，尝试修复编译错误...")
                if self.debug:
                    print(f"      调试: 编译错误前200字符: {compile_error[:200]}...")

                # 尝试修复编译错误
                fixed_code = self._fix_compilation_error_with_debug(current_code, compile_error, method_info, context_info)
                if not fixed_code:
                    print(f"      编译错误修复失败")
                    return {
                        'success': False,
                        'error': f"运行前编译失败且无法修复: {compile_error}",
                        'attempts': attempt
                    }

                current_code = fixed_code
                print(f"      编译错误修复代码已生成，重新尝试编译...")
                continue  # 重新开始这次循环，先编译再运行

            # 尝试运行测试
            run_success, run_error = self._run_test(class_file, method_info)

            if run_success:
                print(f"      测试运行成功！")
                return {
                    'success': True,
                    'code': current_code,
                    'attempts': attempt,
                    'class_file': str(class_file) if class_file else None
                }

            print(f"      测试运行失败，准备修复...")
            if self.debug:
                print(f"      调试: 运行错误前200字符: {run_error[:200]}...")

            self.stats['fix_attempts'] += 1

            # 生成运行时修复代码
            print(f"      生成运行时修复代码...")
            fixed_code = self._fix_runtime_error_with_debug(current_code, run_error, method_info, context_info)
            if not fixed_code:
                print(f"      运行时修复代码生成失败")
                break

            current_code = fixed_code
            print(f"      运行时修复代码已生成，长度: {len(current_code)} 字符")

        return {
            'success': False,
            'error': f"运行时修复达到最大尝试次数 ({max_attempts})",
            'attempts': attempt,
            'last_error': run_error if 'run_error' in locals() else 'Unknown error'
        }

    def _fix_compilation_error_with_debug(self, code: str, error: str, method_info: Dict[str, Any],
                                        context_info: List[Dict]) -> Optional[str]:
        """修复编译错误并显示调试信息"""
        try:
            # 尝试从编译错误中增强上下文
            enhanced_context_info = context_info
            if hasattr(self, 'context_generator') and self.context_generator:
                enhanced_context_info = self.context_generator.enhance_context_from_compilation_errors(
                    error, context_info
                )
                if len(enhanced_context_info) > len(context_info):
                    new_contexts = enhanced_context_info[len(context_info):]
                    print(f"      从编译错误中增强了 {len(new_contexts)} 个上下文")

                    # 记录错误增强的上下文
                    self.error_enhanced_contexts.extend(new_contexts)

                    # 如果有回调函数，调用它来记录上下文
                    if self.error_context_callback:
                        self.error_context_callback(new_contexts, "compilation")

            # 构建修复提示
            fix_prompt = EnhancedTestPrompt.create_compile_fix_prompt(
                method_info=method_info,
                context_info=enhanced_context_info,
                generated_test=code,
                compile_error=error
            )

            if self.debug:
                print(f"    调试: 修复提示长度: {len(fix_prompt)} 字符")
                print(f"    调试: 修复提示前100字符: {fix_prompt[:100]}...")

            print("   调用大模型修复代码...")
            # 调用LLM修复
            messages = [{"role": "user", "content": fix_prompt}]
            response = self.ollama_client.call_unstructured(
                messages=messages,
                is_code_task=True
            )

            if self.debug:
                print(f"    调试: 修复响应类型: {type(response)}")
                if isinstance(response, str):
                    print(f"    调试: 修复响应长度: {len(response)} 字符")

            if response and isinstance(response, str):
                # 保存编译修复对话（使用增强后的上下文）
                self._save_llm_conversation(method_info, fix_prompt, response, "compile_fix",
                                           enhanced_context_info, len(context_info))

                # 清理大模型响应，移除非Java代码内容
                cleaned_response = self._clean_llm_response(response)
                return cleaned_response
            else:
                print("    大模型修复返回了无效的响应")
                return None

        except Exception as e:
            print(f"    修复编译错误失败: {e}")
            return None

    def _find_class_file(self, class_name: str) -> Optional[Path]:
        """查找类文件"""
        # 转换类名为文件路径
        if '.' in class_name:
            parts = class_name.split('.')
            class_file_name = parts[-1] + '.java'
            package_path = '/'.join(parts[:-1])

            # 在src/main/java中查找
            search_path = self.project_path / "src" / "main" / "java" / package_path / class_file_name
            if search_path.exists():
                return search_path

        # 递归查找
        for java_file in self.project_path.rglob("*.java"):
            if java_file.stem == class_name.split('.')[-1]:
                return java_file

        return None

    def _extract_return_type(self, signature: str) -> str:
        """从方法签名中提取返回类型"""
        # 简单的返回类型提取
        parts = signature.split()
        for i, part in enumerate(parts):
            if '(' in part:  # 找到方法名
                if i > 0:
                    return parts[i-1]
                break
        return "void"

    def _extract_parameters(self, signature: str) -> List[str]:
        """从方法签名中提取参数"""
        try:
            # 处理多行签名
            signature_clean = ' '.join(signature.split())

            if '(' in signature_clean and ')' in signature_clean:
                # 找到参数部分
                start = signature_clean.find('(')
                end = signature_clean.rfind(')')
                param_part = signature_clean[start + 1:end].strip()

                if param_part:
                    # 分割参数，处理泛型
                    parameters = []
                    current_param = ""
                    bracket_count = 0

                    for char in param_part + ',':  # 添加逗号确保最后一个参数被处理
                        if char == '<':
                            bracket_count += 1
                        elif char == '>':
                            bracket_count -= 1
                        elif char == ',' and bracket_count == 0:
                            if current_param.strip():
                                parameters.append(current_param.strip())
                            current_param = ""
                            continue
                        current_param += char

                    return parameters
            return []
        except Exception as e:
            logger.debug(f"参数提取失败: {e}")
            return []

    def _save_test_file(self, class_name: str, method_name: str, test_code: str) -> Path:
        """保存测试文件"""
        # 提取简单类名
        simple_class_name = class_name.split('.')[-1]

        # 生成测试文件名
        test_file_name = f"{simple_class_name}_{method_name}_Test.java"
        test_file_path = self.output_dir / test_file_name

        # 写入文件
        test_file_path.write_text(test_code, encoding='utf-8')

        return test_file_path

    def _create_error_result(self, method_signature: str, error: str, start_time: float,
                           rag_enabled: bool = False) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'success': False,
            'method_signature': method_signature,
            'error': error,
            'rag_enabled': rag_enabled,
            'total_duration': time.time() - start_time
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'generator_stats': self.stats,
            'tree_sitter_available': self.tree_sitter_parser.is_available(),
            'compilation_manager_type': 'ImprovedCompilationManager',
            'project_path': str(self.project_path),
            'output_directory': str(self.output_dir),
            'debug_mode': self.debug
        }

    def _run_test(self, class_file: Path, method_info: Dict[str, Any]) -> Tuple[bool, str]:
        """运行测试并返回结果"""
        try:
            # 使用执行管理器运行测试
            test_class_name = class_file.stem  # 获取不带扩展名的文件名
            method_name = method_info.get('method_name')  # 可选的方法名

            success, error_msg = self.execution_manager.execute_runtime_command(
                test_class_name=test_class_name,
                method_name=method_name
            )

            if success:
                self.stats['runtime_successes'] += 1
                return True, "测试运行成功"
            else:
                self.stats['runtime_failures'] += 1
                return False, error_msg

        except Exception as e:
            self.stats['runtime_failures'] += 1
            return False, f"测试运行异常: {str(e)}"

    def _fix_runtime_error_with_debug(self, code: str, error: str, method_info: Dict[str, Any],
                                    context_info: List[Dict]) -> Optional[str]:
        """修复运行时错误并显示调试信息"""
        try:
            # 尝试从运行时错误中增强上下文
            enhanced_context_info = context_info
            if hasattr(self, 'context_generator') and self.context_generator:
                enhanced_context_info = self.context_generator.enhance_context_from_runtime_errors(
                    error, context_info
                )
                if len(enhanced_context_info) > len(context_info):
                    new_contexts = enhanced_context_info[len(context_info):]
                    print(f"      从运行时错误中增强了 {len(new_contexts)} 个上下文")

                    # 记录错误增强的上下文
                    self.error_enhanced_contexts.extend(new_contexts)

                    # 如果有回调函数，调用它来记录上下文
                    if self.error_context_callback:
                        self.error_context_callback(new_contexts, "runtime")

            # 使用增强的运行时修复提示
            from prompting.enhanced_test_prompt import EnhancedTestPrompt

            fix_prompt = EnhancedTestPrompt.create_runtime_fix_prompt(
                method_info=method_info,
                context_info=enhanced_context_info,
                generated_test=code,
                runtime_error=error
            )

            if self.debug:
                print(f"      调试: 运行时修复提示长度: {len(fix_prompt)} 字符")
                print(f"      调试: 运行时修复提示前100字符: {fix_prompt[:100]}...")

            print("     调用大模型修复运行时错误...")
            # 调用LLM修复
            messages = [{"role": "user", "content": fix_prompt}]
            response = self.ollama_client.call_unstructured(
                messages=messages,
                is_code_task=True
            )

            if self.debug:
                print(f"      调试: 运行时修复响应类型: {type(response)}")
                if isinstance(response, str):
                    print(f"      调试: 运行时修复响应长度: {len(response)} 字符")

            if response and isinstance(response, str):
                # 清理大模型响应，移除非Java代码内容
                cleaned_response = self._clean_llm_response(response)
                return cleaned_response
            else:
                print("      大模型运行时修复返回了无效的响应")
                return None

        except Exception as e:
            print(f"      修复运行时错误失败: {e}")
            return None

    def _clean_llm_response(self, response: str) -> str:
        """
        清理大模型响应，移除非Java代码内容

        Args:
            response: 大模型的原始响应

        Returns:
            清理后的Java代码
        """
        import re

        if self.debug:
            print(f"    调试: 清理前响应长度: {len(response)} 字符")
            print(f"    调试: 清理前前100字符: {response[:100]}...")

        # 移除 <think> 标签及其内容
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)

        # 移除其他XML标签
        response = re.sub(r'<[^>]+>', '', response)

        # 移除markdown代码块标记
        response = re.sub(r'```java\s*', '', response)
        response = re.sub(r'```\s*$', '', response)

        # 查找Java包声明的开始位置
        package_match = re.search(r'package\s+[\w.]+\s*;', response)
        if package_match:
            # 从package声明开始截取
            response = response[package_match.start():]

        # 确保代码以完整的类结束
        # 查找最后一个完整的类定义
        class_pattern = r'public\s+class\s+\w+.*?\{.*\}'
        class_matches = list(re.finditer(class_pattern, response, flags=re.DOTALL))

        if class_matches:
            # 取最后一个完整的类
            last_match = class_matches[-1]
            response = response[:last_match.end()]
        else:
            # 如果没有找到完整的类，尝试修复不完整的代码
            response = self._fix_incomplete_java_code(response)

        # 清理多余的空白字符
        response = response.strip()

        if self.debug:
            print(f"    调试: 清理后响应长度: {len(response)} 字符")
            print(f"    调试: 清理后前100字符: {response[:100]}...")

        return response

    def _fix_incomplete_java_code(self, code: str) -> str:
        """
        修复不完整的Java代码

        Args:
            code: 不完整的Java代码

        Returns:
            修复后的Java代码
        """
        lines = code.split('\n')
        fixed_lines = []
        brace_count = 0
        in_string = False
        escape_next = False

        for line in lines:
            # 检查字符串和大括号平衡
            for char in line:
                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1

            # 如果行以未结束的字符串结尾，尝试修复
            if in_string and not line.rstrip().endswith('"'):
                line = line.rstrip() + '"'
                in_string = False

            fixed_lines.append(line)

        # 添加缺失的大括号
        while brace_count > 0:
            fixed_lines.append('}')
            brace_count -= 1

        return '\n'.join(fixed_lines)

    def cleanup(self):
        """清理资源"""
        if self.compilation_manager:
            self.compilation_manager.cleanup()
