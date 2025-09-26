"""
Java compilation utilities for the test suite generator.
"""

import subprocess
import logging
import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, List
# 移除对已删除模块的导入
# from config import test_config
# from init.build import _ensure_sdkman_installed, _install_jdk_with_sdkman

logger = logging.getLogger(__name__)

class JavaCompiler:
    """Java编译器类"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.java_home = self._detect_java_home()
        self.build_system = self._detect_build_system()
    
    def _detect_java_home(self) -> Optional[str]:
        """检测JAVA_HOME"""
        # 检查环境变量
        java_home = os.environ.get('JAVA_HOME')
        if java_home and os.path.exists(java_home):
            return java_home
        
        # 检查系统Java
        try:
            result = subprocess.run(['which', 'java'], capture_output=True, text=True)
            if result.returncode == 0:
                java_path = result.stdout.strip()
                # 尝试找到JAVA_HOME
                java_home = os.path.dirname(os.path.dirname(java_path))
                if os.path.exists(java_home):
                    return java_home
        except Exception:
            pass
        
        return None
    
    def _detect_build_system(self) -> str:
        """检测构建系统"""
        if (self.project_path / "pom.xml").exists():
            return "maven"
        elif (self.project_path / "build.gradle").exists():
            return "gradle"
        else:
            return "none"
    
    def compile_project(self) -> Tuple[bool, str]:
        """编译项目"""
        if self.build_system == "maven":
            return self._compile_with_maven()
        elif self.build_system == "gradle":
            return self._compile_with_gradle()
        else:
            return False, "No build system detected"
    
    def _compile_with_maven(self) -> Tuple[bool, str]:
        """使用Maven编译"""
        try:
            cmd = ["mvn", "compile"]
            env = os.environ.copy()
            
            if self.java_home:
                env['JAVA_HOME'] = self.java_home
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                return True, "Maven compilation successful"
            else:
                return False, f"Maven compilation failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Maven compilation error: {str(e)}"
    
    def _compile_with_gradle(self) -> Tuple[bool, str]:
        """使用Gradle编译"""
        try:
            cmd = ["gradle", "build"]
            env = os.environ.copy()
            
            if self.java_home:
                env['JAVA_HOME'] = self.java_home
                env['GRADLE_OPTS'] = f"-Dorg.gradle.java.home={self.java_home}"
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                return True, "Gradle compilation successful"
            else:
                return False, f"Gradle compilation failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Gradle compilation error: {str(e)}"
    
    def compile_test_file(self, test_file: Path) -> Tuple[bool, str]:
        """编译单个测试文件"""
        try:
            # 使用javac直接编译
            cmd = ["javac", "-cp", self._get_classpath(), str(test_file)]
            env = os.environ.copy()
            
            if self.java_home:
                env['JAVA_HOME'] = self.java_home
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                return True, "Test compilation successful"
            else:
                return False, f"Test compilation failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Test compilation error: {str(e)}"
    
    def _get_classpath(self) -> str:
        """获取类路径"""
        classpath_parts = []
        
        # 添加项目输出目录
        if self.build_system == "maven":
            target_dir = self.project_path / "target" / "classes"
            if target_dir.exists():
                classpath_parts.append(str(target_dir))
        elif self.build_system == "gradle":
            build_dir = self.project_path / "build" / "classes" / "java" / "main"
            if build_dir.exists():
                classpath_parts.append(str(build_dir))
        
        # 添加依赖
        if self.build_system == "maven":
            lib_dir = self.project_path / "target" / "lib"
            if lib_dir.exists():
                for jar_file in lib_dir.glob("*.jar"):
                    classpath_parts.append(str(jar_file))
        
        return ":".join(classpath_parts) if classpath_parts else "." 