"""
项目级代码分析器
结合RAG技术，智能分析Java项目并提供上下文检索
"""

import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import json

from config.remote_ollama_config import remote_config
from .type_resolver import ProjectTypeResolver
from .signature_parser import JavaSignatureParser
from .code_analyzer import SmartCodeAnalyzer
from .external_library_mapper import external_library_mapper

logger = logging.getLogger(__name__)

class SmartProjectAnalyzer:
    """智能项目分析器"""
    
    def __init__(self, project_path: Path, vector_store = None, auto_analyze: bool = True):
        """
        初始化项目分析器

        Args:
            project_path: 项目根路径
            vector_store: 向量存储实例，如果为None则创建新的
            auto_analyze: 是否自动分析项目（默认True）
        """
        self.project_path = Path(project_path)

        # 延迟导入以避免循环依赖
        if vector_store is None:
            from .vector_store import CodeVectorStore
            collection_name = f"project_{self._generate_project_id()}"
            self.vector_store = CodeVectorStore(collection_name=collection_name)
        else:
            self.vector_store = vector_store

        # 初始化类型解析器
        self.type_resolver = ProjectTypeResolver(self.project_path)

        #  新增：初始化智能代码分析器
        self.code_analyzer = SmartCodeAnalyzer()

        self.indexed_files = set()
        self.project_stats = {
            'total_files': 0,
            'indexed_files': 0,
            'total_methods': 0,
            'total_classes': 0
        }

        # 自动分析项目（如果向量存储为空）
        if auto_analyze and self.vector_store.collection.count() == 0:
            logger.info("向量存储为空，自动分析项目...")
            self.analyze_project()
    
    def analyze_project(self, force_reindex: bool = False) -> Dict[str, Any]:
        """
        分析整个项目
        
        Args:
            force_reindex: 是否强制重新索引
            
        Returns:
            项目分析结果
        """
        logger.info(f"开始分析项目: {self.project_path}")
        
        # 如果强制重新索引，清空现有数据
        if force_reindex:
            self.vector_store.clear_collection()
            self.indexed_files.clear()
        
        # 查找Java文件
        java_files = self._find_java_files()
        self.project_stats['total_files'] = len(java_files)
        
        logger.info(f"找到 {len(java_files)} 个Java文件")
        
        # 分析每个文件
        for java_file in java_files:
            try:
                if java_file not in self.indexed_files or force_reindex:
                    self._analyze_file(java_file)
                    self.indexed_files.add(java_file)
                    self.project_stats['indexed_files'] += 1
            except Exception as e:
                logger.error(f"分析文件失败 {java_file}: {e}")
        
        # 获取最终统计
        collection_stats = self.vector_store.get_collection_stats()

        # 判断分析是否成功
        success = (
            self.project_stats['indexed_files'] > 0 and
            collection_stats.get('document_count', 0) > 0
        )

        result = {
            'success': success,
            'project_path': str(self.project_path),
            'stats': self.project_stats,
            'collection_stats': collection_stats,
            'indexed_files_count': len(self.indexed_files)
        }

        logger.info(f"项目分析完成: {result}")
        return result
    
    def find_relevant_context(self, target_method: str, query_description: str = None,
                            top_k: int = 5, method_signature: str = None,
                            force_reindex: bool = False) -> List[Dict]:
        """
        为目标方法查找相关上下文，包括智能参数类型检索和导入类定义检索

        Args:
            target_method: 目标方法签名 (package.ClassName#methodName)
            query_description: 额外的查询描述
            top_k: 返回结果数量
            method_signature: 完整的方法签名（用于提取参数类型）
            force_reindex: 是否强制重新索引项目

        Returns:
            相关上下文列表
        """
        # 如果需要强制重新索引
        if force_reindex:
            logger.info("强制重新索引项目...")
            self.analyze_project()

        # 解析方法签名
        method_info = self._parse_method_signature(target_method)

        # 构建查询
        queries = []

        # 基于方法名的查询
        queries.append(method_info['method_name'])

        # 基于类名的查询
        if method_info['class_name']:
            queries.append(f"{method_info['class_name']} {method_info['method_name']}")
            # 添加同一个类中的其他方法查询
            queries.append(method_info['class_name'])

        # 用户提供的描述
        if query_description:
            queries.append(query_description)

        #  新增：智能参数类型检索
        if method_signature:
            param_type_queries = self._build_parameter_type_queries(method_signature)
            queries.extend(param_type_queries)

        #  新增：被测类导入的本地类定义检索
        imported_class_queries = self._build_imported_class_queries(method_info['class_name'])
        queries.extend(imported_class_queries)

        #  新增：类完整定义检索
        class_def_queries = self._build_class_definition_queries(method_info['class_name'])
        queries.extend(class_def_queries)

        #  新增：依赖类检索
        if method_info.get('method_body'):
            dependency_queries = self._build_dependency_queries(method_info['method_body'])
            queries.extend(dependency_queries)

        #  新增：方法参数类型检索
        if method_info.get('parameters'):
            param_queries = self._build_parameter_type_queries_enhanced(method_info['parameters'])
            queries.extend(param_queries)

        # 添加常见的相关方法名模式
        method_name = method_info['method_name']
        if method_name:
            # 查找可能被调用的方法
            queries.append(f"highlight {method_name}")
            queries.append(f"process {method_name}")
            queries.append(f"handle {method_name}")
            # 查找helper方法
            if 'compare' in method_name.lower():
                queries.append("highlight")
                queries.append("chunk")
                queries.append("diff")

        # 添加依赖类查询
        # 从方法签名中提取类名
        if 'ImageChunk' in target_method:
            queries.extend([
                "ImageChunk",
                "getIdentifier",
                "imageHash",
                "rectangle",
                "record ImageChunk",
                "com.example.pdfcompare.model.ImageChunk"
            ])
        if 'PdfContentByte' in target_method:
            queries.append("PdfContentByte")
        if 'BaseColor' in target_method:
            queries.append("BaseColor")
        if 'TextChunk' in target_method:
            queries.extend([
                "TextChunk",
                "record TextChunk",
                "com.example.pdfcompare.model.TextChunk"
            ])

        # 通用的依赖类查询
        queries.extend([
            "record",  # 查找record类
            "model",   # 查找model包中的类
            "com.example.pdfcompare.model"  # 直接查找model包
        ])
        
        # 执行多个查询并合并结果
        all_results = []
        seen_ids = set()

        for query in queries:
            logger.debug(f"执行查询: {query}")

            results = self.vector_store.search_similar_code(
                query=query,
                top_k=top_k,
                filter_metadata={'language': 'java'}  # 只搜索Java代码
            )

            # 去重并添加到结果
            for result in results:
                result_id = result.get('id')
                if result_id and result_id not in seen_ids:
                    result['query'] = query  # 记录匹配的查询
                    all_results.append(result)
                    seen_ids.add(result_id)

        #  新增：确保导入的本地类定义被包含
        all_results = self._ensure_imported_class_definitions(all_results, method_info['class_name'])

        #  新增：确保record类定义被包含
        all_results = self._ensure_record_definitions(all_results)

        #  新增：确保依赖类定义被包含
        all_results = self._ensure_dependency_definitions(all_results, method_info)

        #  新增：使用智能代码分析器增强上下文
        all_results = self._enhance_with_smart_analysis(all_results, method_info)

        #  新增：添加外部库类信息
        all_results = self._add_external_library_context(all_results, method_info)

        # 按相似度排序并返回top_k
        all_results.sort(key=lambda x: x.get('distance', 1.0))

        logger.info(f"为 {target_method} 找到 {len(all_results[:top_k])} 个相关上下文")
        return all_results[:top_k]
    
    def find_similar_methods(self, method_code: str, top_k: int = 3) -> List[Dict]:
        """
        查找与给定方法相似的方法
        
        Args:
            method_code: 方法代码
            top_k: 返回结果数量
            
        Returns:
            相似方法列表
        """
        # 从方法代码中提取关键信息
        query = self._extract_method_keywords(method_code)
        
        results = self.vector_store.search_similar_code(
            query=query,
            top_k=top_k,
            filter_metadata={'type': 'method', 'language': 'java'}
        )
        
        logger.info(f"找到 {len(results)} 个相似方法")
        return results
    
    def get_class_context(self, class_name: str) -> List[Dict]:
        """
        获取指定类的所有上下文
        
        Args:
            class_name: 类名
            
        Returns:
            类的所有方法和相关信息
        """
        results = self.vector_store.search_similar_code(
            query=class_name,
            top_k=50,  # 获取更多结果
            filter_metadata={'class_name': class_name, 'language': 'java'}
        )
        
        logger.info(f"获取类 {class_name} 的 {len(results)} 个上下文项")
        return results
    
    def _find_java_files(self) -> List[Path]:
        """查找项目中的所有Java文件"""
        java_files = []
        
        # 递归查找.java文件
        for java_file in self.project_path.rglob("*.java"):
            # 跳过测试文件和构建目录
            if self._should_include_file(java_file):
                java_files.append(java_file)
        
        return java_files
    
    def _should_include_file(self, file_path: Path) -> bool:
        """判断是否应该包含该文件"""
        # 排除的目录
        exclude_dirs = {'test', 'tests', 'target', 'build', '.git', 'node_modules'}
        
        # 检查路径中是否包含排除的目录
        for part in file_path.parts:
            if part.lower() in exclude_dirs:
                return False
        
        # 排除测试文件
        filename = file_path.name.lower()
        if 'test' in filename and filename.endswith('.java'):
            return False
        
        return True
    
    def _analyze_file(self, file_path: Path):
        """分析单个Java文件"""
        try:
            # 使用现有的Java解析器
            from source_analysis.java_parser import JavaParser
            
            parser = JavaParser()
            parsed_class = parser.parse_file(file_path)
            
            if not parsed_class:
                logger.warning(f"无法解析文件: {file_path}")
                return
            
            self.project_stats['total_classes'] += 1
            
            # 索引类级别的信息
            class_metadata = {
                'type': 'class',
                'class_name': parsed_class.name,
                'package': parsed_class.package,
                'file_path': str(file_path.relative_to(self.project_path)),
                'language': 'java'
            }
            
            # 添加类的完整信息
            try:
                # 读取完整的类定义
                class_content = file_path.read_text(encoding='utf-8')

                # 对于简短的类（如record），包含完整定义
                if len(class_content) <= 500 or 'record' in class_content:
                    class_info = f"Class: {parsed_class.name}\nPackage: {parsed_class.package}\n\nFull Definition:\n{class_content}"
                else:
                    # 对于长类，只包含摘要
                    class_info = f"class {parsed_class.name} in package {parsed_class.package}"
                    if parsed_class.imports:
                        class_info += f" with imports: {', '.join(parsed_class.imports[:5])}"

                self.vector_store.add_code_snippet(class_info, class_metadata)

            except Exception as e:
                # 回退到简单摘要
                class_summary = f"class {parsed_class.name} in package {parsed_class.package}"
                if parsed_class.imports:
                    class_summary += f" with imports: {', '.join(parsed_class.imports[:5])}"
                self.vector_store.add_code_snippet(class_summary, class_metadata)
            
            # 索引每个方法
            for method in parsed_class.methods:
                self._index_method(method, parsed_class, file_path)
                self.project_stats['total_methods'] += 1
            
            logger.debug(f"已索引文件: {file_path}")
            
        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")
    
    def _index_method(self, method, parsed_class, file_path: Path):
        """索引单个方法"""
        try:
            # 构建方法元数据
            metadata = {
                'type': 'method',
                'method_name': method.name,
                'class_name': parsed_class.name,
                'package': parsed_class.package,
                'file_path': str(file_path.relative_to(self.project_path)),
                'start_line': method.start_line,
                'end_line': method.end_line,
                'access_modifier': method.access_modifier,
                'language': 'java'
            }
            
            # 使用方法签名和方法体作为文档内容
            method_content = f"Method: {method.signature}\n\nImplementation:\n{method.body}"
            
            # 添加到向量存储
            self.vector_store.add_code_snippet(method_content, metadata)
            
        except Exception as e:
            logger.error(f"索引方法失败 {method.name}: {e}")
    
    def _parse_method_signature(self, signature: str) -> Dict[str, str]:
        """解析方法签名"""
        if '#' in signature:
            # Java风格: package.ClassName#methodName
            class_part, method_name = signature.split('#', 1)
            package_parts = class_part.split('.')
            class_name = package_parts[-1] if package_parts else None
            package = '.'.join(package_parts[:-1]) if len(package_parts) > 1 else ''
        else:
            # 简单方法名
            method_name = signature
            class_name = None
            package = ''
        
        return {
            'method_name': method_name,
            'class_name': class_name,
            'package': package
        }
    
    def _extract_method_keywords(self, method_code: str) -> str:
        """从方法代码中提取关键词"""
        # 简单的关键词提取
        keywords = []
        
        # 提取方法名
        import re
        method_match = re.search(r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(', method_code)
        if method_match:
            keywords.append(method_match.group(1))
        
        # 提取常见的编程概念
        concepts = ['add', 'get', 'set', 'create', 'delete', 'update', 'validate', 'check', 'calculate', 'find', 'search', 'sort', 'filter']
        for concept in concepts:
            if concept.lower() in method_code.lower():
                keywords.append(concept)
        
        return ' '.join(keywords) if keywords else method_code[:100]

    def _build_parameter_type_queries(self, method_signature: str) -> List[str]:
        """
        基于方法签名构建参数类型查询

        Args:
            method_signature: 完整的方法签名

        Returns:
            参数类型查询列表
        """
        queries = []

        try:
            # 提取所有类型（参数类型和返回类型）
            all_types = JavaSignatureParser.extract_all_types_from_signature(method_signature)

            logger.debug(f"从方法签名中提取的类型: {all_types}")

            for type_name in all_types:
                # 为每个类型构建多种查询
                type_queries = self._build_queries_for_type(type_name)
                queries.extend(type_queries)

            # 去重
            unique_queries = list(dict.fromkeys(queries))
            logger.debug(f"构建的参数类型查询: {unique_queries}")

            return unique_queries

        except Exception as e:
            logger.debug(f"构建参数类型查询失败: {e}")
            return []

    def _build_queries_for_type(self, type_name: str) -> List[str]:
        """
        为单个类型构建查询

        Args:
            type_name: 类型名称

        Returns:
            查询列表
        """
        queries = []

        # 基础查询
        queries.append(type_name)

        #  增强：类声明查询
        queries.extend([
            f"class {type_name}",
            f"public class {type_name}",
            f"record {type_name}",
            f"public record {type_name}",
            f"interface {type_name}",
            f"enum {type_name}"
        ])

        #  新增：构造函数查询
        queries.extend([
            f"constructor {type_name}",
            f"public {type_name}(",
            f"{type_name}(",
            f"new {type_name}(",
        ])

        #  新增：注解查询
        queries.extend([
            f"@RequiredArgsConstructor",
            f"@Component",
            f"@Service",
            f"@Repository",
            f"@Controller",
        ])

        # 尝试从类型解析器中获取完整包名
        class_info = self.type_resolver.resolve_type(type_name)
        if class_info:
            queries.append(class_info.full_qualified_name)
            queries.append(f"package {class_info.package}")

            # 如果是record类，添加特殊查询
            if class_info.is_record:
                queries.extend([
                    f"record {type_name}",
                    f"{type_name} record",
                    "getIdentifier",  # record类常见方法
                ])

        #  新增：强制包路径查询（即使类型解析器没有找到）
        queries.extend([
            f"import.*{type_name}",
            f"package.*{type_name}",
            f"{type_name}.java",
            f"class.*{type_name}.*\\{{",  # 匹配类定义
            f"public.*{type_name}.*\\{{",
        ])

        #  新增：外部库检查
        if self.external_library_mapper:
            import_stmt = self.external_library_mapper.get_import_statement(type_name)
            if import_stmt:
                queries.append(import_stmt)
                queries.append(f"import {import_stmt.split()[-1]}")

        return queries

    def _build_class_definition_queries(self, class_name: str) -> List[str]:
        """
        构建类完整定义查询

        Args:
            class_name: 类名

        Returns:
            类定义查询列表
        """
        queries = []

        #  完整类定义查询
        queries.extend([
            f"record {class_name}",
            f"class {class_name}",
            f"public class {class_name}",
            f"@Component class {class_name}",
            f"@Service class {class_name}",
            f"@Repository class {class_name}",
            f"@Controller class {class_name}",
        ])

        #  构造函数相关查询
        queries.extend([
            f"@RequiredArgsConstructor",
            f"@AllArgsConstructor",
            f"@NoArgsConstructor",
            f"constructor {class_name}",
            f"public {class_name}(",
            f"{class_name}(",
        ])

        #  依赖注入相关查询
        queries.extend([
            f"@Autowired",
            f"@Inject",
            f"private final",
            f"private {class_name}",
        ])

        return queries

    def _build_dependency_queries(self, method_implementation: str) -> List[str]:
        """
        从方法实现中提取依赖类查询

        Args:
            method_implementation: 方法实现代码

        Returns:
            依赖查询列表
        """
        queries = []

        if not method_implementation:
            return queries

        try:
            import re

            #  提取方法调用模式：object.method()
            method_calls = re.findall(r'(\w+)\.(\w+)\s*\(', method_implementation)
            for obj, method in method_calls:
                if obj not in ['this', 'super', 'System', 'Math']:  # 排除常见的非依赖调用
                    queries.extend([
                        f"class {obj}",
                        f"public class {obj}",
                        f"@Component class {obj}",
                        f"public {method}",
                        f"{obj}.{method}",
                        f"void {method}",
                        f"String {method}",
                        f"int {method}",
                        f"boolean {method}",
                    ])

            #  提取类型引用
            type_references = re.findall(r'\b([A-Z][a-zA-Z0-9]*)\b', method_implementation)
            for type_ref in set(type_references):
                if len(type_ref) > 2:  # 过滤掉太短的匹配
                    queries.extend([
                        f"class {type_ref}",
                        f"record {type_ref}",
                        f"interface {type_ref}",
                        f"enum {type_ref}",
                    ])

        except Exception as e:
            logger.debug(f"提取依赖查询失败: {e}")

        return queries

    def _build_imported_class_queries(self, class_name: str) -> List[str]:
        """
        构建被测类导入的本地类查询

        Args:
            class_name: 被测类名

        Returns:
            导入类查询列表
        """
        queries = []

        if not class_name:
            return queries

        try:
            # 查找被测类的文件
            class_info = self.type_resolver.resolve_type(class_name)
            if not class_info:
                logger.debug(f"未找到类信息: {class_name}")
                return queries

            # 读取被测类文件内容
            import os
            class_file_path = os.path.join(self.project_path, class_info.file_path)
            if not os.path.exists(class_file_path):
                logger.debug(f"类文件不存在: {class_file_path}")
                return queries

            with open(class_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取import语句中的本地类
            import re
            import_pattern = r'import\s+com\.example\.pdfcompare\.(\w+)\.(\w+);'
            imports = re.findall(import_pattern, content)

            for package_part, imported_class in imports:
                # 为每个导入的本地类构建查询
                queries.extend([
                    imported_class,
                    f"class {imported_class}",
                    f"public class {imported_class}",
                    f"record {imported_class}",
                    f"public record {imported_class}",
                    f"com.example.pdfcompare.{package_part}.{imported_class}"
                ])

                logger.debug(f"添加导入类查询: {imported_class} from {package_part}")

        except Exception as e:
            logger.debug(f"构建导入类查询失败: {e}")

        return queries

    def _ensure_imported_class_definitions(self, results: List[Dict], class_name: str) -> List[Dict]:
        """
        确保导入的本地类定义被包含在结果中

        Args:
            results: 当前搜索结果
            class_name: 被测类名

        Returns:
            增强后的结果列表
        """
        if not class_name:
            return results

        try:
            # 查找被测类的导入信息
            class_info = self.type_resolver.resolve_type(class_name)
            if not class_info:
                return results

            # 读取被测类文件内容
            import os
            class_file_path = os.path.join(self.project_path, class_info.file_path)
            if not os.path.exists(class_file_path):
                return results

            with open(class_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取import语句中的本地类
            import re
            import_pattern = r'import\s+com\.example\.pdfcompare\.(\w+)\.(\w+);'
            imports = re.findall(import_pattern, content)

            # 检查每个导入的类是否在结果中有完整定义
            for package_part, imported_class in imports:
                has_definition = False

                # 检查是否已有该类的完整定义
                for result in results:
                    result_content = result.get('content', '')
                    if (f"class {imported_class}" in result_content or
                        f"record {imported_class}" in result_content) and \
                       len(result_content) > 100:  # 确保是完整定义，不只是导入语句
                        has_definition = True
                        break

                # 如果没有完整定义，尝试直接搜索
                if not has_definition:
                    logger.debug(f"缺少 {imported_class} 的完整定义，尝试直接搜索...")

                    definition_results = self.vector_store.search_similar_code(
                        query=f"class {imported_class}",
                        top_k=3,
                        filter_metadata={'language': 'java'}
                    )

                    # 添加找到的定义
                    for def_result in definition_results:
                        def_content = def_result.get('content', '')
                        if (f"class {imported_class}" in def_content or
                            f"record {imported_class}" in def_content) and \
                           len(def_content) > 100:
                            def_result['query'] = f"imported_class_definition_{imported_class}"
                            def_result['distance'] = 0.5  # 给予较高优先级
                            results.append(def_result)
                            logger.debug(f"添加了 {imported_class} 的完整定义")
                            break

        except Exception as e:
            logger.debug(f"确保导入类定义失败: {e}")

        return results

    def _ensure_record_definitions(self, results: List[Dict]) -> List[Dict]:
        """
        确保record类的完整定义被包含

        Args:
            results: 当前搜索结果

        Returns:
            增强后的结果列表
        """
        enhanced_results = results.copy()

        try:
            # 查找结果中提到的record类
            record_classes = set()
            for result in results:
                content = result.get('content', '')
                metadata = result.get('metadata', {})

                # 从内容中提取record类名
                import re
                record_matches = re.findall(r'record\s+(\w+)', content)
                record_classes.update(record_matches)

                # 从metadata中提取
                if metadata.get('type') == 'class' and 'record' in content:
                    class_name = metadata.get('class_name')
                    if class_name:
                        record_classes.add(class_name)

            # 为每个record类检索完整定义
            for record_class in record_classes:
                record_queries = [
                    f"record {record_class}",
                    f"public record {record_class}",
                    f"{record_class} record",
                ]

                for query in record_queries:
                    additional_results = self.vector_store.search_similar_code(
                        query=query,
                        top_k=2,
                        filter_metadata={'language': 'java'}
                    )

                    for result in additional_results:
                        result_id = result.get('id')
                        if result_id and not any(r.get('id') == result_id for r in enhanced_results):
                            result['query'] = f"record_definition:{query}"
                            enhanced_results.append(result)
                            logger.debug(f"添加record类定义: {record_class}")

        except Exception as e:
            logger.debug(f"确保record定义失败: {e}")

        return enhanced_results

    def _ensure_dependency_definitions(self, results: List[Dict], method_info: Dict) -> List[Dict]:
        """
        确保依赖类定义被包含

        Args:
            results: 当前搜索结果
            method_info: 方法信息

        Returns:
            增强后的结果列表
        """
        enhanced_results = results.copy()

        try:
            # 从方法实现中提取依赖
            method_body = method_info.get('method_body', '')
            if not method_body:
                return enhanced_results

            import re

            # 提取可能的依赖类名
            dependency_classes = set()

            # 提取方法调用中的对象名
            method_calls = re.findall(r'(\w+)\.(\w+)\s*\(', method_body)
            for obj, method in method_calls:
                if obj not in ['this', 'super', 'System', 'Math'] and obj[0].islower():
                    # 可能是依赖对象，尝试推断类名
                    potential_class = obj.capitalize() + 'er' if not obj.endswith('er') else obj.capitalize()
                    dependency_classes.add(potential_class)

                    # 常见模式：pdfHighlighter -> PDFHighlighter
                    if 'pdf' in obj.lower():
                        dependency_classes.add('PDFHighlighter')
                    if 'highlighter' in obj.lower():
                        dependency_classes.add('PDFHighlighter')

            # 为每个依赖类检索定义
            for dep_class in dependency_classes:
                dep_queries = [
                    f"class {dep_class}",
                    f"public class {dep_class}",
                    f"@Component class {dep_class}",
                    f"@Service class {dep_class}",
                ]

                for query in dep_queries:
                    additional_results = self.vector_store.search_similar_code(
                        query=query,
                        top_k=2,
                        filter_metadata={'language': 'java'}
                    )

                    for result in additional_results:
                        result_id = result.get('id')
                        if result_id and not any(r.get('id') == result_id for r in enhanced_results):
                            result['query'] = f"dependency_definition:{query}"
                            enhanced_results.append(result)
                            logger.debug(f"添加依赖类定义: {dep_class}")

        except Exception as e:
            logger.debug(f"确保依赖定义失败: {e}")

        return enhanced_results

    def _enhance_with_smart_analysis(self, results: List[Dict], method_info: Dict) -> List[Dict]:
        """
        使用智能代码分析器增强上下文

        Args:
            results: 当前搜索结果
            method_info: 方法信息

        Returns:
            增强后的结果列表
        """
        enhanced_results = results.copy()

        try:
            # 分析被测类
            class_name = method_info.get('class_name')
            if not class_name:
                return enhanced_results

            # 查找被测类文件
            class_info = self.type_resolver.resolve_type(class_name)
            if not class_info:
                return enhanced_results

            import os
            class_file_path = os.path.join(self.project_path, class_info.file_path)
            if not os.path.exists(class_file_path):
                return enhanced_results

            # 使用智能代码分析器分析类
            analyzed_class = self.code_analyzer.analyze_class(class_file_path)
            if not analyzed_class:
                return enhanced_results

            logger.debug(f"智能分析类 {class_name}: record={analyzed_class.is_record}, component={analyzed_class.is_component}")

            # 为分析结果添加特殊的上下文信息
            analysis_context = {
                'id': f"smart_analysis_{class_name}",
                'content': self._format_smart_analysis(analyzed_class),
                'metadata': {
                    'type': 'smart_analysis',
                    'class_name': class_name,
                    'package': analyzed_class.package,
                    'language': 'java',
                    'is_record': analyzed_class.is_record,
                    'is_component': analyzed_class.is_component,
                },
                'distance': 0.1,  # 给予最高优先级
                'query': 'smart_analysis'
            }

            # 将智能分析结果插入到结果列表的开头
            enhanced_results.insert(0, analysis_context)

            # 分析依赖类
            for dependency in analyzed_class.dependencies:
                dep_class_info = self.type_resolver.resolve_type(dependency)
                if dep_class_info:
                    dep_file_path = os.path.join(self.project_path, dep_class_info.file_path)
                    if os.path.exists(dep_file_path):
                        analyzed_dep = self.code_analyzer.analyze_class(dep_file_path)
                        if analyzed_dep:
                            dep_context = {
                                'id': f"smart_analysis_dep_{dependency}",
                                'content': self._format_smart_analysis(analyzed_dep),
                                'metadata': {
                                    'type': 'smart_analysis_dependency',
                                    'class_name': dependency,
                                    'package': analyzed_dep.package,
                                    'language': 'java',
                                    'is_record': analyzed_dep.is_record,
                                    'is_component': analyzed_dep.is_component,
                                },
                                'distance': 0.2,
                                'query': f'smart_analysis_dependency_{dependency}'
                            }
                            enhanced_results.append(dep_context)
                            logger.debug(f"添加依赖类智能分析: {dependency}")

        except Exception as e:
            logger.debug(f"智能分析增强失败: {e}")

        return enhanced_results

    def _format_smart_analysis(self, class_info) -> str:
        """
        格式化智能分析结果

        Args:
            class_info: 分析得到的类信息

        Returns:
            格式化的分析结果
        """
        lines = []

        # 基本信息
        class_type = "record" if class_info.is_record else "class"
        lines.append(f" SMART ANALYSIS: {class_type} {class_info.name}")
        lines.append(f" Package: {class_info.package}")

        # 注解信息
        if class_info.annotations:
            lines.append(f" Annotations: {', '.join(class_info.annotations)}")

        # 构造函数信息
        if class_info.constructors:
            for i, constructor in enumerate(class_info.constructors):
                if constructor.parameters:
                    param_str = ', '.join([f"{ptype} {pname}" for ptype, pname in constructor.parameters])
                    lines.append(f" Constructor {i+1}: {class_info.name}({param_str})")
                else:
                    lines.append(f" Constructor {i+1}: {class_info.name}() - default constructor")

                if constructor.annotations:
                    lines.append(f"   Annotations: {', '.join(constructor.annotations)}")

        # 依赖信息
        if class_info.dependencies:
            lines.append(f"🔗 Dependencies: {', '.join(class_info.dependencies)}")

        # 特殊提示
        if class_info.is_record:
            lines.append("  RECORD CLASS: Use exact constructor parameters!")

        if class_info.is_component:
            lines.append("  SPRING COMPONENT: Use @Mock for dependencies and @InjectMocks for this class!")

        if any('@RequiredArgsConstructor' in ann for ann in class_info.annotations):
            lines.append("  LOMBOK @RequiredArgsConstructor: Cannot use no-arg constructor!")

        return '\n'.join(lines)

    def _build_parameter_type_queries_enhanced(self, parameters: List[str]) -> List[str]:
        """
        增强的参数类型查询构建

        Args:
            parameters: 参数列表

        Returns:
            参数类型查询列表
        """
        queries = []

        try:
            for param in parameters:
                if not param or not param.strip():
                    continue

                # 提取参数类型
                param_parts = param.strip().split()
                if len(param_parts) >= 2:
                    param_type = param_parts[0]

                    # 处理泛型类型 List<ImageChunk> -> ImageChunk
                    if '<' in param_type and '>' in param_type:
                        generic_type = param_type[param_type.find('<')+1:param_type.find('>')]
                        queries.extend(self._build_queries_for_type(generic_type))
                        # 同时查询泛型容器类型本身
                        base_type = param_type[:param_type.find('<')]
                        if base_type not in ['List', 'Set', 'Map', 'Collection']:
                            queries.extend(self._build_queries_for_type(base_type))

                    # 处理基本类型
                    if param_type not in ['int', 'float', 'double', 'boolean', 'String', 'List']:
                        queries.extend(self._build_queries_for_type(param_type))

                    #  新增：强制查询所有参数类型的包路径
                    if param_type and param_type not in ['int', 'float', 'double', 'boolean', 'void']:
                        queries.extend([
                            f"package {param_type}",
                            f"import.*{param_type}",
                            f"{param_type}.java",
                        ])

        except Exception as e:
            logger.debug(f"构建参数类型查询失败: {e}")

        return queries

    def _add_external_library_context(self, results: List[Dict], method_info: Dict) -> List[Dict]:
        """
        添加外部库类上下文信息

        Args:
            results: 当前搜索结果
            method_info: 方法信息

        Returns:
            增强后的结果列表
        """
        enhanced_results = results.copy()

        try:
            # 从方法签名和实现中提取可能的外部库类
            external_classes = set()

            # 从方法签名中提取
            signature = method_info.get('signature', '')
            method_body = method_info.get('method_body', '')

            # 常见的外部库类模式
            import re
            class_patterns = [
                r'\b(PdfContentByte)\b',
                r'\b(BaseColor)\b',
                r'\b(Rectangle)\b',
                r'\b(Color)\b',
                r'\b(List)<(\w+)>',
                r'\b(Patch)<(\w+)>',
                r'\b(Delta)\b',
                r'\b(DiffUtils)\b',
            ]

            for pattern in class_patterns:
                matches = re.findall(pattern, signature + ' ' + method_body)
                for match in matches:
                    if isinstance(match, tuple):
                        external_classes.update(match)
                    else:
                        external_classes.add(match)

            # 为每个外部库类添加上下文
            for class_name in external_classes:
                if external_library_mapper.is_external_library_class(class_name):
                    import_stmt = external_library_mapper.get_import_statement(class_name)
                    constructor_hint = external_library_mapper.get_constructor_hints(class_name)

                    context_content = f" EXTERNAL LIBRARY: {class_name}\n"
                    context_content += f" Import: {import_stmt}\n"
                    if constructor_hint:
                        context_content += f" Constructor: {constructor_hint}\n"
                    context_content += f"  This is an external library class - use exact import path!"

                    external_context = {
                        'id': f"external_lib_{class_name}",
                        'content': context_content,
                        'metadata': {
                            'type': 'external_library',
                            'class_name': class_name,
                            'package': external_library_mapper.get_package_path(class_name),
                            'language': 'java',
                            'is_external': True,
                        },
                        'distance': 0.15,  # 高优先级
                        'query': f'external_library_{class_name}'
                    }

                    enhanced_results.append(external_context)
                    logger.debug(f"添加外部库类上下文: {class_name}")

        except Exception as e:
            logger.debug(f"添加外部库上下文失败: {e}")

        return enhanced_results

    def _generate_project_id(self) -> str:
        """生成项目唯一ID"""
        # 使用项目绝对路径的哈希值
        project_str = str(self.project_path.absolute())
        return hashlib.md5(project_str.encode()).hexdigest()[:8]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        collection_stats = self.vector_store.get_collection_stats()
        
        return {
            'project_path': str(self.project_path),
            'project_stats': self.project_stats,
            'vector_store_stats': collection_stats,
            'indexed_files': len(self.indexed_files)
        }
