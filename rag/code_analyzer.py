"""
智能代码分析器 - 用于分析Java类的构造函数、依赖关系等信息
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConstructorInfo:
    """构造函数信息"""
    parameters: List[Tuple[str, str]]  # [(type, name), ...]
    is_default: bool
    is_public: bool
    annotations: List[str]


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    package: str
    is_record: bool
    is_component: bool
    annotations: List[str]
    constructors: List[ConstructorInfo]
    dependencies: List[str]  # 依赖的类名
    imports: List[str]


class ConstructorAnalyzer:
    """构造函数分析器"""
    
    def __init__(self):
        self.logger = logger
    
    def analyze_constructor(self, class_path: str) -> Optional[ConstructorInfo]:
        """
        分析类的构造函数签名
        
        Args:
            class_path: 类文件路径
            
        Returns:
            构造函数信息
        """
        try:
            if not Path(class_path).exists():
                return None
                
            with open(class_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._parse_constructor_from_content(content)
            
        except Exception as e:
            self.logger.debug(f"分析构造函数失败 {class_path}: {e}")
            return None
    
    def _parse_constructor_from_content(self, content: str) -> Optional[ConstructorInfo]:
        """从内容中解析构造函数"""
        try:
            # 检查是否是record类
            if self._is_record_class(content):
                return self._parse_record_constructor(content)
            
            # 检查是否有@RequiredArgsConstructor
            if '@RequiredArgsConstructor' in content:
                return self._parse_lombok_constructor(content)
            
            # 解析显式构造函数
            return self._parse_explicit_constructor(content)
            
        except Exception as e:
            self.logger.debug(f"解析构造函数内容失败: {e}")
            return None
    
    def _is_record_class(self, content: str) -> bool:
        """检查是否是record类"""
        return bool(re.search(r'\brecord\s+\w+', content))
    
    def _parse_record_constructor(self, content: str) -> Optional[ConstructorInfo]:
        """解析record类构造函数"""
        try:
            # record类的构造函数参数在类声明中
            record_match = re.search(r'record\s+\w+\s*\(([^)]*)\)', content)
            if not record_match:
                return None
            
            params_str = record_match.group(1).strip()
            parameters = self._parse_parameters(params_str)
            
            return ConstructorInfo(
                parameters=parameters,
                is_default=False,
                is_public=True,
                annotations=[]
            )
            
        except Exception as e:
            self.logger.debug(f"解析record构造函数失败: {e}")
            return None
    
    def _parse_lombok_constructor(self, content: str) -> Optional[ConstructorInfo]:
        """解析Lombok @RequiredArgsConstructor"""
        try:
            # 查找final字段
            final_fields = re.findall(r'private\s+final\s+(\w+)\s+(\w+)', content)
            
            parameters = [(field_type, field_name) for field_type, field_name in final_fields]
            
            return ConstructorInfo(
                parameters=parameters,
                is_default=False,
                is_public=True,
                annotations=['@RequiredArgsConstructor']
            )
            
        except Exception as e:
            self.logger.debug(f"解析Lombok构造函数失败: {e}")
            return None
    
    def _parse_explicit_constructor(self, content: str) -> Optional[ConstructorInfo]:
        """解析显式构造函数"""
        try:
            # 查找构造函数声明
            class_name = self._extract_class_name(content)
            if not class_name:
                return None
            
            constructor_pattern = rf'(public|private|protected)?\s*{class_name}\s*\(([^)]*)\)'
            constructor_match = re.search(constructor_pattern, content)
            
            if not constructor_match:
                # 没有显式构造函数，使用默认构造函数
                return ConstructorInfo(
                    parameters=[],
                    is_default=True,
                    is_public=True,
                    annotations=[]
                )
            
            access_modifier = constructor_match.group(1) or 'public'
            params_str = constructor_match.group(2).strip()
            parameters = self._parse_parameters(params_str)
            
            return ConstructorInfo(
                parameters=parameters,
                is_default=False,
                is_public=access_modifier == 'public',
                annotations=[]
            )
            
        except Exception as e:
            self.logger.debug(f"解析显式构造函数失败: {e}")
            return None
    
    def _extract_class_name(self, content: str) -> Optional[str]:
        """提取类名"""
        class_match = re.search(r'(?:public\s+)?class\s+(\w+)', content)
        if class_match:
            return class_match.group(1)
        
        record_match = re.search(r'(?:public\s+)?record\s+(\w+)', content)
        if record_match:
            return record_match.group(1)
        
        return None
    
    def _parse_parameters(self, params_str: str) -> List[Tuple[str, str]]:
        """解析参数列表"""
        if not params_str.strip():
            return []
        
        parameters = []
        # 简单的参数解析，处理 "Type name, Type2 name2" 格式
        param_parts = [p.strip() for p in params_str.split(',')]
        
        for param in param_parts:
            if param:
                # 分割类型和名称
                parts = param.strip().split()
                if len(parts) >= 2:
                    param_type = parts[-2]  # 倒数第二个是类型
                    param_name = parts[-1]  # 最后一个是名称
                    parameters.append((param_type, param_name))
        
        return parameters


class DependencyAnalyzer:
    """依赖分析器"""
    
    def __init__(self):
        self.logger = logger
    
    def analyze_dependencies(self, class_path: str) -> List[str]:
        """
        分析类的依赖关系
        
        Args:
            class_path: 类文件路径
            
        Returns:
            依赖的类名列表
        """
        try:
            if not Path(class_path).exists():
                return []
                
            with open(class_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._extract_dependencies(content)
            
        except Exception as e:
            self.logger.debug(f"分析依赖关系失败 {class_path}: {e}")
            return []
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """从内容中提取依赖"""
        dependencies = set()
        
        try:
            # 1. 从@RequiredArgsConstructor + final字段提取
            if '@RequiredArgsConstructor' in content:
                final_fields = re.findall(r'private\s+final\s+(\w+)\s+\w+', content)
                dependencies.update(final_fields)
            
            # 2. 从@Autowired字段提取
            autowired_fields = re.findall(r'@Autowired\s+private\s+(\w+)\s+\w+', content)
            dependencies.update(autowired_fields)
            
            # 3. 从构造函数参数提取
            constructor_params = re.findall(r'public\s+\w+\s*\([^)]*(\w+)\s+\w+[^)]*\)', content)
            dependencies.update(constructor_params)
            
            # 4. 从方法调用中提取可能的依赖
            method_calls = re.findall(r'(\w+)\.(\w+)\s*\(', content)
            for obj, method in method_calls:
                if obj[0].islower() and obj not in ['this', 'super']:
                    # 推断可能的类名
                    potential_class = self._infer_class_name(obj)
                    if potential_class:
                        dependencies.add(potential_class)
            
        except Exception as e:
            self.logger.debug(f"提取依赖失败: {e}")
        
        return list(dependencies)
    
    def _infer_class_name(self, object_name: str) -> Optional[str]:
        """从对象名推断类名"""
        # 常见模式映射
        patterns = {
            'pdfHighlighter': 'PDFHighlighter',
            'highlighter': 'PDFHighlighter',
            'comparator': 'Comparator',
            'extractor': 'Extractor',
            'analyzer': 'Analyzer',
            'processor': 'Processor',
            'service': 'Service',
            'repository': 'Repository',
            'dao': 'DAO',
        }
        
        # 直接匹配
        if object_name in patterns:
            return patterns[object_name]
        
        # 模式匹配
        for pattern, class_suffix in patterns.items():
            if pattern.lower() in object_name.lower():
                return class_suffix
        
        # 默认规则：首字母大写
        if object_name and object_name[0].islower():
            return object_name[0].upper() + object_name[1:]
        
        return None


class SmartCodeAnalyzer:
    """智能代码分析器"""
    
    def __init__(self):
        self.constructor_analyzer = ConstructorAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.logger = logger
    
    def analyze_class(self, class_path: str) -> Optional[ClassInfo]:
        """
        分析Java类的完整信息
        
        Args:
            class_path: 类文件路径
            
        Returns:
            类信息
        """
        try:
            if not Path(class_path).exists():
                return None
                
            with open(class_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取基本信息
            class_name = self._extract_class_name(content)
            package = self._extract_package(content)
            is_record = self._is_record_class(content)
            is_component = self._is_component_class(content)
            annotations = self._extract_annotations(content)
            imports = self._extract_imports(content)
            
            # 分析构造函数
            constructor_info = self.constructor_analyzer._parse_constructor_from_content(content)
            constructors = [constructor_info] if constructor_info else []
            
            # 分析依赖
            dependencies = self.dependency_analyzer._extract_dependencies(content)
            
            return ClassInfo(
                name=class_name or 'Unknown',
                package=package or 'unknown',
                is_record=is_record,
                is_component=is_component,
                annotations=annotations,
                constructors=constructors,
                dependencies=dependencies,
                imports=imports
            )
            
        except Exception as e:
            self.logger.debug(f"分析类失败 {class_path}: {e}")
            return None
    
    def _extract_class_name(self, content: str) -> Optional[str]:
        """提取类名"""
        class_match = re.search(r'(?:public\s+)?class\s+(\w+)', content)
        if class_match:
            return class_match.group(1)
        
        record_match = re.search(r'(?:public\s+)?record\s+(\w+)', content)
        if record_match:
            return record_match.group(1)
        
        return None
    
    def _extract_package(self, content: str) -> Optional[str]:
        """提取包名"""
        package_match = re.search(r'package\s+([\w.]+);', content)
        return package_match.group(1) if package_match else None
    
    def _is_record_class(self, content: str) -> bool:
        """检查是否是record类"""
        return bool(re.search(r'\brecord\s+\w+', content))
    
    def _is_component_class(self, content: str) -> bool:
        """检查是否是Spring组件"""
        component_annotations = ['@Component', '@Service', '@Repository', '@Controller', '@RestController']
        return any(annotation in content for annotation in component_annotations)
    
    def _extract_annotations(self, content: str) -> List[str]:
        """提取类级别注解"""
        annotations = []
        annotation_pattern = r'@(\w+)(?:\([^)]*\))?'
        
        # 只提取类声明前的注解
        class_match = re.search(r'((?:@\w+(?:\([^)]*\))?\s*)*)\s*(?:public\s+)?(?:class|record)\s+\w+', content)
        if class_match:
            annotation_section = class_match.group(1)
            annotations = re.findall(annotation_pattern, annotation_section)
        
        return annotations
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取导入语句"""
        import_pattern = r'import\s+([\w.]+);'
        return re.findall(import_pattern, content)
