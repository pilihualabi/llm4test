"""
解析器管理器
统一管理所有语言解析器，提供自动语言检测和解析器选择功能
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import logging

from .base_parser import (
    BaseLanguageParser, LanguageDetector, ParserFactory, ParsedClass
)

# 导入所有解析器以触发注册
from .java_parser import JavaParser
# from .python_parser import PythonParser  # 暂时注释掉，因为模块不存在

logger = logging.getLogger(__name__)

class ParserManager:
    """解析器管理器"""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self._ensure_parsers_registered()
    
    def _ensure_parsers_registered(self):
        """确保所有解析器都已注册"""
        # 这里可以添加更多解析器的导入
        logger.info(f"已注册的解析器: {ParserFactory.get_supported_languages()}")
    
    def parse_file(self, file_path: Union[str, Path]) -> Optional[ParsedClass]:
        """
        自动检测语言并解析文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的类信息，如果解析失败返回None
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None
        
        # 检测语言
        language = self.language_detector.detect_language(file_path)
        if not language:
            logger.error(f"无法检测文件语言: {file_path}")
            return None
        
        # 获取解析器
        parser = ParserFactory.create_parser(language)
        if not parser:
            logger.error(f"不支持的语言: {language}")
            return None
        
        try:
            return parser.parse_file(file_path)
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
            return None
    
    def parse_project(self, project_path: Union[str, Path]) -> Dict[str, List[ParsedClass]]:
        """
        解析整个项目
        
        Args:
            project_path: 项目路径
            
        Returns:
            按语言分组的解析结果
        """
        project_path = Path(project_path)
        results = {}
        
        # 获取项目中的语言分布
        language_counts = self.language_detector.detect_project_language(project_path)
        logger.info(f"项目语言分布: {language_counts}")
        
        # 解析每种语言的文件
        for language in language_counts.keys():
            if ParserFactory.is_language_supported(language):
                language_files = self._get_language_files(project_path, language)
                parsed_classes = []
                
                for file_path in language_files:
                    parsed_class = self.parse_file(file_path)
                    if parsed_class:
                        parsed_classes.append(parsed_class)
                
                if parsed_classes:
                    results[language] = parsed_classes
                    logger.info(f"解析 {language} 文件: {len(parsed_classes)} 个类/模块")
        
        return results
    
    def _get_language_files(self, project_path: Path, language: str) -> List[Path]:
        """获取指定语言的所有文件"""
        parser = ParserFactory.create_parser(language)
        if not parser:
            return []
        
        extensions = parser.get_language_extensions()
        files = []
        
        for ext in extensions:
            files.extend(project_path.rglob(f"*{ext}"))
        
        # 过滤掉测试文件和构建文件
        filtered_files = []
        for file_path in files:
            if self._should_include_file(file_path):
                filtered_files.append(file_path)
        
        return filtered_files
    
    def _should_include_file(self, file_path: Path) -> bool:
        """判断是否应该包含该文件"""
        # 排除常见的测试和构建目录
        exclude_patterns = [
            'test', 'tests', '__pycache__', 'node_modules', 
            'target', 'build', '.git', 'venv', 'env'
        ]
        
        path_str = str(file_path).lower()
        for pattern in exclude_patterns:
            if pattern in path_str:
                return False
        
        return True
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return ParserFactory.get_supported_languages()
    
    def get_primary_language(self, project_path: Union[str, Path]) -> Optional[str]:
        """获取项目的主要编程语言"""
        return self.language_detector.get_primary_language(Path(project_path))
    
    def find_method_in_project(self, project_path: Union[str, Path], 
                              method_signature: str) -> Optional[Tuple[ParsedClass, str]]:
        """
        在项目中查找指定的方法
        
        Args:
            project_path: 项目路径
            method_signature: 方法签名，格式为 package.ClassName#methodName 或 module.function_name
            
        Returns:
            包含方法的类和方法名，如果未找到返回None
        """
        project_path = Path(project_path)
        
        # 解析方法签名
        if '#' in method_signature:
            # Java风格: package.ClassName#methodName
            class_part, method_name = method_signature.split('#', 1)
            package_parts = class_part.split('.')
            class_name = package_parts[-1]
        elif '.' in method_signature:
            # Python风格: module.function_name
            parts = method_signature.split('.')
            method_name = parts[-1]
            class_name = parts[-2] if len(parts) > 1 else None
        else:
            # 只有方法名
            method_name = method_signature
            class_name = None
        
        # 解析项目
        project_results = self.parse_project(project_path)
        
        # 搜索方法
        for language, parsed_classes in project_results.items():
            for parsed_class in parsed_classes:
                # 检查类名匹配（如果指定了类名）
                if class_name and parsed_class.name != class_name:
                    continue
                
                # 检查方法是否存在
                # 创建临时解析器来查找方法
                parser = ParserFactory.create_parser(language)
                method = parser.find_method(parsed_class, method_name) if parser else None
                if method:
                    return parsed_class, method_name
        
        return None
    
    def extract_method_context(self, project_path: Union[str, Path], 
                              method_signature: str) -> Optional[Dict]:
        """
        提取方法的完整上下文信息
        
        Args:
            project_path: 项目路径
            method_signature: 方法签名
            
        Returns:
            方法上下文信息字典
        """
        result = self.find_method_in_project(project_path, method_signature)
        if not result:
            return None
        
        parsed_class, method_name = result
        
        # 获取解析器
        language = self.language_detector.get_primary_language(Path(project_path))
        parser = ParserFactory.create_parser(language)
        
        if not parser:
            return None
        
        # 提取依赖和切片
        dependencies = parser.extract_dependencies(parsed_class, method_name)
        method_slice = parser.extract_method_slice(parsed_class, method_name)
        method = parser.find_method(parsed_class, method_name)
        
        return {
            'class_info': parsed_class,
            'method_info': method,
            'dependencies': dependencies,
            'method_slice': method_slice,
            'language': language,
            'test_framework': parser.get_test_framework()
        }

# 全局解析器管理器实例
parser_manager = ParserManager()
