"""
项目类型解析器
用于解析项目中所有类的完整包路径，解决导入语句错误问题
"""

import logging
import re
from pathlib import Path
from typing import Dict, Optional, Set, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClassInfo:
    """类信息"""
    name: str
    package: str
    full_qualified_name: str
    file_path: str
    is_record: bool = False
    is_interface: bool = False
    is_enum: bool = False
    imports: List[str] = None

class ProjectTypeResolver:
    """项目类型解析器"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.type_mapping: Dict[str, ClassInfo] = {}  # {simple_class_name: ClassInfo}
        self.package_mapping: Dict[str, Set[str]] = {}  # {package: {class_names}}
        self.ambiguous_types: Dict[str, List[ClassInfo]] = {}  # 同名类的处理
        self._build_type_mapping()
    
    def _build_type_mapping(self):
        """构建项目中所有类的映射表"""
        logger.info(f"开始构建项目类型映射: {self.project_path}")
        
        java_files = list(self.project_path.rglob("*.java"))
        logger.info(f"找到 {len(java_files)} 个Java文件")
        
        for java_file in java_files:
            try:
                # 跳过测试文件
                if self._is_test_file(java_file):
                    continue
                    
                class_info = self._parse_class_info(java_file)
                if class_info:
                    self._add_class_to_mapping(class_info)
                    
            except Exception as e:
                logger.debug(f"解析类失败 {java_file}: {e}")
        
        logger.info(f"类型映射构建完成: {len(self.type_mapping)} 个类")
        self._log_mapping_summary()
    
    def _is_test_file(self, file_path: Path) -> bool:
        """判断是否为测试文件"""
        path_str = str(file_path).lower()
        return (
            'test' in path_str or
            file_path.name.lower().endswith('test.java') or
            file_path.name.lower().endswith('tests.java')
        )
    
    def _parse_class_info(self, java_file: Path) -> Optional[ClassInfo]:
        """解析Java文件中的类信息"""
        try:
            content = java_file.read_text(encoding='utf-8')
            
            # 提取包名
            package = self._extract_package(content)
            
            # 提取类名和类型
            class_name, class_type = self._extract_class_name_and_type(content)
            if not class_name:
                return None
            
            # 提取导入语句
            imports = self._extract_imports(content)
            
            # 构建完整类名
            full_qualified_name = f"{package}.{class_name}" if package else class_name
            
            return ClassInfo(
                name=class_name,
                package=package,
                full_qualified_name=full_qualified_name,
                file_path=str(java_file.relative_to(self.project_path)),
                is_record=class_type == 'record',
                is_interface=class_type == 'interface',
                is_enum=class_type == 'enum',
                imports=imports or []
            )
            
        except Exception as e:
            logger.debug(f"解析文件失败 {java_file}: {e}")
            return None
    
    def _extract_package(self, content: str) -> str:
        """提取包名"""
        package_match = re.search(r'package\s+([\w.]+)\s*;', content)
        return package_match.group(1) if package_match else ""
    
    def _extract_class_name_and_type(self, content: str) -> tuple[Optional[str], str]:
        """提取类名和类型（class/record/interface/enum）"""
        # 匹配各种类型的声明
        patterns = [
            (r'public\s+record\s+(\w+)', 'record'),
            (r'record\s+(\w+)', 'record'),
            (r'public\s+interface\s+(\w+)', 'interface'),
            (r'interface\s+(\w+)', 'interface'),
            (r'public\s+enum\s+(\w+)', 'enum'),
            (r'enum\s+(\w+)', 'enum'),
            (r'public\s+class\s+(\w+)', 'class'),
            (r'class\s+(\w+)', 'class'),
        ]
        
        for pattern, class_type in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1), class_type
        
        return None, 'class'
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取导入语句"""
        imports = []
        import_pattern = r'import\s+([\w.]+)\s*;'
        
        for match in re.finditer(import_pattern, content):
            import_stmt = match.group(1)
            if not import_stmt.startswith('java.lang'):  # 跳过java.lang包
                imports.append(import_stmt)
        
        return imports
    
    def _add_class_to_mapping(self, class_info: ClassInfo):
        """将类信息添加到映射表"""
        class_name = class_info.name
        
        # 检查是否有同名类
        if class_name in self.type_mapping:
            # 处理同名类
            existing_class = self.type_mapping[class_name]
            if class_name not in self.ambiguous_types:
                self.ambiguous_types[class_name] = [existing_class]
            self.ambiguous_types[class_name].append(class_info)
            logger.warning(f"发现同名类: {class_name} 在 {existing_class.package} 和 {class_info.package}")
        else:
            self.type_mapping[class_name] = class_info
        
        # 添加到包映射
        package = class_info.package
        if package not in self.package_mapping:
            self.package_mapping[package] = set()
        self.package_mapping[package].add(class_name)
    
    def resolve_type(self, simple_class_name: str, context_package: str = None) -> Optional[ClassInfo]:
        """
        解析简单类名到完整类信息
        
        Args:
            simple_class_name: 简单类名
            context_package: 上下文包名，用于解决同名类冲突
            
        Returns:
            ClassInfo对象，如果找不到则返回None
        """
        if simple_class_name not in self.type_mapping:
            return None
        
        # 如果没有同名冲突，直接返回
        if simple_class_name not in self.ambiguous_types:
            return self.type_mapping[simple_class_name]
        
        # 处理同名类冲突
        candidates = self.ambiguous_types[simple_class_name]
        
        # 如果提供了上下文包名，优先选择同包或相近包的类
        if context_package:
            # 1. 优先选择同包的类
            for candidate in candidates:
                if candidate.package == context_package:
                    return candidate
            
            # 2. 选择包名最相似的类
            best_candidate = None
            max_similarity = 0
            
            for candidate in candidates:
                similarity = self._calculate_package_similarity(context_package, candidate.package)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_candidate = candidate
            
            if best_candidate:
                return best_candidate
        
        # 如果无法确定，返回第一个（通常是最先找到的）
        logger.warning(f"无法确定类 {simple_class_name} 的具体包，使用: {candidates[0].full_qualified_name}")
        return candidates[0]
    
    def _calculate_package_similarity(self, package1: str, package2: str) -> int:
        """计算两个包名的相似度"""
        if not package1 or not package2:
            return 0
        
        parts1 = package1.split('.')
        parts2 = package2.split('.')
        
        # 计算共同前缀长度
        common_prefix = 0
        for i in range(min(len(parts1), len(parts2))):
            if parts1[i] == parts2[i]:
                common_prefix += 1
            else:
                break
        
        return common_prefix
    
    def get_import_statement(self, simple_class_name: str, context_package: str = None) -> str:
        """
        获取导入语句
        
        Args:
            simple_class_name: 简单类名
            context_package: 上下文包名
            
        Returns:
            导入语句，如果不需要导入则返回空字符串
        """
        class_info = self.resolve_type(simple_class_name, context_package)
        if not class_info:
            return ""
        
        # 如果在同一个包中，不需要导入
        if context_package and class_info.package == context_package:
            return ""
        
        # 如果在java.lang包中，不需要导入
        if class_info.package == "java.lang":
            return ""
        
        # 如果没有包名（默认包），不需要导入
        if not class_info.package:
            return ""
        
        return f"import {class_info.full_qualified_name};"
    
    def get_all_imports_for_types(self, type_names: List[str], context_package: str = None) -> List[str]:
        """
        为多个类型获取所有需要的导入语句
        
        Args:
            type_names: 类型名称列表
            context_package: 上下文包名
            
        Returns:
            导入语句列表
        """
        imports = []
        seen_imports = set()
        
        for type_name in type_names:
            # 处理泛型类型，如 List<String>
            base_type = self._extract_base_type(type_name)
            import_stmt = self.get_import_statement(base_type, context_package)
            
            if import_stmt and import_stmt not in seen_imports:
                imports.append(import_stmt)
                seen_imports.add(import_stmt)
        
        return sorted(imports)
    
    def _extract_base_type(self, type_name: str) -> str:
        """从复杂类型中提取基础类型名"""
        # 移除泛型参数
        if '<' in type_name:
            type_name = type_name[:type_name.index('<')]
        
        # 移除数组标记
        if '[' in type_name:
            type_name = type_name[:type_name.index('[')]
        
        # 移除包名前缀
        if '.' in type_name:
            type_name = type_name.split('.')[-1]
        
        return type_name.strip()
    
    def find_types_in_package(self, package_name: str) -> List[ClassInfo]:
        """查找指定包中的所有类型"""
        if package_name not in self.package_mapping:
            return []
        
        result = []
        for class_name in self.package_mapping[package_name]:
            class_info = self.type_mapping.get(class_name)
            if class_info and class_info.package == package_name:
                result.append(class_info)
        
        return result

    def _log_mapping_summary(self):
        """记录映射摘要信息"""
        if logger.isEnabledFor(logging.INFO):
            logger.info("=== 类型映射摘要 ===")
            logger.info(f"总类数: {len(self.type_mapping)}")
            logger.info(f"包数: {len(self.package_mapping)}")

            if self.ambiguous_types:
                logger.info(f"同名类冲突: {len(self.ambiguous_types)}")
                for class_name, candidates in self.ambiguous_types.items():
                    packages = [c.package for c in candidates]
                    logger.info(f"  {class_name}: {packages}")

            # 显示主要包的类数量
            package_stats = [(pkg, len(classes)) for pkg, classes in self.package_mapping.items()]
            package_stats.sort(key=lambda x: x[1], reverse=True)

            logger.info("主要包:")
            for pkg, count in package_stats[:5]:
                logger.info(f"  {pkg}: {count} 个类")

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_classes': len(self.type_mapping),
            'total_packages': len(self.package_mapping),
            'ambiguous_types': len(self.ambiguous_types),
            'records': sum(1 for c in self.type_mapping.values() if c.is_record),
            'interfaces': sum(1 for c in self.type_mapping.values() if c.is_interface),
            'enums': sum(1 for c in self.type_mapping.values() if c.is_enum),
        }
