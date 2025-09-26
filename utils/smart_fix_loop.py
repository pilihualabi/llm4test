"""
智能修复循环管理器
处理测试代码的编译和运行时错误自动修复
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.ollama_client import OllamaClient
from config.remote_ollama_config import RemoteOllamaConfig
from prompting.enhanced_test_prompt import EnhancedTestPrompt
from utils.test_compilation_manager import TestCompilationManager

logger = logging.getLogger(__name__)

@dataclass
class FixAttempt:
    """修复尝试记录"""
    attempt_number: int
    error_type: str  # 'compile' or 'runtime'
    error_message: str
    fixed_code: str
    success: bool
    duration: float

class SmartFixLoop:
    """智能修复循环管理器"""
    
    def __init__(self, 
                 project_path: Path, 
                 config: RemoteOllamaConfig, 
                 output_dir: Path,
                 max_compile_fixes: int = 3, 
                 max_runtime_fixes: int = 2):
        """
        初始化智能修复循环
        
        Args:
            project_path: 项目路径
            config: Ollama配置
            output_dir: 输出目录
            max_compile_fixes: 最大编译修复次数
            max_runtime_fixes: 最大运行时修复次数
        """
        self.project_path = project_path
        self.output_dir = output_dir
        self.max_compile_fixes = max_compile_fixes
        self.max_runtime_fixes = max_runtime_fixes
        
        # 初始化Ollama客户端
        self.ollama_client = OllamaClient(
            base_url=config.get_base_url(),
            code_model=config.get_code_model(),
            non_code_model=config.get_fix_model(),
            timeout=config.get_request_timeout()
        )
        
        # 初始化编译管理器
        self.compilation_manager = TestCompilationManager(project_path)
        
        # 初始化对话记录器
        from .conversation_logger import ConversationLogger
        self.conversation_logger = ConversationLogger(
            output_dir=output_dir,
            project_name=project_path.name
        )
        
        # 将对话记录器传递给Ollama客户端
        self.ollama_client.conversation_logger = self.conversation_logger
        
        # 修复历史记录
        self.fix_history = []
        
    def generate_and_fix_test(self, 
                             class_info: Dict[str, Any],
                             method_info: Dict[str, Any],
                             context_info: List[Dict[str, Any]] = None,
                             test_style: str = "comprehensive",
                             custom_prompt: str = None) -> Dict[str, Any]:
        """
        生成测试并自动修复错误
        
        Args:
            class_info: 类信息
            method_info: 方法信息
            context_info: 相关上下文
            test_style: 测试风格
            custom_prompt: 自定义提示模板
            
        Returns:
            生成结果字典
        """
        start_time = time.time()
        
        try:
            # 开始对话记录
            self.conversation_logger.start_conversation(
                conversation_type="test_generation",
                target_class=class_info['name'],
                target_method=method_info['name'],
                test_style=test_style
            )
            
            # 1. 生成初始测试代码
            logger.info(f"开始为 {class_info['name']}#{method_info['name']} 生成测试")
            
            if custom_prompt:
                # 使用自定义提示
                prompt = self._create_custom_prompt(custom_prompt, class_info, method_info, context_info)
            else:
                # 使用标准提示
                prompt = EnhancedTestPrompt.create_method_test_prompt(
                    class_info, method_info, context_info, test_style
                )
            
            # 记录原始提示
            original_prompt = prompt
            
            logger.info(f"生成的提示长度: {len(original_prompt)} 字符")
            logger.info(f"提示前100字符: {original_prompt[:100]}...")
            
            # 生成测试代码
            logger.info(f"调用_call_ollama_for_code生成测试代码...")
            generation_result = self._call_ollama_for_code(prompt)
            
            logger.info(f"_call_ollama_for_code返回结果: {generation_result}")
            logger.info(f"结果类型: {type(generation_result)}")
            if isinstance(generation_result, dict):
                logger.info(f"结果键: {list(generation_result.keys())}")
                logger.info(f"success值: {generation_result.get('success')}")
                logger.info(f"error值: {generation_result.get('error')}")
            else:
                logger.error(f"generation_result不是字典类型: {type(generation_result)}, 值: {generation_result}")
                return {
                    'success': False,
                    'error': f"代码生成返回了意外的类型: {type(generation_result)}",
                    'fix_attempts': 0,
                    'total_duration': time.time() - start_time
                }
            
            # 安全访问generation_result
            if not isinstance(generation_result, dict):
                logger.error(f"generation_result不是字典类型: {type(generation_result)}")
                return {
                    'success': False,
                    'error': f"generation_result不是字典类型: {type(generation_result)}",
                    'fix_attempts': 0,
                    'total_duration': time.time() - start_time
                }
            
            if not generation_result.get('success', False):
                return {
                    'success': False,
                    'error': f"代码生成失败: {generation_result.get('error', 'Unknown error')}",
                    'fix_attempts': 0,
                    'total_duration': time.time() - start_time
                }
            
            generated_test = generation_result['code']
            logger.info(f"初始测试代码生成成功，长度: {len(generated_test)} 字符")
            
            # 2. 编译修复循环
            compile_fix_result = self._compile_fix_loop(
                generated_test, original_prompt, class_info, method_info
            )
            
            if not compile_fix_result['success']:
                return {
                    'success': False,
                    'error': f"编译修复失败: {compile_fix_result['error']}",
                    'fix_attempts': len(self.fix_history),
                    'total_duration': time.time() - start_time,
                    'fix_history': self.fix_history
                }
            
            # 3. 运行时修复循环
            runtime_fix_result = self._runtime_fix_loop(
                compile_fix_result['fixed_code'], 
                original_prompt, 
                class_info, 
                method_info
            )
            
            if not runtime_fix_result['success']:
                return {
                    'success': False,
                    'error': f"运行时修复失败: {runtime_fix_result['error']}",
                    'fix_attempts': len(self.fix_history),
                    'total_duration': time.time() - start_time,
                    'fix_history': self.fix_history
                }
            
            # 4. 最终验证
            final_test = runtime_fix_result['fixed_code']
            final_success, final_error = self._verify_final_test(final_test, class_info, method_info)
            
            total_duration = time.time() - start_time
            
            if final_success:
                logger.info(f"测试生成和修复完成，总耗时: {total_duration:.2f}秒")
                # 结束对话记录（成功）
                self.conversation_logger.end_conversation(success=True)
                return {
                    'success': True,
                    'generated_test': final_test,
                    'fix_attempts': len(self.fix_history),
                    'total_duration': total_duration,
                    'fix_history': self.fix_history,
                    'final_verification': 'passed'
                }
            else:
                # 结束对话记录（失败）
                self.conversation_logger.end_conversation(success=False, error=f"最终验证失败: {final_error}")
                return {
                    'success': False,
                    'error': f"最终验证失败: {final_error}",
                    'fix_attempts': len(self.fix_history),
                    'total_duration': total_duration,
                    'fix_history': self.fix_history,
                    'final_verification': 'failed'
                }
                
        except Exception as e:
            logger.error(f"测试生成和修复过程中发生异常: {e}")
            # 结束对话记录（异常）
            self.conversation_logger.end_conversation(success=False, error=f"处理异常: {e}")
            return {
                'success': False,
                'error': f"处理异常: {e}",
                'fix_attempts': len(self.fix_history),
                'total_duration': time.time() - start_time
            }
    
    def _compile_fix_loop(self, 
                          test_code: str, 
                          original_prompt: str,
                          class_info: Dict[str, Any],
                          method_info: Dict[str, Any]) -> Dict[str, Any]:
        """编译修复循环"""
        current_code = test_code
        attempt_count = 0
        
        while attempt_count < self.max_compile_fixes:
            # 尝试编译
            success, error, class_file = self.compilation_manager.compile_test(
                current_code, 
                class_info['name'], 
                class_info.get('package')
            )
            
            if success:
                logger.info(f"编译成功，尝试次数: {attempt_count + 1}")
                return {
                    'success': True,
                    'fixed_code': current_code,
                    'class_file': class_file,
                    'attempts': attempt_count + 1
                }
            
            attempt_count += 1
            logger.info(f"编译失败，尝试修复 (第{attempt_count}次): {error[:100]}...")
            
            # 创建修复提示
            fix_prompt = EnhancedTestPrompt.create_compile_fix_prompt(
                original_prompt, current_code, error, method_info
            )
            
            # 请求修复
            fix_result = self._call_ollama_for_code(fix_prompt)
            
            if not fix_result['success']:
                logger.error(f"修复代码生成失败: {fix_result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': f"修复代码生成失败: {fix_result.get('error', 'Unknown error')}",
                    'attempts': attempt_count
                }
            
            # 记录修复尝试
            self.fix_history.append(FixAttempt(
                attempt_number=attempt_count,
                error_type='compile',
                error_message=error,
                fixed_code=fix_result['code'],
                success=False,
                duration=0.0
            ))
            
            # 更新代码
            current_code = fix_result['code']
            
            # 短暂等待避免过快请求
            time.sleep(1)
        
        # 达到最大尝试次数
        # 保存调试代码
        debug_file = self.project_path / f"debug_{class_info['name']}_{method_info['name']}_failed.java"
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        debug_file.write_text(current_code, encoding='utf-8')
        logger.warning(f"编译修复失败，调试代码已保存到: {debug_file}")
        
        # 结束对话记录（编译修复失败）
        if hasattr(self, 'conversation_logger') and self.conversation_logger:
            self.conversation_logger.end_conversation(
                success=False, 
                error=f"编译修复达到最大尝试次数 ({self.max_compile_fixes})"
            )
        
        return {
            'success': False,
            'error': f"编译修复达到最大尝试次数 ({self.max_compile_fixes})",
            'attempts': attempt_count
        }
    
    def _runtime_fix_loop(self, 
                          test_code: str, 
                          original_prompt: str,
                          class_info: Dict[str, Any],
                          method_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行时修复循环"""
        current_code = test_code
        attempt_count = 0
        
        while attempt_count < self.max_runtime_fixes:
            # 尝试运行
            success, error = self.compilation_manager.run_test(
                current_code, 
                class_info['name'], 
                class_info.get('package')
            )
            
            if success:
                logger.info(f"运行成功，尝试次数: {attempt_count + 1}")
                return {
                    'success': True,
                    'fixed_code': current_code,
                    'attempts': attempt_count + 1
                }
            
            attempt_count += 1
            logger.info(f"运行失败，尝试修复 (第{attempt_count}次): {error[:100]}...")
            
            # 创建运行时修复提示
            fix_prompt = EnhancedTestPrompt.create_runtime_fix_prompt(
                original_prompt, current_code, error, method_info
            )
            
            # 请求修复
            fix_result = self._call_ollama_for_code(fix_prompt)
            
            if not fix_result['success']:
                logger.error(f"运行时修复代码生成失败: {fix_result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': f"运行时修复代码生成失败: {fix_result.get('error', 'Unknown error')}",
                    'attempts': attempt_count
                }
            
            # 记录修复尝试
            self.fix_history.append(FixAttempt(
                attempt_number=attempt_count,
                error_type='runtime',
                error_message=error,
                fixed_code=fix_result['code'],
                success=False,
                duration=0.0
            ))
            
            # 更新代码
            current_code = fix_result['code']
            
            # 短暂等待避免过快请求
            time.sleep(1)
        
        # 达到最大尝试次数
        # 结束对话记录（运行时修复失败）
        if hasattr(self, 'conversation_logger') and self.conversation_logger:
            self.conversation_logger.end_conversation(
                success=False, 
                error=f"运行时修复达到最大尝试次数 ({self.max_runtime_fixes})"
            )
        
        return {
            'success': False,
            'error': f"运行时修复达到最大尝试次数 ({self.max_runtime_fixes})",
            'attempts': attempt_count
        }
    
    def _verify_final_test(self, 
                           test_code: str, 
                           class_info: Dict[str, Any],
                           method_info: Dict[str, Any]) -> Tuple[bool, str]:
        """验证最终测试代码"""
        try:
            # 编译验证
            success, error, class_file = self.compilation_manager.compile_test(
                test_code, 
                class_info['name'], 
                class_info.get('package')
            )
            
            if not success:
                return False, f"最终编译验证失败: {error}"
            
            # 运行验证
            success, error = self.compilation_manager.run_test(
                class_file, 
                class_info['name'], 
                class_info.get('package')
            )
            
            if not success:
                return False, f"最终运行验证失败: {error}"
            
            return True, ""
            
        except Exception as e:
            return False, f"最终验证异常: {e}"
    
    def _create_custom_prompt(self, 
                              template: str, 
                              class_info: Dict[str, Any],
                              method_info: Dict[str, Any],
                              context_info: List[Dict[str, Any]] = None) -> str:
        """创建自定义提示"""
        try:
            # 准备模板变量
            template_vars = {
                'class_name': class_info['name'],
                'package_name': class_info.get('package', ''),
                'method_name': method_info['name'],
                'method_signature': method_info['signature'],
                'return_type': method_info.get('return_type', 'void'),
                'parameters': method_info.get('parameters', ''),
                'exceptions': method_info.get('exceptions', ''),
                'test_style': 'comprehensive'
            }
            
            # 添加上下文信息
            if context_info:
                context_text = "\n".join([
                    f"- {ctx.get('metadata', {}).get('class_name', 'Unknown')}.{ctx.get('metadata', {}).get('method_name', 'Unknown')}"
                    for ctx in context_info[:3]
                ])
                template_vars['context'] = context_text
            
            # 应用模板
            return template.format(**template_vars)
            
        except KeyError as e:
            logger.warning(f"自定义提示模板缺少变量 {e}，使用默认提示")
            return EnhancedTestPrompt.create_method_test_prompt(
                class_info, method_info, context_info
            )
    
    def get_fix_statistics(self) -> Dict[str, Any]:
        """获取修复统计信息"""
        if not self.fix_history:
            return {
                'total_attempts': 0,
                'compile_fixes': 0,
                'runtime_fixes': 0,
                'success_rate': 0.0
            }
        
        total_attempts = len(self.fix_history)
        compile_fixes = len([f for f in self.fix_history if f.error_type == 'compile'])
        runtime_fixes = len([f for f in self.fix_history if f.error_type == 'runtime'])
        
        return {
            'total_attempts': total_attempts,
            'compile_fixes': compile_fixes,
            'runtime_fixes': runtime_fixes,
            'success_rate': 0.0  # 需要根据实际成功情况计算
        }
    
    def cleanup(self):
        """清理资源"""
        if self.compilation_manager:
            self.compilation_manager.cleanup()
    
    def _call_ollama_for_code(self, prompt: str) -> Dict[str, Any]:
        """调用Ollama生成代码"""
        try:
            # 构建消息格式
            messages = [{"role": "user", "content": prompt}]
            
            # 调用Ollama
            response = self.ollama_client.call_unstructured(
                messages=messages,
                is_code_task=True
            )
            
            # 确保response是字符串类型
            if not isinstance(response, str):
                logger.error(f"OllamaClient返回了意外的类型: {type(response)}, 值: {response}")
                return {
                    'success': False,
                    'error': f'OllamaClient返回了意外的类型: {type(response)}'
                }
            
            if response and response.strip():
                return {
                    'success': True,
                    'code': response.strip()
                }
            else:
                return {
                    'success': False,
                    'error': '生成的代码为空'
                }
                
        except Exception as e:
            logger.error(f"调用Ollama失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }
