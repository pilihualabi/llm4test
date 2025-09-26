"""
执行管理器 - 处理编译和运行时的不同执行策略
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import os

logger = logging.getLogger(__name__)

class ExecutionManager:
    """执行管理器 - 统一处理编译和运行时执行"""
    
    def __init__(self, project_path: Path, is_maven_project: bool = True):
        """
        初始化执行管理器
        
        Args:
            project_path: 项目路径
            is_maven_project: 是否为Maven项目
        """
        self.project_path = Path(project_path)
        self.is_maven_project = is_maven_project
        
    def execute_compile_command(self, test_file: Path, class_name: str, package: str = None) -> Tuple[bool, str]:
        """
        执行编译命令
        
        Args:
            test_file: 测试文件路径
            class_name: 类名
            package: 包名
            
        Returns:
            (成功状态, 错误信息)
        """
        try:
            if self.is_maven_project:
                return self._execute_maven_compile()
            else:
                return self._execute_javac_compile(test_file)
                
        except Exception as e:
            logger.error(f"编译执行失败: {e}")
            return False, f"编译执行异常: {str(e)}"
    
    def execute_runtime_command(self, test_class_name: str, method_name: str = None) -> Tuple[bool, str]:
        """
        执行运行时命令
        
        Args:
            test_class_name: 测试类名
            method_name: 特定方法名（可选）
            
        Returns:
            (成功状态, 错误信息)
        """
        try:
            if self.is_maven_project:
                return self._execute_maven_test(test_class_name, method_name)
            else:
                return self._execute_junit_test(test_class_name, method_name)
                
        except Exception as e:
            logger.error(f"运行时执行失败: {e}")
            return False, f"运行时执行异常: {str(e)}"
    
    def _execute_maven_compile(self) -> Tuple[bool, str]:
        """执行Maven编译命令"""
        cmd = [
            'mvn', 'clean', 'test-compile', 
            '-q',  # 安静模式
            '-Dcheckstyle.skip=true',
            '-Dspotless.check.skip=true',
            '-Dpmd.skip=true',
            '-Dfindbugs.skip=true'
        ]
        
        logger.info(f"执行Maven编译命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )
        
        if result.returncode == 0:
            return True, "Maven编译成功"
        else:
            error_msg = self._parse_maven_compile_errors(result.stdout, result.stderr)
            return False, error_msg
    
    def _execute_javac_compile(self, test_file: Path) -> Tuple[bool, str]:
        """执行javac编译命令"""
        # 构建classpath
        classpath = self._build_classpath()
        
        cmd = ['javac', '-cp', classpath, str(test_file)]
        
        logger.info(f"执行javac编译命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True, "javac编译成功"
        else:
            error_msg = self._parse_javac_compile_errors(result.stderr)
            return False, error_msg
    
    def _execute_maven_test(self, test_class_name: str, method_name: str = None) -> Tuple[bool, str]:
        """执行Maven测试命令"""
        cmd = ['mvn', 'test', '-q']
        
        # 指定测试类
        if test_class_name:
            cmd.append(f'-Dtest={test_class_name}')
            
        # 指定测试方法
        if method_name:
            cmd[-1] = f'-Dtest={test_class_name}#{method_name}'
        
        # 跳过代码检查
        cmd.extend([
            '-Dcheckstyle.skip=true',
            '-Dspotless.check.skip=true',
            '-Dpmd.skip=true',
            '-Dfindbugs.skip=true'
        ])
        
        logger.info(f"执行Maven测试命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=self.project_path,
            capture_output=True,
            text=True,
            timeout=180  # 3分钟超时
        )
        
        if result.returncode == 0:
            return True, "Maven测试执行成功"
        else:
            error_msg = self._parse_maven_test_errors(result.stdout, result.stderr)
            return False, error_msg
    
    def _execute_junit_test(self, test_class_name: str, method_name: str = None) -> Tuple[bool, str]:
        """执行JUnit测试命令"""
        classpath = self._build_classpath()
        
        cmd = [
            'java', '-cp', classpath,
            'org.junit.platform.console.ConsoleLauncher',
            '--select-class', test_class_name
        ]
        
        if method_name:
            cmd[-2] = '--select-method'
            cmd[-1] = f'{test_class_name}#{method_name}'
        
        logger.info(f"执行JUnit测试命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return True, "JUnit测试执行成功"
        else:
            error_msg = self._parse_junit_test_errors(result.stdout, result.stderr)
            return False, error_msg
    
    def _build_classpath(self) -> str:
        """构建classpath"""
        classpath_parts = []
        
        if self.is_maven_project:
            # Maven项目路径
            target_classes = self.project_path / "target" / "classes"
            if target_classes.exists():
                classpath_parts.append(str(target_classes))
            
            target_test_classes = self.project_path / "target" / "test-classes"
            if target_test_classes.exists():
                classpath_parts.append(str(target_test_classes))
        else:
            # 非Maven项目路径
            build_dirs = ["build/classes", "out/production", "bin"]
            for build_dir in build_dirs:
                build_path = self.project_path / build_dir
                if build_path.exists():
                    classpath_parts.append(str(build_path))
        
        return ':'.join(classpath_parts) if classpath_parts else ""
    
    def _parse_maven_compile_errors(self, stdout: str, stderr: str) -> str:
        """解析Maven编译错误"""
        combined = f"{stdout}\n{stderr}".strip()
        
        # 提取编译错误行
        error_lines = []
        for line in combined.split('\n'):
            if any(keyword in line.lower() for keyword in [
                'compilation failure', 'error:', '[error]', 'failed to compile'
            ]):
                error_lines.append(line.strip())
        
        return '\n'.join(error_lines) if error_lines else combined
    
    def _parse_javac_compile_errors(self, stderr: str) -> str:
        """解析javac编译错误"""
        if not stderr:
            return "未知javac编译错误"
        
        # 提取错误行
        error_lines = []
        for line in stderr.split('\n'):
            if 'error:' in line.lower():
                error_lines.append(line.strip())
        
        return '\n'.join(error_lines) if error_lines else stderr
    
    def _parse_maven_test_errors(self, stdout: str, stderr: str) -> str:
        """解析Maven测试错误"""
        combined = f"{stdout}\n{stderr}".strip()
        
        # 提取测试失败信息
        error_lines = []
        for line in combined.split('\n'):
            if any(keyword in line.lower() for keyword in [
                'test failure', 'failed:', 'error:', 'exception', 'assertion'
            ]):
                error_lines.append(line.strip())
        
        return '\n'.join(error_lines) if error_lines else combined
    
    def _parse_junit_test_errors(self, stdout: str, stderr: str) -> str:
        """解析JUnit测试错误"""
        combined = f"{stdout}\n{stderr}".strip()
        
        # 提取JUnit测试失败信息
        error_lines = []
        for line in combined.split('\n'):
            if any(keyword in line.lower() for keyword in [
                'failed', 'error', 'exception', 'assertion'
            ]):
                error_lines.append(line.strip())
        
        return '\n'.join(error_lines) if error_lines else combined
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要信息"""
        return {
            'project_path': str(self.project_path),
            'is_maven_project': self.is_maven_project,
            'execution_manager_type': 'ExecutionManager'
        }
