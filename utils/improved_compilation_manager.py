"""
改进的测试编译管理器
支持Maven项目和更好的依赖管理
"""

import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import re
import time
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ImprovedCompilationManager:
    """改进的测试编译管理器"""
    
    def __init__(self, project_path: Path):
        """
        初始化编译管理器
        
        Args:
            project_path: Java项目路径
        """
        self.project_path = Path(project_path)
        self.temp_dir = None
        self.is_maven_project = self._is_maven_project()
        self.classpath = self._build_classpath()
        
    def _is_maven_project(self) -> bool:
        """检查是否为Maven项目"""
        return (self.project_path / "pom.xml").exists()
    
    def compile_test(self, test_code: str, target_class_name: str, package: str = None) -> Tuple[bool, str, Optional[Path]]:
        """
        编译测试代码
        
        Args:
            test_code: 测试代码
            target_class_name: 目标类名（被测试的类）
            package: 包名
            
        Returns:
            (编译成功, 错误信息, 编译后的class文件路径)
        """
        try:
            # 从测试代码中提取测试类名
            test_class_name = self._extract_test_class_name(test_code)
            if not test_class_name:
                test_class_name = f"{target_class_name}Test"
            
            # 创建临时目录
            self.temp_dir = Path(tempfile.mkdtemp())
            
            # 创建包目录结构
            if package:
                package_dir = self.temp_dir / package.replace('.', '/')
                package_dir.mkdir(parents=True, exist_ok=True)
                test_file = package_dir / f"{test_class_name}.java"
            else:
                test_file = self.temp_dir / f"{test_class_name}.java"
            
            # 写入测试代码
            test_file.write_text(test_code, encoding='utf-8')
            
            logger.info(f"编译测试文件: {test_file}")
            logger.info(f"使用classpath: {self.classpath}")
            
            # 编译
            if self.is_maven_project:
                compile_result = self._compile_with_maven(test_file, test_class_name, package)
            else:
                compile_result = self._compile_with_javac(test_file, test_class_name)
            
            if compile_result['success']:
                # 查找生成的class文件
                class_file = self._find_class_file(test_class_name, package)
                return True, "", class_file
            else:
                return False, compile_result['error'], None
                
        except Exception as e:
            logger.error(f"编译测试代码失败: {e}")
            return False, str(e), None
    
    def _extract_test_class_name(self, test_code: str) -> Optional[str]:
        """从测试代码中提取测试类名"""
        # 查找 public class ClassName
        match = re.search(r'public\s+class\s+(\w+)', test_code)
        if match:
            return match.group(1)
        return None
    
    def _compile_with_maven(self, test_file: Path, test_class_name: str, package: str) -> Dict[str, Any]:
        """使用Maven编译测试"""
        try:
            # 将测试文件复制到Maven测试目录
            if package:
                maven_test_dir = self.project_path / "src" / "test" / "java" / package.replace('.', '/')
            else:
                maven_test_dir = self.project_path / "src" / "test" / "java"
            
            maven_test_dir.mkdir(parents=True, exist_ok=True)
            maven_test_file = maven_test_dir / f"{test_class_name}.java"
            
            # 复制文件
            maven_test_file.write_text(test_file.read_text(encoding='utf-8'), encoding='utf-8')
            
            # 运行Maven编译
            cmd = ['mvn', 'test-compile', '-q']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=60
            )
            
            if result.returncode == 0:
                return {'success': True, 'error': ''}
            else:
                # Maven错误可能在stdout或stderr中
                error_msg = self._parse_maven_errors(result.stderr, result.stdout)
                return {'success': False, 'error': error_msg}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Maven编译超时'}
        except Exception as e:
            return {'success': False, 'error': f'Maven编译异常: {e}'}
    
    def _compile_with_javac(self, test_file: Path, test_class_name: str) -> Dict[str, Any]:
        """使用javac编译测试"""
        try:
            # 构建javac命令
            cmd = ['javac']
            
            # 添加classpath
            if self.classpath:
                cmd.extend(['-cp', self.classpath])
            
            # 添加源文件
            cmd.append(str(test_file))
            
            # 执行编译
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.temp_dir,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'success': True, 'error': ''}
            else:
                # 解析编译错误
                error_msg = self._parse_javac_errors(result.stderr)
                return {'success': False, 'error': error_msg}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'javac编译超时'}
        except Exception as e:
            return {'success': False, 'error': f'javac编译异常: {e}'}
    
    def _build_classpath(self) -> str:
        """构建classpath"""
        classpath_parts = []
        
        if self.is_maven_project:
            # Maven项目：使用target目录
            target_classes = self.project_path / "target" / "classes"
            if target_classes.exists():
                classpath_parts.append(str(target_classes))
            
            target_test_classes = self.project_path / "target" / "test-classes"
            if target_test_classes.exists():
                classpath_parts.append(str(target_test_classes))
            
            # 添加Maven依赖
            maven_deps = self._get_maven_dependencies()
            classpath_parts.extend(maven_deps)
        else:
            # 非Maven项目：查找常见的构建目录
            build_dirs = ["build/classes", "out/production", "bin"]
            for build_dir in build_dirs:
                build_path = self.project_path / build_dir
                if build_path.exists():
                    classpath_parts.append(str(build_path))
        
        # 添加JUnit依赖
        junit_jars = self._find_junit_jars()
        classpath_parts.extend(junit_jars)
        
        # 添加临时目录
        if self.temp_dir:
            classpath_parts.append(str(self.temp_dir))
        
        return ':'.join(classpath_parts) if classpath_parts else ""
    
    def _get_maven_dependencies(self) -> List[str]:
        """获取Maven依赖"""
        deps = []
        try:
            # 运行mvn dependency:build-classpath
            result = subprocess.run(
                ['mvn', 'dependency:build-classpath', '-Dmdep.outputFile=classpath.txt', '-q'],
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=30
            )
            
            if result.returncode == 0:
                classpath_file = self.project_path / "classpath.txt"
                if classpath_file.exists():
                    classpath_content = classpath_file.read_text().strip()
                    if classpath_content:
                        deps.extend(classpath_content.split(':'))
                    classpath_file.unlink()  # 删除临时文件
                    
        except Exception as e:
            logger.warning(f"获取Maven依赖失败: {e}")
        
        return deps
    
    def _find_junit_jars(self) -> List[str]:
        """查找JUnit JAR文件"""
        junit_jars = []
        
        # 常见的JUnit路径
        search_paths = [
            self.project_path / "target" / "lib",
            self.project_path / "lib",
            Path.home() / ".m2" / "repository" / "org" / "junit" / "jupiter",
            Path("/usr/share/java"),  # Linux系统路径
            Path("/opt/homebrew/share/java"),  # macOS Homebrew路径
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                for jar_file in search_path.rglob("*.jar"):
                    jar_name = jar_file.name.lower()
                    if any(keyword in jar_name for keyword in ['junit', 'hamcrest', 'apiguardian']):
                        junit_jars.append(str(jar_file))
        
        return junit_jars
    
    def _find_class_file(self, class_name: str, package: str = None) -> Optional[Path]:
        """查找生成的class文件"""
        search_paths = []
        
        if self.is_maven_project:
            # Maven项目：在target/test-classes中查找
            if package:
                search_paths.append(self.project_path / "target" / "test-classes" / package.replace('.', '/'))
            else:
                search_paths.append(self.project_path / "target" / "test-classes")
        
        # 临时目录
        if self.temp_dir:
            if package:
                search_paths.append(self.temp_dir / package.replace('.', '/'))
            else:
                search_paths.append(self.temp_dir)
        
        for search_path in search_paths:
            class_file = search_path / f"{class_name}.class"
            if class_file.exists():
                return class_file
        
        return None
    
    def _parse_maven_errors(self, stderr: str, stdout: str = "") -> str:
        """解析Maven编译错误"""
        # 合并stdout和stderr
        combined_output = f"{stdout}\n{stderr}".strip()

        if not combined_output:
            return "未知Maven编译错误"

        # 提取Java编译错误（更精确的模式）
        error_lines = []
        for line in combined_output.split('\n'):
            line = line.strip()
            if not line:
                continue

            # 匹配Java编译错误格式
            if ('java:' in line and any(keyword in line for keyword in ['错误', 'error', '不存在', 'cannot find', 'package does not exist'])):
                error_lines.append(line)
            # 匹配文件路径和行号
            elif line.endswith('.java') and ':' in line:
                error_lines.append(line)
            # 匹配Maven编译失败信息
            elif any(keyword in line.lower() for keyword in ['compilation failure', 'failed to compile', '[error]']):
                error_lines.append(line)

        if error_lines:
            return '\n'.join(error_lines)

        # 如果没有找到特定错误，返回包含关键词的行
        fallback_lines = []
        for line in combined_output.split('\n'):
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in ['error', 'failed', 'compilation']):
                fallback_lines.append(line)

        return '\n'.join(fallback_lines) if fallback_lines else combined_output
    
    def _parse_javac_errors(self, stderr: str) -> str:
        """解析javac编译错误"""
        if not stderr:
            return "未知javac编译错误"
        
        # 提取错误行
        error_lines = []
        for line in stderr.split('\n'):
            if line.strip() and ('error:' in line or 'Error:' in line):
                error_lines.append(line.strip())
        
        return '\n'.join(error_lines) if error_lines else stderr
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")
