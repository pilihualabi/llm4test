#!/usr/bin/env python3
"""
Context-Aware 代码生成器
构建核心代码区和依赖上下文区
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from .project_index import ProjectIndexDatabase, ClassIndex, MethodSignature
from .static_analyzer import JavaStaticAnalyzer
from .error_context_enhancer import ErrorContextEnhancer

logger = logging.getLogger(__name__)

@dataclass
class CoreCodeContext:
    """核心代码区上下文"""
    target_class_fqn: str
    target_class_constructors: List[str]
    target_class_fields: List[str]
    target_method_signature: str
    target_method_implementation: str
    called_internal_methods: List[str]
    used_classes: List[str]

@dataclass
class DependencyContext:
    """依赖上下文区"""
    dependency_fqn: str
    dependency_type: str  # class, interface, abstract_class, enum
    public_constructors: List[str]
    static_factory_methods: List[str]
    is_mockable: bool
    instantiation_guide: str

@dataclass
class ContextAwareTestContext:
    """Context-Aware测试上下文"""
    core_context: CoreCodeContext
    dependency_contexts: List[DependencyContext]
    import_statements: List[str]
    project_group_id: Optional[str]

class ContextAwareGenerator:
    """Context-Aware代码生成器"""
    
    def __init__(self, project_path: str, db_path: str = "./project_index.db"):
        self.project_path = project_path
        self.db = ProjectIndexDatabase(db_path)
        self.project_index = self.db  # 添加project_index别名以兼容新方法
        self.analyzer = JavaStaticAnalyzer(project_path, db_path)
        self.project_group_id = self.analyzer.get_project_group_id()
        self.error_enhancer = ErrorContextEnhancer(self.project_index, self.analyzer)
    
    def generate_context(self, target_class_fqn: str, target_method_name: str) -> ContextAwareTestContext:
        """生成Context-Aware测试上下文"""
        logger.info(f"生成上下文: {target_class_fqn}.{target_method_name}")
        
        # 1. 获取目标类信息
        target_class = self.db.get_class_by_fqn(target_class_fqn)
        if not target_class:
            raise ValueError(f"未找到目标类: {target_class_fqn}")
        
        # 2. 获取目标方法信息
        target_method = self._find_method(target_class, target_method_name)
        if not target_method:
            raise ValueError(f"未找到目标方法: {target_method_name}")
        
        # 3. 构建核心代码区
        core_context = self._build_core_context(target_class, target_method)
        
        # 4. 分析依赖并构建依赖上下文区
        dependency_contexts = self._build_dependency_contexts(target_class, target_method)
        
        # 5. 生成导入语句
        import_statements = self._generate_import_statements(target_class, dependency_contexts, core_context)
        
        return ContextAwareTestContext(
            core_context=core_context,
            dependency_contexts=dependency_contexts,
            import_statements=import_statements,
            project_group_id=self.project_group_id
        )
    
    def _find_method(self, class_index: ClassIndex, method_name: str) -> Optional[MethodSignature]:
        """查找指定方法"""
        for method in class_index.methods:
            if method.name == method_name:
                return method
        return None
    
    def _build_core_context(self, target_class: ClassIndex, target_method: MethodSignature) -> CoreCodeContext:
        """构建核心代码区上下文"""

        # 构造器签名
        constructors = []
        for constructor in target_class.constructors:
            if constructor.access_modifier == "public":
                params = ", ".join(constructor.parameters)
                constructors.append(f"public {target_class.simple_name}({params})")

        # 相关字段签名
        fields = []
        for field in target_class.fields:
            if field.access_modifier in ["public", "protected"]:
                modifiers = []
                if field.is_static:
                    modifiers.append("static")
                if field.is_final:
                    modifiers.append("final")

                modifier_str = " ".join(modifiers)
                if modifier_str:
                    modifier_str += " "

                fields.append(f"{field.access_modifier} {modifier_str}{field.type} {field.name}")

        # 目标方法签名
        params = ", ".join(target_method.parameters)
        method_signature = f"{target_method.access_modifier} {target_method.return_type} {target_method.name}({params})"

        # 获取方法实现（从文件中读取）
        method_implementation = self._get_method_implementation(target_class, target_method)

        # 分析方法实现中使用的类
        used_classes = self._analyze_used_classes(method_implementation)

        # 被调用的内部方法（需要从方法体中分析，这里简化处理）
        called_methods = self._analyze_called_methods(target_class, target_method)

        return CoreCodeContext(
            target_class_fqn=target_class.fully_qualified_name,
            target_class_constructors=constructors,
            target_class_fields=fields,
            target_method_signature=method_signature,
            target_method_implementation=method_implementation,
            called_internal_methods=called_methods,
            used_classes=used_classes
        )
    
    def _analyze_called_methods(self, target_class: ClassIndex, target_method: MethodSignature) -> List[str]:
        """分析被调用的内部方法（简化版本）"""
        called_methods = []
        
        # 这里需要实际的方法体分析，暂时返回同类中的其他public方法
        for method in target_class.methods:
            if (method.name != target_method.name and 
                method.access_modifier in ["public", "protected"]):
                params = ", ".join(method.parameters)
                called_methods.append(f"{method.return_type} {method.name}({params})")
        
        return called_methods

    def _get_method_implementation(self, target_class: ClassIndex, target_method: MethodSignature) -> str:
        """获取方法的实际实现代码（完整版本）"""
        try:
            # 从analyzer获取方法实现
            class_file_path = target_class.file_path
            if not class_file_path:
                return f"// Method implementation not available for {target_method.name}: no file path"

            # 确保路径是Path对象，并相对于项目根目录解析
            from pathlib import Path
            if isinstance(class_file_path, str):
                class_file_path = Path(class_file_path)

            # 如果是相对路径，相对于项目根目录解析
            if not class_file_path.is_absolute():
                class_file_path = self.project_path / class_file_path

            if not class_file_path.exists():
                return f"// Method implementation not available for {target_method.name}: file not found at {class_file_path}"

            # 读取文件内容
            with open(class_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取类注解信息
            class_annotations = self._extract_class_annotations(content)

            # 使用改进的方法提取完整方法实现
            method_impl = self._extract_complete_method(content, target_method.name)

            if method_impl:
                # 构建完整的上下文信息
                result = []

                # 添加类注解信息
                if class_annotations:
                    result.append("## 类注解信息")
                    for annotation in class_annotations:
                        result.append(f"- {annotation}")
                    result.append("")

                # 添加方法实现
                result.append("## 完整方法实现")
                result.append("```java")
                result.append(method_impl)
                result.append("```")

                return '\n'.join(result)
            else:
                return f"// Method implementation not available for {target_method.name}: method not found in file"

        except Exception as e:
            logger.warning(f"Failed to get method implementation: {e}")
            return f"// Method implementation not available: {e}"

    def _extract_class_annotations(self, content: str) -> List[str]:
        """提取类级别注解"""
        annotations = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('@'):
                annotations.append(stripped)
            elif stripped.startswith('public class') or stripped.startswith('class'):
                break

        return annotations

    def _extract_complete_method(self, content: str, method_name: str) -> str:
        """提取完整的方法实现"""
        lines = content.split('\n')
        in_method = False
        method_lines = []
        brace_count = 0

        for line in lines:
            stripped = line.strip()

            # 检测方法开始
            if (method_name in line and
                ('public' in line or 'private' in line or 'protected' in line) and
                '(' in line):
                in_method = True
                method_lines.append(line)
                brace_count += line.count('{') - line.count('}')
            elif in_method:
                method_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and '}' in line:
                    break

        return '\n'.join(method_lines) if method_lines else ""

    def _analyze_used_classes(self, method_implementation: str) -> List[str]:
        """分析方法实现中使用的类"""
        used_classes = []

        # 常见的Java类模式
        class_patterns = [
            r'\b(MessageDigest)\b',
            r'\b(BigInteger)\b',
            r'\b(StringBuilder)\b',
            r'\b(Arrays)\b',
            r'\b(String)\b',
            r'\b(Exception)\b',
            r'\b(List|ArrayList|LinkedList)\b',
            r'\b(Map|HashMap|LinkedHashMap)\b',
            r'\b(Set|HashSet|LinkedHashSet)\b',
            r'\b(Date|LocalDate|LocalDateTime)\b',
            r'\b(Pattern|Matcher)\b',
            r'\b(File|Path|Files)\b',
            r'\b(InputStream|OutputStream|Reader|Writer)\b'
        ]

        for pattern in class_patterns:
            matches = re.findall(pattern, method_implementation)
            for match in matches:
                if match not in used_classes:
                    used_classes.append(match)

        return used_classes

    def _build_dependency_contexts(self, target_class: ClassIndex, target_method: MethodSignature) -> List[DependencyContext]:
        """构建依赖上下文区"""
        dependency_contexts = []
        dependencies = self._extract_dependencies(target_class, target_method)
        
        for dep_type in dependencies:
            dep_context = self._analyze_dependency(dep_type)
            if dep_context:
                dependency_contexts.append(dep_context)
        
        return dependency_contexts
    
    def _extract_dependencies(self, target_class: ClassIndex, target_method: MethodSignature) -> Set[str]:
        """提取依赖类型，包括测试中需要构造函数信息的类"""
        dependencies = set()

        # 从方法参数中提取所有需要构造函数信息的类型
        for param in target_method.parameters:
            param_types = self._extract_all_types_from_parameter(param)
            for param_type in param_types:
                if self._needs_constructor_info(param_type):
                    dependencies.add(param_type)

        # 从字段中提取
        for field in target_class.fields:
            if field.is_final and field.access_modifier == "private":
                # 可能是依赖注入的字段
                field_type = self._extract_simple_type(field.type)
                if field_type and (self._is_project_class(field_type) or self._needs_constructor_info(field_type)):
                    dependencies.add(field_type)

        # 从构造器参数中提取
        for constructor in target_class.constructors:
            if constructor.access_modifier == "public":
                for param in constructor.parameters:
                    param_types = self._extract_all_types_from_parameter(param)
                    for param_type in param_types:
                        if self._needs_constructor_info(param_type):
                            dependencies.add(param_type)

        return dependencies

    def _extract_all_types_from_parameter(self, parameter: str) -> List[str]:
        """从参数字符串中提取所有类型，包括泛型中的类型"""
        types = []

        # 移除final等修饰符
        param = re.sub(r'\b(final|@\w+)\s+', '', parameter)

        # 提取主要类型
        main_type_match = re.match(r'([\w.<>[\]]+)', param.strip())
        if main_type_match:
            type_str = main_type_match.group(1)

            # 提取主要类型（去掉泛型部分）
            if '<' in type_str:
                main_type = type_str.split('<')[0]
                types.append(main_type)

                # 提取泛型中的类型
                generic_part = type_str[type_str.find('<')+1:type_str.rfind('>')]
                generic_types = self._extract_generic_types(generic_part)
                types.extend(generic_types)
            else:
                types.append(type_str)

        return [t for t in types if t and not self._is_basic_type(t)]

    def _extract_generic_types(self, generic_part: str) -> List[str]:
        """从泛型部分提取类型"""
        types = []
        # 简单处理，按逗号分割
        for part in generic_part.split(','):
            part = part.strip()
            if part and not self._is_basic_type(part):
                # 处理嵌套泛型，如 List<ImageChunk> 中的 ImageChunk
                if '<' in part:
                    # 递归处理嵌套泛型
                    main_type = part.split('<')[0]
                    if not self._is_basic_type(main_type):
                        types.append(main_type)
                    nested_generic = part[part.find('<')+1:part.rfind('>')]
                    types.extend(self._extract_generic_types(nested_generic))
                else:
                    types.append(part)
        return types

    def _is_basic_type(self, type_name: str) -> bool:
        """判断是否是基本类型"""
        basic_types = {
            'int', 'long', 'double', 'float', 'boolean', 'char', 'byte', 'short',
            'String', 'Object', 'Integer', 'Long', 'Double', 'Float', 'Boolean',
            'Character', 'Byte', 'Short', 'void'
        }
        return type_name in basic_types

    def _needs_constructor_info(self, class_name: str) -> bool:
        """判断是否需要提供构造函数信息"""
        if self._is_basic_type(class_name):
            return False

        # 项目内的类需要构造函数信息
        if self._is_project_class(class_name):
            return True

        # 常用的第三方类也需要构造函数信息
        common_test_types = {
            'PdfContentByte', 'BaseColor', 'Rectangle', 'Document', 'Page',
            'Element', 'Chunk', 'Paragraph', 'Image', 'Table', 'Cell',
            'ImageChunk', 'PDFPageComparator', 'PageComparator',
            'InputStream', 'OutputStream', 'ByteArrayInputStream', 'ByteArrayOutputStream',
            'IOException', 'DocumentException'
        }

        return class_name in common_test_types

    def _extract_type_from_parameter(self, parameter: str) -> Optional[str]:
        """从参数字符串中提取类型"""
        # 移除final等修饰符
        param = re.sub(r'\b(final|@\w+)\s+', '', parameter)
        
        # 提取类型（处理泛型）
        match = re.match(r'([\w.<>[\]]+)', param.strip())
        if match:
            type_str = match.group(1)
            # 处理泛型，提取主要类型
            if '<' in type_str:
                type_str = type_str.split('<')[0]
            # 处理数组
            type_str = type_str.replace('[]', '')
            return type_str
        
        return None
    
    def _extract_simple_type(self, type_str: str) -> str:
        """提取简单类型名"""
        # 移除泛型
        if '<' in type_str:
            type_str = type_str.split('<')[0]
        # 移除数组标记
        type_str = type_str.replace('[]', '')
        # 获取简单类名
        if '.' in type_str:
            return type_str.split('.')[-1]
        return type_str
    
    def _is_project_class(self, class_name: str) -> bool:
        """判断是否是项目内的类"""
        if not class_name:
            return False
        
        # 检查是否是基本类型
        basic_types = {'int', 'long', 'double', 'float', 'boolean', 'char', 'byte', 'short', 'String'}
        if class_name in basic_types:
            return False
        
        # 检查是否是Java标准库类
        if class_name.startswith('java.') or class_name.startswith('javax.'):
            return False
        
        # 检查数据库中是否存在
        classes = self.db.get_class_by_simple_name(class_name)
        return len(classes) > 0
    
    def _analyze_dependency(self, class_name: str) -> Optional[DependencyContext]:
        """分析单个依赖"""
        # 首先检查是否是常见的第三方类型
        common_type_info = self._get_common_type_constructor_info(class_name)
        if common_type_info:
            return common_type_info

        # 然后检查项目内的类
        classes = self.db.get_class_by_simple_name(class_name)
        if not classes:
            return None

        # 选择最匹配的类（优先选择项目内的类）
        target_class = None
        for cls in classes:
            if self.project_group_id and cls.package.startswith(self.project_group_id):
                target_class = cls
                break

        if not target_class:
            target_class = classes[0]
        
        # 分析构造器
        public_constructors = []
        for constructor in target_class.constructors:
            if constructor.access_modifier == "public":
                params = ", ".join(constructor.parameters)
                public_constructors.append(f"public {target_class.simple_name}({params})")
        
        # 分析静态工厂方法
        static_factory_methods = []
        for method in target_class.methods:
            if (method.is_static and 
                method.access_modifier == "public" and
                method.return_type == target_class.simple_name):
                params = ", ".join(method.parameters)
                static_factory_methods.append(f"public static {method.return_type} {method.name}({params})")
        
        # 判断是否可以Mock
        is_mockable = (target_class.class_type in ["interface", "abstract_class"] or
                      len(public_constructors) == 0)
        
        # 生成实例化指导
        instantiation_guide = self._generate_instantiation_guide(
            target_class, public_constructors, static_factory_methods, is_mockable
        )
        
        return DependencyContext(
            dependency_fqn=target_class.fully_qualified_name,
            dependency_type=target_class.class_type,
            public_constructors=public_constructors,
            static_factory_methods=static_factory_methods,
            is_mockable=is_mockable,
            instantiation_guide=instantiation_guide
        )
    
    def _generate_instantiation_guide(self, class_index: ClassIndex, 
                                    public_constructors: List[str],
                                    static_factory_methods: List[str],
                                    is_mockable: bool) -> str:
        """生成实例化指导"""
        guides = []
        
        if is_mockable:
            guides.append(f"// {class_index.simple_name} 建议使用Mock")
            guides.append(f"@Mock")
            guides.append(f"private {class_index.simple_name} {class_index.simple_name.lower()}Mock;")
        
        if public_constructors:
            guides.append(f"// {class_index.simple_name} 可用构造器:")
            for constructor in public_constructors:
                guides.append(f"// {constructor}")
        
        if static_factory_methods:
            guides.append(f"// {class_index.simple_name} 静态工厂方法:")
            for method in static_factory_methods:
                guides.append(f"// {method}")
        
        return "\n".join(guides)
    
    def _generate_import_statements(self, target_class: ClassIndex,
                                  dependency_contexts: List[DependencyContext],
                                  core_context: CoreCodeContext) -> List[str]:
        """生成导入语句"""
        imports = set()

        # 添加目标类的导入
        imports.add(f"import {target_class.fully_qualified_name};")

        # 添加依赖类的导入
        for dep_context in dependency_contexts:
            imports.add(f"import {dep_context.dependency_fqn};")

        # 添加方法实现中使用的类的导入
        used_class_imports = {
            "MessageDigest": "import java.security.MessageDigest;",
            "BigInteger": "import java.math.BigInteger;",
            "StringBuilder": "import java.lang.StringBuilder;",
            "Arrays": "import java.util.Arrays;",
            "List": "import java.util.List;",
            "ArrayList": "import java.util.ArrayList;",
            "Map": "import java.util.Map;",
            "HashMap": "import java.util.HashMap;",
            "Set": "import java.util.Set;",
            "HashSet": "import java.util.HashSet;",
            "Date": "import java.util.Date;",
            "LocalDate": "import java.time.LocalDate;",
            "LocalDateTime": "import java.time.LocalDateTime;",
            "Pattern": "import java.util.regex.Pattern;",
            "Matcher": "import java.util.regex.Matcher;",
            "File": "import java.io.File;",
            "Path": "import java.nio.file.Path;",
            "Files": "import java.nio.file.Files;"
        }

        # 从核心上下文获取使用的类
        for used_class in core_context.used_classes:
            if used_class in used_class_imports:
                imports.add(used_class_imports[used_class])

        # 分析方法参数和返回类型的导入需求
        method_type_imports = self._analyze_method_type_imports(core_context)
        imports.update(method_type_imports)

        # 添加测试框架导入（根据类类型决定是否包含Mock）
        # 使用真实注解检测而不是构造函数数量
        actual_annotations = self._get_actual_class_annotations(target_class.fully_qualified_name)
        is_utility_class = any('@UtilityClass' in ann for ann in actual_annotations)

        if is_utility_class:
            # @UtilityClass - 不需要Mock
            test_imports = [
                "import org.junit.jupiter.api.Test;",
                "import org.junit.jupiter.api.BeforeEach;",
                "import org.junit.jupiter.api.AfterEach;",
                "import static org.junit.jupiter.api.Assertions.*;"
            ]
        else:
            # 普通类 - 可能需要Mock
            test_imports = [
                "import org.junit.jupiter.api.Test;",
                "import org.junit.jupiter.api.BeforeEach;",
                "import org.junit.jupiter.api.AfterEach;",
                "import org.junit.jupiter.api.extension.ExtendWith;",
                "import org.mockito.Mock;",
                "import org.mockito.InjectMocks;",
                "import org.mockito.junit.jupiter.MockitoExtension;",
                "import static org.junit.jupiter.api.Assertions.*;",
                "import static org.mockito.Mockito.*;"
            ]

        imports.update(test_imports)

        return sorted(list(imports))

    def format_for_prompt(self, context: ContextAwareTestContext) -> List[Dict]:
        """将Context-Aware上下文格式化为适合LLM的格式"""
        formatted_contexts = []

        # 1. 核心代码上下文
        core_content = self._format_core_context(context.core_context)
        formatted_contexts.append({
            'content': core_content,
            'metadata': {
                'type': 'core_context',
                'class_name': context.core_context.target_class_fqn,
                'method_name': context.core_context.target_method_signature.split('(')[0].split()[-1]
            },
            'distance': 0.0
        })

        # 2. 类注解和特殊信息上下文
        class_info_content = self._format_class_info_context(context.core_context)
        if class_info_content:
            formatted_contexts.append({
                'content': class_info_content,
                'metadata': {
                    'type': 'class_info',
                    'class_name': context.core_context.target_class_fqn
                },
                'distance': 0.0
            })

        # 3. 导入语句上下文
        import_content = self._format_import_context(context.import_statements)
        formatted_contexts.append({
            'content': import_content,
            'metadata': {
                'type': 'imports',
                'import_count': len(context.import_statements)
            },
            'distance': 0.0
        })

        # 4. 依赖上下文
        if context.dependency_contexts:
            dependency_content = self._format_dependency_context(context.dependency_contexts)
            formatted_contexts.append({
                'content': dependency_content,
                'metadata': {
                    'type': 'dependency_context',
                    'dependency_count': len(context.dependency_contexts)
                },
                'distance': 0.0
            })

        return formatted_contexts

    def _format_core_context(self, core_context: CoreCodeContext) -> str:
        """格式化核心代码上下文，使用与RAG模式一致的简洁格式"""
        lines = []
        lines.append(f"Method: {core_context.target_method_signature}")
        lines.append("")
        lines.append("Implementation:")

        # 添加类注解信息（如果有），不使用格式化标记
        if hasattr(core_context, 'class_annotations') and core_context.class_annotations:
            for annotation in core_context.class_annotations:
                # 移除任何格式化标记
                clean_annotation = annotation.strip()
                if not clean_annotation.startswith('#') and clean_annotation:
                    lines.append(clean_annotation)

        # 方法实现（完全移除格式化标记）
        if core_context.target_method_implementation:
            implementation = core_context.target_method_implementation
            # 移除所有格式化标记
            implementation = implementation.replace('## 类注解信息', '')
            implementation = implementation.replace('## 完整方法实现', '')
            implementation = implementation.replace('```java', '')
            implementation = implementation.replace('```', '')
            # 清理多余的空行
            clean_lines = []
            for line in implementation.split('\n'):
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    clean_lines.append(line)

            if clean_lines:
                lines.extend(clean_lines)

        # 添加类的其他方法签名信息
        other_methods_info = self._get_class_other_methods_info(core_context.target_class_fqn, core_context.target_method_signature)
        if other_methods_info:
            lines.append("")
            lines.append("Other methods in this class:")
            lines.extend(other_methods_info)

        return '\n'.join(lines)

    def _get_class_other_methods_info(self, class_fqn: str, target_method_signature: str) -> List[str]:
        """获取类的其他方法签名信息（排除目标方法）"""
        try:
            # 从数据库获取类信息
            class_index = self.project_index.get_class_by_fqn(class_fqn)
            if not class_index:
                return []

            method_lines = []

            # 添加构造方法信息
            if class_index.constructors:
                method_lines.append("Constructors:")
                for constructor in class_index.constructors:
                    # 参数是字符串列表，直接使用
                    params = ", ".join(constructor.parameters) if constructor.parameters else ""
                    signature = f"  {constructor.access_modifier} {class_index.simple_name}({params})"
                    if constructor.exceptions:
                        exceptions = ", ".join(constructor.exceptions)
                        signature += f" throws {exceptions}"
                    method_lines.append(signature)
                method_lines.append("")

            # 添加其他方法信息（排除目标方法）
            if class_index.methods:
                other_methods = []
                target_method_name = target_method_signature.split('(')[0].split()[-1]  # 提取方法名

                for method in class_index.methods:
                    # 跳过目标方法
                    if method.name == target_method_name:
                        continue

                    # 参数是字符串列表，直接使用
                    params = ", ".join(method.parameters) if method.parameters else ""
                    modifiers = []
                    if method.is_static:
                        modifiers.append("static")
                    if method.is_final:
                        modifiers.append("final")
                    if method.is_abstract:
                        modifiers.append("abstract")

                    modifier_str = " ".join(modifiers)
                    if modifier_str:
                        modifier_str = " " + modifier_str

                    signature = f"  {method.access_modifier}{modifier_str} {method.return_type} {method.name}({params})"
                    if method.exceptions:
                        exceptions = ", ".join(method.exceptions)
                        signature += f" throws {exceptions}"

                    other_methods.append(signature)

                if other_methods:
                    method_lines.append("Other methods:")
                    method_lines.extend(other_methods)

            return method_lines

        except Exception as e:
            print(f"Warning: Failed to get class methods info: {e}")
            return []

    def _format_class_info_context(self, core_context: CoreCodeContext) -> str:
        """格式化类信息上下文，使用简洁格式"""
        lines = []
        class_name = core_context.target_class_fqn.split('.')[-1]
        package_name = '.'.join(core_context.target_class_fqn.split('.')[:-1])

        # 获取真实的类注解信息
        actual_annotations = self._get_actual_class_annotations(core_context.target_class_fqn)

        # 检查是否真的是@UtilityClass（基于实际注解，不是构造函数）
        is_utility_class = any('@UtilityClass' in ann for ann in actual_annotations)

        if is_utility_class:
            lines.append(f"class {class_name} in package {package_name} with annotations: @UtilityClass")
            lines.append("")
            lines.append("SPECIAL INSTRUCTIONS FOR @UtilityClass:")
            lines.append("- This class cannot be instantiated")
            lines.append("- All methods are static methods")
            lines.append("- DO NOT use @InjectMocks or @Mock annotations")
            lines.append("- Call methods directly: ClassName.methodName(params)")
            lines.append("- DO NOT create instances with 'new ClassName()'")
        else:
            # 使用实际获取的注解信息
            if actual_annotations:
                lines.append(f"class {class_name} in package {package_name} with annotations: {', '.join(actual_annotations)}")
            else:
                # 如果没有获取到注解，检查是否有构造器（可能是@Component）
                annotations = []
                if core_context.target_class_constructors:
                    annotations.append("@Component")

                if annotations:
                    lines.append(f"class {class_name} in package {package_name} with annotations: {', '.join(annotations)}")

        # 添加字段信息（特别是final字段，这些通常是依赖）
        try:
            target_class = self.db.get_class_by_fqn(core_context.target_class_fqn)
            if target_class and target_class.fields:
                final_fields = [f for f in target_class.fields if f.is_final and f.access_modifier == "private"]
                if final_fields:
                    lines.append("")
                    lines.append("Class fields:")
                    for field in final_fields:
                        field_type = self._extract_simple_type(field.type)
                        lines.append(f"  private final {field_type} {field.name};")
        except Exception as e:
            logger.debug(f"获取字段信息失败: {e}")

        # 如果没有任何信息，至少显示基本的类信息
        if not lines:
            lines.append(f"class {class_name} in package {package_name}")

        return '\n'.join(lines)

    def _get_actual_class_annotations(self, class_fqn: str) -> List[str]:
        """获取类的真实注解信息"""
        try:
            # 首先尝试从项目索引获取类信息
            class_index = self.project_index.get_class_by_fqn(class_fqn)
            if class_index and hasattr(class_index, 'annotations') and class_index.annotations:
                return class_index.annotations

            # 如果项目索引中没有注解信息，直接从源文件读取
            if class_index and hasattr(class_index, 'file_path') and class_index.file_path:
                try:
                    # 确保路径是Path对象，并相对于项目根目录解析
                    from pathlib import Path
                    class_file_path = class_index.file_path
                    if isinstance(class_file_path, str):
                        class_file_path = Path(class_file_path)

                    # 如果是相对路径，相对于项目根目录解析
                    if not class_file_path.is_absolute():
                        class_file_path = Path(self.project_path) / class_file_path

                    if class_file_path.exists():
                        # 读取文件内容
                        with open(class_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 使用现有的_extract_class_annotations方法
                        return self._extract_class_annotations(content)
                except Exception as file_e:
                    logger.debug(f"从源文件读取注解失败: {file_e}")

            # 如果以上方法都失败，尝试从数据库获取
            try:
                class_info = self.project_index.get_class_info(class_fqn)
                if class_info and isinstance(class_info, dict):
                    # 首先检查是否有annotations字段
                    if 'annotations' in class_info and class_info['annotations']:
                        return class_info['annotations']

                    # 如果没有，尝试解析源代码
                    source_code = class_info.get('source_code', '')
                    if source_code:
                        return self._extract_class_annotations(source_code)
            except Exception as inner_e:
                logger.debug(f"从数据库获取类信息失败: {inner_e}")

            return []
        except Exception as e:
            logger.warning(f"获取类注解失败: {e}")
            return []

    def _analyze_method_type_imports(self, core_context: CoreCodeContext) -> Set[str]:
        """分析方法参数和返回类型的导入需求"""
        imports = set()

        try:
            # 从方法签名中提取类型信息
            signature = core_context.target_method_signature
            if not signature:
                return imports

            # 解析方法签名中的类型
            import re

            # 提取参数类型
            param_pattern = r'(\w+(?:\.\w+)*)\s+\w+'
            param_matches = re.findall(param_pattern, signature)

            for param_type in param_matches:
                import_stmt = self._get_import_for_type(param_type)
                if import_stmt:
                    imports.add(import_stmt)

            # 从方法实现中提取使用的类型
            implementation = core_context.target_method_implementation or ""

            # 查找常见的类型使用模式
            type_patterns = [
                r'new\s+(\w+(?:\.\w+)*)\s*\(',  # new ClassName()
                r'(\w+(?:\.\w+)*)\s*\.\s*\w+',  # ClassName.method()
                r'List<(\w+(?:\.\w+)*)>',       # List<Type>
                r'Map<\w+,\s*(\w+(?:\.\w+)*)>', # Map<Key, Value>
            ]

            for pattern in type_patterns:
                matches = re.findall(pattern, implementation)
                for match in matches:
                    import_stmt = self._get_import_for_type(match)
                    if import_stmt:
                        imports.add(import_stmt)

        except Exception as e:
            logger.warning(f"分析方法类型导入失败: {e}")

        return imports

    def _get_import_for_type(self, type_name: str) -> Optional[str]:
        """根据类型名获取对应的导入语句"""
        # 跳过基本类型和java.lang包中的类
        if type_name in ['int', 'long', 'double', 'float', 'boolean', 'char', 'byte', 'short',
                        'String', 'Object', 'Integer', 'Long', 'Double', 'Float', 'Boolean']:
            return None

        # 检查是否是项目内的类
        try:
            # 尝试在项目索引中查找
            all_classes = self.project_index.get_all_classes()
            for class_info in all_classes:
                class_name = class_info.get('fully_qualified_name', '').split('.')[-1]
                if class_name == type_name:
                    return f"import {class_info.get('fully_qualified_name')};"

            # 检查常见的第三方库类型
            common_imports = {
                'List': 'import java.util.List;',
                'ArrayList': 'import java.util.ArrayList;',
                'Map': 'import java.util.Map;',
                'HashMap': 'import java.util.HashMap;',
                'Set': 'import java.util.Set;',
                'HashSet': 'import java.util.HashSet;',
                'Optional': 'import java.util.Optional;',
                'Stream': 'import java.util.stream.Stream;',
                'Collectors': 'import java.util.stream.Collectors;',
                'Arrays': 'import java.util.Arrays;',
                'Date': 'import java.util.Date;',
                'LocalDate': 'import java.time.LocalDate;',
                'LocalDateTime': 'import java.time.LocalDateTime;',
                'BigDecimal': 'import java.math.BigDecimal;',
                'BigInteger': 'import java.math.BigInteger;',
                'Pattern': 'import java.util.regex.Pattern;',
                'Matcher': 'import java.util.regex.Matcher;',
                'File': 'import java.io.File;',
                'Path': 'import java.nio.file.Path;',
                'Files': 'import java.nio.file.Files;',
                'PdfContentByte': 'import com.itextpdf.text.pdf.PdfContentByte;',
                'BaseColor': 'import com.itextpdf.text.BaseColor;',
                'Rectangle': 'import com.itextpdf.text.Rectangle;',
                'ImageChunk': 'import com.example.pdfcompare.model.ImageChunk;',
                'TextChunk': 'import com.example.pdfcompare.model.TextChunk;',
                'PDFPageComparator': 'import com.example.pdfcompare.util.PDFPageComparator;',
                'PageComparator': 'import com.example.pdfcompare.util.PDFPageComparator;',
                'InputStream': 'import java.io.InputStream;',
                'OutputStream': 'import java.io.OutputStream;',
                'ByteArrayInputStream': 'import java.io.ByteArrayInputStream;',
                'ByteArrayOutputStream': 'import java.io.ByteArrayOutputStream;',
                'IOException': 'import java.io.IOException;',
                'DocumentException': 'import com.itextpdf.text.DocumentException;',
                'Document': 'import com.itextpdf.text.Document;',
                'PdfReader': 'import com.itextpdf.text.pdf.PdfReader;',
                'PdfWriter': 'import com.itextpdf.text.pdf.PdfWriter;',
                'PdfImportedPage': 'import com.itextpdf.text.pdf.PdfImportedPage;',
                'MockitoExtension': 'import org.mockito.junit.jupiter.MockitoExtension;',
                'IOException': 'import java.io.IOException;',
            }

            return common_imports.get(type_name)

        except Exception as e:
            logger.warning(f"获取类型导入失败: {type_name}, {e}")
            return None

    def _format_import_context(self, import_statements: List[str]) -> str:
        """格式化导入语句上下文，使用简洁格式"""
        # 过滤掉不适合@UtilityClass的导入
        filtered_imports = []
        excluded_imports = ['@InjectMocks', '@Mock', 'MockitoExtension', 'InjectMocks', 'Mock']

        for import_stmt in import_statements:
            should_exclude = False
            for excluded in excluded_imports:
                if excluded in import_stmt:
                    should_exclude = True
                    break

            if not should_exclude:
                filtered_imports.append(import_stmt)

        return '\n'.join(sorted(filtered_imports))

    def _format_dependency_context(self, dependency_contexts: List[DependencyContext]) -> str:
        """格式化依赖上下文，使用简洁格式"""
        lines = []

        for i, dep in enumerate(dependency_contexts, 1):
            class_name = dep.dependency_fqn.split('.')[-1]
            lines.append(f"{i}. {class_name} ({dep.dependency_type}):")

            if dep.public_constructors:
                lines.append("   Constructors:")
                for constructor in dep.public_constructors:
                    lines.append(f"   - {constructor}")

            if dep.static_factory_methods:
                lines.append("   Factory methods:")
                for method in dep.static_factory_methods:
                    lines.append(f"   - {method}")

            if dep.instantiation_guide:
                lines.append(f"   Usage: {dep.instantiation_guide}")

            if i < len(dependency_contexts):
                lines.append("")

        return '\n'.join(lines)

    def _get_common_type_constructor_info(self, class_name: str) -> Optional[DependencyContext]:
        """获取常见类型的构造函数信息"""
        common_types = {
            'ImageChunk': DependencyContext(
                dependency_fqn='com.example.pdfcompare.model.ImageChunk',
                dependency_type='record',
                public_constructors=['ImageChunk(String imageHash, Rectangle rectangle)'],
                static_factory_methods=[],
                is_mockable=True,
                instantiation_guide='new ImageChunk("hash", new Rectangle(0, 0, 100, 100))'
            ),
            'PdfContentByte': DependencyContext(
                dependency_fqn='com.itextpdf.text.pdf.PdfContentByte',
                dependency_type='class',
                public_constructors=['PdfContentByte(PdfWriter writer)'],
                static_factory_methods=[],
                is_mockable=True,
                instantiation_guide='Use @Mock annotation for testing'
            ),
            'BaseColor': DependencyContext(
                dependency_fqn='com.itextpdf.text.BaseColor',
                dependency_type='class',
                public_constructors=[
                    'BaseColor(int red, int green, int blue)',
                    'BaseColor(int red, int green, int blue, int alpha)',
                    'BaseColor(float red, float green, float blue)',
                    'BaseColor(float red, float green, float blue, float alpha)'
                ],
                static_factory_methods=['BaseColor.RED', 'BaseColor.GREEN', 'BaseColor.BLUE'],
                is_mockable=True,
                instantiation_guide='BaseColor.RED or new BaseColor(255, 0, 0)'
            ),
            'Rectangle': DependencyContext(
                dependency_fqn='com.itextpdf.text.Rectangle',
                dependency_type='class',
                public_constructors=[
                    'Rectangle(float llx, float lly, float urx, float ury)',
                    'Rectangle(Rectangle rect)'
                ],
                static_factory_methods=[],
                is_mockable=True,
                instantiation_guide='new Rectangle(0, 0, 100, 100)'
            ),
            # 添加更多项目特定的类型
            'PDFPageComparator': DependencyContext(
                dependency_fqn='com.example.pdfcompare.util.PDFPageComparator',
                dependency_type='class',
                public_constructors=['PDFPageComparator(TextComparator textComparator, ImageComparator imageComparator, PDFHighlighter pdfHighlighter, PDFTextExtractor pdfTextExtractor, PDFImageExtractor pdfImageExtractor)'],
                static_factory_methods=[],
                is_mockable=True,
                instantiation_guide='Use @Mock annotation for testing'
            ),
            'PageComparator': DependencyContext(
                dependency_fqn='com.example.pdfcompare.util.PDFPageComparator',
                dependency_type='class',
                public_constructors=['PDFPageComparator(TextComparator textComparator, ImageComparator imageComparator, PDFHighlighter pdfHighlighter, PDFTextExtractor pdfTextExtractor, PDFImageExtractor pdfImageExtractor)'],
                static_factory_methods=[],
                is_mockable=True,
                instantiation_guide='Use @Mock annotation for testing. Note: Actual class name is PDFPageComparator'
            ),
            # 添加Java标准库类型
            'InputStream': DependencyContext(
                dependency_fqn='java.io.InputStream',
                dependency_type='abstract class',
                public_constructors=[],
                static_factory_methods=[],
                is_mockable=True,
                instantiation_guide='Use ByteArrayInputStream for testing: new ByteArrayInputStream("test".getBytes())'
            ),
            'OutputStream': DependencyContext(
                dependency_fqn='java.io.OutputStream',
                dependency_type='abstract class',
                public_constructors=[],
                static_factory_methods=[],
                is_mockable=True,
                instantiation_guide='Use ByteArrayOutputStream for testing: new ByteArrayOutputStream()'
            )
        }

        return common_types.get(class_name)

    def enhance_context_from_compilation_errors(self, error_output: str,
                                               existing_contexts: List[Dict]) -> List[Dict]:
        """从编译错误中增强上下文"""
        try:
            enhanced_contexts = self.error_enhancer.enhance_context_from_errors(
                error_output, error_type='compilation'
            )

            # 合并现有上下文和增强上下文，避免重复
            existing_content = {ctx.get('content', '') for ctx in existing_contexts}
            new_contexts = []

            for ctx in enhanced_contexts:
                if ctx.get('content', '') not in existing_content:
                    new_contexts.append(ctx)
                    existing_content.add(ctx.get('content', ''))

            if new_contexts:
                logger.info(f"从编译错误中增强了 {len(new_contexts)} 个上下文")
                return existing_contexts + new_contexts

            return existing_contexts

        except Exception as e:
            logger.error(f"从编译错误增强上下文失败: {e}")
            return existing_contexts

    def enhance_context_from_runtime_errors(self, error_output: str,
                                           existing_contexts: List[Dict]) -> List[Dict]:
        """从运行时错误中增强上下文"""
        try:
            enhanced_contexts = self.error_enhancer.enhance_context_from_errors(
                error_output, error_type='runtime'
            )

            # 合并现有上下文和增强上下文，避免重复
            existing_content = {ctx.get('content', '') for ctx in existing_contexts}
            new_contexts = []

            for ctx in enhanced_contexts:
                if ctx.get('content', '') not in existing_content:
                    new_contexts.append(ctx)
                    existing_content.add(ctx.get('content', ''))

            if new_contexts:
                logger.info(f"从运行时错误中增强了 {len(new_contexts)} 个上下文")
                return existing_contexts + new_contexts

            return existing_contexts

        except Exception as e:
            logger.error(f"从运行时错误增强上下文失败: {e}")
            return existing_contexts
