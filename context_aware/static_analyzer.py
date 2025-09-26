#!/usr/bin/env python3
"""
静态代码分析器
用于扫描整个项目并构建类索引
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime

from .project_index import (
    ClassIndex, MethodSignature, ConstructorSignature, FieldSignature,
    ProjectIndexDatabase
)

logger = logging.getLogger(__name__)

class JavaStaticAnalyzer:
    """Java静态代码分析器"""
    
    def __init__(self, project_path: str, db_path: str = "./project_index.db"):
        self.project_path = Path(project_path)
        self.db = ProjectIndexDatabase(db_path)
        
        # 编译正则表达式
        self.package_pattern = re.compile(r'package\s+([\w.]+);')
        self.import_pattern = re.compile(r'import\s+(static\s+)?([\w.*]+);')
        self.class_pattern = re.compile(
            r'(?:^|\n)\s*(?:@[\w.()=",\s]+\s+)*'
            r'(public|private|protected|)\s*'
            r'(?:(static|final|abstract)\s+)*'
            r'(class|interface|enum|record)\s+'
            r'(\w+)'
            r'(?:\s+extends\s+([\w.<>]+))?'
            r'(?:\s+implements\s+([\w.<>,\s]+))?'
            r'\s*\{',
            re.MULTILINE
        )
        self.method_pattern = re.compile(
            r'(?:^|\n)\s*(?:@[\w.()=",\s]+\s+)*'
            r'(public|private|protected|)\s*'
            r'(?:(static|final|abstract|synchronized)\s+)*'
            r'(?:<[^>]+>\s+)?'  # 泛型
            r'([\w.<>[\]]+)\s+'  # 返回类型
            r'(\w+)\s*'  # 方法名
            r'\(([^)]*(?:\([^)]*\)[^)]*)*)\)'  # 参数（支持嵌套括号）
            r'(?:\s+throws\s+([\w.,\s]+))?'  # 异常
            r'\s*[{;]',
            re.MULTILINE | re.DOTALL
        )
        self.constructor_pattern = re.compile(
            r'(?:^|\n)\s*(?:@[\w.()=",\s]+\s+)*'
            r'(public|private|protected|)\s*'
            r'(\w+)\s*'  # 构造器名（应该与类名相同）
            r'\(([^)]*)\)'  # 参数
            r'(?:\s+throws\s+([\w.,\s]+))?'  # 异常
            r'\s*\{',
            re.MULTILINE
        )
        self.field_pattern = re.compile(
            r'(?:^|\n)\s*(?:@[\w.()=",\s]+\s+)*'
            r'(public|private|protected|)\s*'
            r'(?:(static|final|volatile|transient)\s+)*'
            r'([\w.<>[\]]+)\s+'  # 字段类型
            r'(\w+)'  # 字段名
            r'(?:\s*=\s*[^;]+)?'  # 初始值（可选）
            r'\s*;',
            re.MULTILINE
        )
        self.annotation_pattern = re.compile(r'@([\w.]+)(?:\([^)]*\))?')

    def analyze_project_structure_only(self, project_path: str) -> Dict[str, Any]:
        """仅分析项目结构，不依赖向量存储"""
        logger.info(f"开始分析项目结构: {project_path}")

        project_path = Path(project_path)
        java_files = list(project_path.rglob("*.java"))

        logger.info(f"找到 {len(java_files)} 个Java文件")

        stats = {
            'files_processed': 0,
            'classes_found': 0,
            'methods_found': 0,
            'total_files': len(java_files)
        }

        for java_file in java_files:
            try:
                # 简单解析文件，提取基本信息
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取包名
                package_match = self.package_pattern.search(content)
                package = package_match.group(1) if package_match else ""

                # 提取类信息
                class_matches = self.class_pattern.findall(content)
                for match in class_matches:
                    access_modifier, modifiers, class_type, class_name, extends, implements = match

                    # 构建类信息
                    class_data = {
                        'simple_name': class_name,
                        'fully_qualified_name': f"{package}.{class_name}" if package else class_name,
                        'package': package,
                        'file_path': str(java_file),
                        'access_modifier': access_modifier or 'package',
                        'class_type': class_type,
                        'extends': extends or None,
                        'implements': implements.split(',') if implements else [],
                        'annotations': [],
                        'inner_classes': [],
                        'imports': [],
                        'last_modified': datetime.fromtimestamp(java_file.stat().st_mtime).isoformat()
                    }

                    # 插入到数据库
                    self.db.insert_class(class_data)
                    stats['classes_found'] += 1

                    # 提取方法信息
                    method_matches = self.method_pattern.findall(content)
                    for method_match in method_matches:
                        access_mod, modifiers, return_type, method_name, params, exceptions = method_match

                        method_data = {
                            'class_fqn': class_data['fully_qualified_name'],
                            'name': method_name,
                            'access_modifier': access_mod or 'package',
                            'return_type': return_type,
                            'parameters': [p.strip() for p in params.split(',') if p.strip()],
                            'signature': f"{access_mod or 'package'} {return_type} {method_name}({params})",
                            'annotations': [],
                            'exceptions': exceptions.split(',') if exceptions else [],
                            'is_static': 'static' in (modifiers or ''),
                            'is_abstract': 'abstract' in (modifiers or ''),
                            'is_final': 'final' in (modifiers or '')
                        }

                        self.db.insert_method(method_data)
                        stats['methods_found'] += 1

                stats['files_processed'] += 1

            except Exception as e:
                logger.warning(f"分析文件失败 {java_file}: {e}")

        return stats

    def analyze_project(self, force_reindex: bool = False) -> Dict:
        """分析整个项目"""
        logger.info(f"开始分析项目: {self.project_path}")
        
        stats = {
            'files_processed': 0,
            'classes_found': 0,
            'methods_found': 0,
            'constructors_found': 0,
            'fields_found': 0,
            'errors': []
        }
        
        # 查找所有Java文件
        java_files = list(self.project_path.rglob("*.java"))
        logger.info(f"找到 {len(java_files)} 个Java文件")
        
        for java_file in java_files:
            try:
                if self._should_process_file(java_file, force_reindex):
                    class_indexes = self._analyze_file(java_file)
                    
                    for class_index in class_indexes:
                        self.db.insert_class_index(class_index)
                        stats['classes_found'] += 1
                        stats['methods_found'] += len(class_index.methods)
                        stats['constructors_found'] += len(class_index.constructors)
                        stats['fields_found'] += len(class_index.fields)
                    
                    stats['files_processed'] += 1
                    
            except Exception as e:
                error_msg = f"分析文件失败 {java_file}: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        logger.info(f"项目分析完成: {stats}")
        return stats
    
    def _should_process_file(self, java_file: Path, force_reindex: bool) -> bool:
        """判断是否需要处理文件"""
        if force_reindex:
            return True
        
        # 检查文件修改时间
        file_mtime = datetime.fromtimestamp(java_file.stat().st_mtime).isoformat()
        
        # 从文件路径推断类名和包名
        relative_path = java_file.relative_to(self.project_path)
        if not str(relative_path).startswith('src/'):
            return True  # 不在标准目录结构中，重新处理
        
        # 简单的类名推断
        class_name = java_file.stem
        
        # 检查数据库中是否存在且是最新的
        existing_classes = self.db.get_class_by_simple_name(class_name)
        for existing_class in existing_classes:
            if (existing_class.file_path == str(relative_path) and 
                existing_class.last_modified >= file_mtime):
                return False  # 文件未修改，跳过
        
        return True
    
    def _analyze_file(self, java_file: Path) -> List[ClassIndex]:
        """分析单个Java文件"""
        logger.debug(f"分析文件: {java_file}")
        
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(java_file, 'r', encoding='gbk') as f:
                content = f.read()
        
        # 提取基本信息
        package = self._extract_package(content)
        imports = self._extract_imports(content)
        file_mtime = datetime.fromtimestamp(java_file.stat().st_mtime).isoformat()
        relative_path = java_file.relative_to(self.project_path)
        
        # 查找所有类定义
        class_indexes = []
        class_matches = self.class_pattern.finditer(content)
        
        for match in class_matches:
            try:
                class_index = self._parse_class_definition(
                    match, content, package, imports, str(relative_path), file_mtime
                )
                if class_index:
                    class_indexes.append(class_index)
            except Exception as e:
                logger.error(f"解析类定义失败 {java_file}: {e}")
        
        return class_indexes
    
    def _extract_package(self, content: str) -> str:
        """提取包名"""
        match = self.package_pattern.search(content)
        return match.group(1) if match else ""
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取导入语句"""
        imports = []
        for match in self.import_pattern.finditer(content):
            import_stmt = match.group(2)
            if match.group(1):  # static import
                import_stmt = f"static {import_stmt}"
            imports.append(import_stmt)
        return imports
    
    def _parse_class_definition(self, match, content: str, package: str,
                              imports: List[str], file_path: str,
                              last_modified: str) -> Optional[ClassIndex]:
        """解析类定义"""
        access_modifier = match.group(1) or "package"
        modifiers = match.group(2) or ""
        class_type = match.group(3)
        class_name = match.group(4)
        extends = match.group(5)
        implements_str = match.group(6)

        # 处理implements
        implements = []
        if implements_str:
            implements = [impl.strip() for impl in implements_str.split(',')]

        # 确定类类型
        if "abstract" in modifiers:
            class_type = "abstract_class"

        # 构建完全限定名
        fqn = f"{package}.{class_name}" if package else class_name

        # 提取类体 - 从类定义开始位置查找
        class_body = self._extract_class_body(content, match.start())

        # 提取注解
        annotations = self._extract_annotations_before_position(content, match.start())

        # 分析类成员 - 直接从完整内容中分析，而不是从类体
        constructors = self._extract_constructors_from_content(content, class_name, match.start(), match.end())
        methods = self._extract_methods_from_content(content, class_name, match.start(), match.end())
        fields = self._extract_fields(class_body)

        return ClassIndex(
            simple_name=class_name,
            fully_qualified_name=fqn,
            package=package,
            file_path=file_path,
            access_modifier=access_modifier,
            class_type=class_type,
            extends=extends,
            implements=implements,
            annotations=annotations,
            constructors=constructors,
            methods=methods,
            fields=fields,
            imports=imports,
            last_modified=last_modified
        )
    
    def _extract_class_body(self, content: str, class_start_pos: int) -> str:
        """提取类体内容，包括方法签名"""
        # 从类定义开始查找第一个{
        start_brace_pos = content.find('{', class_start_pos)
        if start_brace_pos == -1:
            return ""

        # 找到类体的结束}
        brace_count = 0
        pos = start_brace_pos
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    # 返回从{到}的完整内容，包括方法签名
                    return content[start_brace_pos:pos+1]
            pos += 1

        return content[start_brace_pos:]
    
    def _extract_annotations_before_position(self, content: str, pos: int) -> List[str]:
        """提取指定位置之前的注解"""
        # 向前查找注解
        lines_before = content[:pos].split('\n')
        annotations = []
        
        for line in reversed(lines_before[-10:]):  # 只检查前10行
            line = line.strip()
            if line.startswith('@'):
                match = self.annotation_pattern.search(line)
                if match:
                    annotations.insert(0, match.group(1))
            elif line and not line.startswith('//') and not line.startswith('/*'):
                break  # 遇到非注解、非空行、非注释行就停止
        
        return annotations
    
    def _extract_constructors(self, class_body: str, class_name: str) -> List[ConstructorSignature]:
        """提取构造器"""
        constructors = []

        # 使用清理后的代码
        cleaned_body = self._clean_multiline_signatures(class_body)

        for match in self.constructor_pattern.finditer(cleaned_body):
            constructor_name = match.group(2)
            if constructor_name == class_name:  # 确保是构造器
                access_modifier = match.group(1) or "package"
                parameters_str = match.group(3) or ""
                exceptions_str = match.group(4) or ""

                parameters = self._parse_parameters(parameters_str)
                exceptions = self._parse_exceptions(exceptions_str)

                constructors.append(ConstructorSignature(
                    access_modifier=access_modifier,
                    parameters=parameters,
                    exceptions=exceptions
                ))

        # 如果没有找到显式构造器，检查是否有@RequiredArgsConstructor等Lombok注解
        if not constructors:
            constructors.extend(self._extract_lombok_constructors(class_body, class_name))

        return constructors

    def _extract_lombok_constructors(self, class_body: str, class_name: str) -> List[ConstructorSignature]:
        """提取Lombok生成的构造器"""
        constructors = []

        # 检查类级别的注解
        class_annotations = self._extract_annotations_before_position(class_body, 0)

        if 'RequiredArgsConstructor' in class_annotations:
            # 查找final字段作为构造器参数
            final_fields = []
            for field in self._extract_fields(class_body):
                if field.is_final and field.access_modifier == "private":
                    final_fields.append(f"{field.type} {field.name}")

            constructors.append(ConstructorSignature(
                access_modifier="public",
                parameters=final_fields,
                exceptions=[]
            ))

        if 'AllArgsConstructor' in class_annotations:
            # 所有字段作为构造器参数
            all_fields = []
            for field in self._extract_fields(class_body):
                if not field.is_static:
                    all_fields.append(f"{field.type} {field.name}")

            constructors.append(ConstructorSignature(
                access_modifier="public",
                parameters=all_fields,
                exceptions=[]
            ))

        if 'NoArgsConstructor' in class_annotations:
            constructors.append(ConstructorSignature(
                access_modifier="public",
                parameters=[],
                exceptions=[]
            ))

        return constructors

    def _extract_methods_from_content(self, content: str, class_name: str,
                                    class_start: int, class_end: int) -> List[MethodSignature]:
        """从完整内容中提取方法"""
        methods = []

        # 找到类的开始和结束位置
        class_start_brace = content.find('{', class_start)
        if class_start_brace == -1:
            return methods

        # 找到类的结束位置
        brace_count = 0
        class_end_pos = class_start_brace
        pos = class_start_brace
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    class_end_pos = pos
                    break
            pos += 1

        # 在类的范围内查找方法
        class_content = content[class_start_brace:class_end_pos + 1]

        # 使用改进的方法模式
        method_pattern = re.compile(
            r'(?:^|\n)\s*(?:@[\w.()=",\s]*\s+)*'  # 注解
            r'(public|private|protected|)\s*'     # 访问修饰符
            r'(?:(static|final|abstract|synchronized)\s+)*'  # 其他修饰符
            r'(?:<[^>]+>\s+)?'                    # 泛型
            r'([\w.<>[\]]+)\s+'                   # 返回类型
            r'(\w+)\s*'                           # 方法名
            r'\(([^)]*(?:\([^)]*\)[^)]*)*)\)'     # 参数
            r'(?:\s+throws\s+([\w.,\s]+))?'       # 异常
            r'\s*\{',                             # 方法体开始
            re.MULTILINE | re.DOTALL
        )

        for match in method_pattern.finditer(class_content):
            method_name = match.group(4)

            # 跳过构造器
            if method_name == class_name:
                continue

            access_modifier = match.group(1) or "package"
            modifiers = match.group(2) or ""
            return_type = match.group(3)
            parameters_str = match.group(5) or ""
            exceptions_str = match.group(6) or ""

            # 清理参数字符串
            parameters_str = re.sub(r'\s+', ' ', parameters_str.strip())

            parameters = self._parse_parameters(parameters_str)
            exceptions = self._parse_exceptions(exceptions_str)

            methods.append(MethodSignature(
                name=method_name,
                access_modifier=access_modifier,
                return_type=return_type,
                parameters=parameters,
                exceptions=exceptions,
                is_static="static" in modifiers,
                is_abstract="abstract" in modifiers,
                is_final="final" in modifiers
            ))

        return methods

    def _extract_constructors_from_content(self, content: str, class_name: str,
                                         class_start: int, class_end: int) -> List[ConstructorSignature]:
        """从完整内容中提取构造器"""
        constructors = []

        # 找到类的开始和结束位置
        class_start_brace = content.find('{', class_start)
        if class_start_brace == -1:
            return constructors

        # 找到类的结束位置
        brace_count = 0
        class_end_pos = class_start_brace
        pos = class_start_brace
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    class_end_pos = pos
                    break
            pos += 1

        # 在类的范围内查找构造器
        class_content = content[class_start_brace:class_end_pos + 1]

        # 构造器模式
        constructor_pattern = re.compile(
            r'(?:^|\n)\s*(?:@[\w.()=",\s]*\s+)*'  # 注解
            r'(public|private|protected|)\s*'     # 访问修饰符
            r'(' + re.escape(class_name) + r')\s*'  # 构造器名
            r'\(([^)]*(?:\([^)]*\)[^)]*)*)\)'     # 参数
            r'(?:\s+throws\s+([\w.,\s]+))?'       # 异常
            r'\s*\{',                             # 构造器体开始
            re.MULTILINE | re.DOTALL
        )

        for match in constructor_pattern.finditer(class_content):
            access_modifier = match.group(1) or "package"
            parameters_str = match.group(3) or ""
            exceptions_str = match.group(4) or ""

            # 清理参数字符串
            parameters_str = re.sub(r'\s+', ' ', parameters_str.strip())

            parameters = self._parse_parameters(parameters_str)
            exceptions = self._parse_exceptions(exceptions_str)

            constructors.append(ConstructorSignature(
                access_modifier=access_modifier,
                parameters=parameters,
                exceptions=exceptions
            ))

        # 如果没有找到显式构造器，检查Lombok注解
        if not constructors:
            constructors.extend(self._extract_lombok_constructors(class_content, class_name))

        return constructors
    
    def _extract_methods(self, class_body: str, class_name: str) -> List[MethodSignature]:
        """提取方法"""
        methods = []

        # 改进的方法解析：先清理多行，然后解析
        cleaned_body = self._clean_multiline_signatures(class_body)

        for match in self.method_pattern.finditer(cleaned_body):
            method_name = match.group(4)

            # 跳过构造器
            if method_name == class_name:
                continue

            access_modifier = match.group(1) or "package"
            modifiers = match.group(2) or ""
            return_type = match.group(3)
            parameters_str = match.group(5) or ""
            exceptions_str = match.group(6) or ""

            parameters = self._parse_parameters(parameters_str)
            exceptions = self._parse_exceptions(exceptions_str)

            methods.append(MethodSignature(
                name=method_name,
                access_modifier=access_modifier,
                return_type=return_type,
                parameters=parameters,
                exceptions=exceptions,
                is_static="static" in modifiers,
                is_abstract="abstract" in modifiers,
                is_final="final" in modifiers
            ))

        return methods

    def _clean_multiline_signatures(self, code: str) -> str:
        """清理多行方法签名，将其合并为单行"""
        # 移除注释
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        # 将多行方法签名合并为单行
        # 查找方法签名模式并合并换行
        lines = code.split('\n')
        cleaned_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # 检查是否是方法签名的开始
            if self._looks_like_method_start(line):
                # 收集完整的方法签名
                method_signature = line
                i += 1

                # 继续收集直到找到方法体开始
                while i < len(lines) and not lines[i].strip().endswith('{') and not lines[i].strip().endswith(';'):
                    next_line = lines[i].strip()
                    if next_line:
                        method_signature += " " + next_line
                    i += 1

                # 添加最后一行（包含{或;）
                if i < len(lines):
                    method_signature += " " + lines[i].strip()

                cleaned_lines.append(method_signature)
            else:
                cleaned_lines.append(line)

            i += 1

        return '\n'.join(cleaned_lines)

    def _looks_like_method_start(self, line: str) -> bool:
        """判断一行是否像方法签名的开始"""
        # 简单的启发式判断
        if not line:
            return False

        # 包含访问修饰符或返回类型的行
        modifiers = ['public', 'private', 'protected', 'static', 'final', 'abstract']
        words = line.split()

        if not words:
            return False

        # 检查是否包含访问修饰符
        for word in words:
            if word in modifiers:
                return True

        # 检查是否包含方法名模式（返回类型 + 方法名 + 括号）
        if '(' in line and not line.strip().startswith('//') and not line.strip().startswith('*'):
            return True

        return False
    
    def _extract_fields(self, class_body: str) -> List[FieldSignature]:
        """提取字段"""
        fields = []
        
        for match in self.field_pattern.finditer(class_body):
            access_modifier = match.group(1) or "package"
            modifiers = match.group(2) or ""
            field_type = match.group(3)
            field_name = match.group(4)
            
            fields.append(FieldSignature(
                name=field_name,
                access_modifier=access_modifier,
                type=field_type,
                is_static="static" in modifiers,
                is_final="final" in modifiers
            ))
        
        return fields
    
    def _parse_parameters(self, parameters_str: str) -> List[str]:
        """解析参数列表"""
        if not parameters_str.strip():
            return []
        
        parameters = []
        # 简单的参数解析，处理泛型和数组
        param_parts = parameters_str.split(',')
        
        for param in param_parts:
            param = param.strip()
            if param:
                # 移除final修饰符
                param = re.sub(r'\bfinal\s+', '', param)
                parameters.append(param)
        
        return parameters
    
    def _parse_exceptions(self, exceptions_str: str) -> List[str]:
        """解析异常列表"""
        if not exceptions_str.strip():
            return []
        
        return [exc.strip() for exc in exceptions_str.split(',')]

    def get_project_group_id(self) -> Optional[str]:
        """从pom.xml或build.gradle中获取项目groupId"""
        # 检查pom.xml
        pom_path = self.project_path / "pom.xml"
        if pom_path.exists():
            try:
                with open(pom_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'<groupId>(.*?)</groupId>', content)
                    if match:
                        return match.group(1)
            except Exception as e:
                logger.debug(f"读取pom.xml失败: {e}")

        # 检查build.gradle
        gradle_path = self.project_path / "build.gradle"
        if gradle_path.exists():
            try:
                with open(gradle_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'group\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                    if match:
                        return match.group(1)
            except Exception as e:
                logger.debug(f"读取build.gradle失败: {e}")

        return None
