import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import re
# 移除对已删除模块的导入
# from config import test_config
# from init.repository import RepositoryManager

logger = logging.getLogger(__name__)

class BugAssessment:
    """Bug评估类"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    def assess_test_quality(self, test_file: Path) -> Dict[str, any]:
        """评估测试质量"""
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            
            metrics = {
                'test_count': content.count('@Test'),
                'assertion_count': content.count('assert'),
                'has_exception_test': 'assertThrows' in content,
                'has_setup': '@BeforeEach' in content,
                'has_teardown': '@AfterEach' in content,
                'has_parameterized_test': '@ParameterizedTest' in content,
                'code_coverage': self._estimate_code_coverage(content)
            }
            
            # 计算质量分数
            score = 0
            if metrics['test_count'] > 0: score += 20
            if metrics['assertion_count'] > 0: score += 20
            if metrics['has_exception_test']: score += 15
            if metrics['has_setup']: score += 10
            if metrics['has_teardown']: score += 10
            if metrics['has_parameterized_test']: score += 15
            if metrics['code_coverage'] > 0.7: score += 10
            
            metrics['quality_score'] = min(score, 100)
            metrics['quality_level'] = self._get_quality_level(score)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error assessing test quality: {e}")
            return {'error': str(e)}
    
    def _estimate_code_coverage(self, content: str) -> float:
        """估算代码覆盖率"""
        # 简单的覆盖率估算
        lines = content.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('//')]
        
        if not code_lines:
            return 0.0
        
        # 计算测试方法数量与代码行数的比例
        test_methods = content.count('@Test')
        if test_methods == 0:
            return 0.0
        
        # 简单的覆盖率估算算法
        coverage = min(test_methods * 0.3, 1.0)
        return coverage
    
    def _get_quality_level(self, score: int) -> str:
        """获取质量等级"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 60:
            return "Poor"
        else:
            return "Very Poor"
    
    def run_tests(self, test_file: Path) -> Dict[str, any]:
        """运行测试"""
        try:
            # 编译测试
            compile_success, compile_output = self._compile_test(test_file)
            if not compile_success:
                return {
                    'success': False,
                    'stage': 'compilation',
                    'output': compile_output
                }
            
            # 运行测试
            run_success, run_output = self._run_test(test_file)
            return {
                'success': run_success,
                'stage': 'execution',
                'output': run_output
            }
            
        except Exception as e:
            return {
                'success': False,
                'stage': 'error',
                'output': str(e)
            }
    
    def _compile_test(self, test_file: Path) -> Tuple[bool, str]:
        """编译测试文件"""
        try:
            cmd = ["javac", "-cp", self._get_classpath(), str(test_file)]
        result = subprocess.run(
            cmd,
                cwd=self.project_path,
            capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, "Compilation successful"
            else:
                return False, f"Compilation failed: {result.stderr}"
                
                except Exception as e:
            return False, f"Compilation error: {str(e)}"
    
    def _run_test(self, test_file: Path) -> Tuple[bool, str]:
        """运行测试文件"""
        try:
            # 获取测试类名
            class_name = test_file.stem
            
            # 构建运行命令
            cmd = ["java", "-cp", self._get_classpath(), class_name]
        result = subprocess.run(
            cmd,
                cwd=self.project_path,
            capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Test execution successful: {result.stdout}"
            else:
                return False, f"Test execution failed: {result.stderr}"
                
    except Exception as e:
            return False, f"Test execution error: {str(e)}"
    
    def _get_classpath(self) -> str:
        """获取类路径"""
        classpath_parts = []
        
        # 添加项目输出目录
        target_dir = self.project_path / "target" / "classes"
        if target_dir.exists():
            classpath_parts.append(str(target_dir))
        
        build_dir = self.project_path / "build" / "classes" / "java" / "main"
        if build_dir.exists():
            classpath_parts.append(str(build_dir))
        
        # 添加测试输出目录
        test_target_dir = self.project_path / "target" / "test-classes"
        if test_target_dir.exists():
            classpath_parts.append(str(test_target_dir))
        
        test_build_dir = self.project_path / "build" / "classes" / "java" / "test"
        if test_build_dir.exists():
            classpath_parts.append(str(test_build_dir))
        
        return ":".join(classpath_parts) if classpath_parts else "." 