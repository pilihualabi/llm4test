#!/usr/bin/env python3
"""
本地包路径验证器
验证和修复生成的测试代码中的包路径问题
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

from .project_index import ProjectIndexDatabase

logger = logging.getLogger(__name__)

class PackageValidator:
    """本地包路径验证器"""
    
    def __init__(self, project_path: str, db_path: str = "./project_index.db", 
                 project_group_id: Optional[str] = None):
        self.project_path = Path(project_path)
        self.db = ProjectIndexDatabase(db_path)
        self.project_group_id = project_group_id
        
        # 编译正则表达式
        self.import_pattern = re.compile(r'import\s+([\w.*]+);')
        self.class_usage_pattern = re.compile(r'\b([A-Z]\w*)\b')
    
    def validate_and_fix_imports(self, test_code: str, target_class_fqn: str) -> Tuple[str, List[str]]:
        """验证和修复测试代码中的导入语句"""
        logger.info("验证和修复导入语句")
        
        fixes_applied = []
        
        # 1. 提取现有导入
        existing_imports = self._extract_imports(test_code)
        
        # 2. 提取代码中使用的类
        used_classes = self._extract_used_classes(test_code)
        
        # 3. 验证和修复每个类的导入
        corrected_imports = {}
        for class_name in used_classes:
            if self._is_local_class(class_name):
                correct_import = self._find_correct_import(class_name, target_class_fqn)
                if correct_import:
                    current_import = self._find_current_import(class_name, existing_imports)
                    if current_import != correct_import:
                        corrected_imports[class_name] = correct_import
                        if current_import:
                            fixes_applied.append(f"修正导入: {current_import} -> {correct_import}")
                        else:
                            fixes_applied.append(f"添加导入: {correct_import}")
        
        # 4. 应用修复
        fixed_code = self._apply_import_fixes(test_code, corrected_imports)
        
        return fixed_code, fixes_applied
    
    def _extract_imports(self, code: str) -> Dict[str, str]:
        """提取现有导入语句"""
        imports = {}
        for match in self.import_pattern.finditer(code):
            import_stmt = match.group(1)
            if '.' in import_stmt:
                class_name = import_stmt.split('.')[-1]
                imports[class_name] = import_stmt
        return imports
    
    def _extract_used_classes(self, code: str) -> Set[str]:
        """提取代码中使用的类名"""
        used_classes = set()
        
        # 移除字符串和注释
        code_without_strings = re.sub(r'"[^"]*"', '', code)
        code_without_comments = re.sub(r'//.*|/\*.*?\*/', '', code_without_strings, flags=re.DOTALL)
        
        # 查找类名模式
        for match in self.class_usage_pattern.finditer(code_without_comments):
            class_name = match.group(1)
            
            # 过滤掉Java关键字和常见的非类名
            if not self._is_java_keyword(class_name):
                used_classes.add(class_name)
        
        return used_classes
    
    def _is_java_keyword(self, word: str) -> bool:
        """判断是否是Java关键字"""
        keywords = {
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
            'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
            'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
            'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new',
            'package', 'private', 'protected', 'public', 'return', 'short', 'static',
            'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
            'transient', 'try', 'void', 'volatile', 'while', 'true', 'false', 'null'
        }
        return word.lower() in keywords
    
    def _is_local_class(self, class_name: str) -> bool:
        """判断是否是本地项目的类"""
        if not class_name:
            return False
        
        # 检查是否是基本类型
        basic_types = {'String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Character', 'Byte', 'Short'}
        if class_name in basic_types:
            return False
        
        # 检查数据库中是否存在
        classes = self.db.get_class_by_simple_name(class_name)
        if not classes:
            return False
        
        # 检查是否是项目内的类
        for cls in classes:
            if self._is_project_class(cls.fully_qualified_name):
                return True
        
        return False
    
    def _is_project_class(self, fqn: str) -> bool:
        """判断是否是项目类"""
        if self.project_group_id:
            return fqn.startswith(self.project_group_id)
        
        # 如果没有group_id，使用启发式方法
        # 检查是否以com.example开头（常见的示例项目前缀）
        return fqn.startswith('com.example')
    
    def _find_correct_import(self, class_name: str, target_class_fqn: str) -> Optional[str]:
        """查找正确的导入语句"""
        classes = self.db.get_class_by_simple_name(class_name)
        if not classes:
            return None
        
        # 优先选择与目标类在同一包或子包的类
        target_package = '.'.join(target_class_fqn.split('.')[:-1])
        
        best_match = None
        best_score = -1
        
        for cls in classes:
            if not self._is_project_class(cls.fully_qualified_name):
                continue
            
            score = self._calculate_package_similarity(cls.package, target_package)
            if score > best_score:
                best_score = score
                best_match = cls.fully_qualified_name
        
        return best_match
    
    def _calculate_package_similarity(self, package1: str, package2: str) -> int:
        """计算包路径相似度"""
        parts1 = package1.split('.')
        parts2 = package2.split('.')
        
        # 计算公共前缀长度
        common_prefix = 0
        for i in range(min(len(parts1), len(parts2))):
            if parts1[i] == parts2[i]:
                common_prefix += 1
            else:
                break
        
        return common_prefix
    
    def _find_current_import(self, class_name: str, existing_imports: Dict[str, str]) -> Optional[str]:
        """查找当前的导入语句"""
        return existing_imports.get(class_name)
    
    def _apply_import_fixes(self, code: str, corrected_imports: Dict[str, str]) -> str:
        """应用导入修复"""
        if not corrected_imports:
            return code
        
        lines = code.split('\n')
        import_section_end = 0
        
        # 找到导入区域的结束位置
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                import_section_end = i + 1
            elif line.strip() and not line.strip().startswith('package'):
                break
        
        # 移除错误的导入
        filtered_lines = []
        for line in lines:
            if line.strip().startswith('import '):
                import_stmt = line.strip()[7:-1]  # 移除'import '和';'
                class_name = import_stmt.split('.')[-1]
                if class_name not in corrected_imports:
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)
        
        # 添加正确的导入
        new_imports = []
        for class_name, correct_fqn in corrected_imports.items():
            new_imports.append(f"import {correct_fqn};")
        
        # 插入新导入
        if import_section_end > 0:
            # 在现有导入区域后插入
            result_lines = (filtered_lines[:import_section_end] + 
                          new_imports + 
                          filtered_lines[import_section_end:])
        else:
            # 在package语句后插入
            package_line_end = 0
            for i, line in enumerate(filtered_lines):
                if line.strip().startswith('package '):
                    package_line_end = i + 1
                    break
            
            result_lines = (filtered_lines[:package_line_end] + 
                          [''] + new_imports + [''] +
                          filtered_lines[package_line_end:])
        
        return '\n'.join(result_lines)
    
    def analyze_compilation_errors(self, error_output: str) -> Dict[str, List[str]]:
        """分析编译错误并提取需要修复的信息"""
        logger.info("分析编译错误")
        
        error_analysis = {
            'missing_imports': [],
            'wrong_constructors': [],
            'wrong_parameters': [],
            'package_errors': []
        }
        
        lines = error_output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 检测缺失的导入
            if '找不到符号' in line or 'cannot find symbol' in line.lower():
                # 提取类名
                class_match = re.search(r'类\s+(\w+)|symbol:\s+class\s+(\w+)', line)
                if class_match:
                    class_name = class_match.group(1) or class_match.group(2)
                    error_analysis['missing_imports'].append(class_name)
            
            # 检测构造器错误
            elif '构造器' in line or 'constructor' in line.lower():
                error_analysis['wrong_constructors'].append(line)
            
            # 检测参数错误
            elif '参数' in line or 'parameter' in line.lower():
                error_analysis['wrong_parameters'].append(line)
            
            # 检测包路径错误
            elif '包不存在' in line or 'package does not exist' in line.lower():
                error_analysis['package_errors'].append(line)
        
        return error_analysis
    
    def generate_fix_context(self, error_analysis: Dict[str, List[str]], 
                           target_class_fqn: str) -> str:
        """根据错误分析生成修复上下文"""
        logger.info("生成修复上下文")
        
        context_parts = []
        
        # 处理缺失的导入
        if error_analysis['missing_imports']:
            context_parts.append("## 缺失的类导入信息:")
            for class_name in error_analysis['missing_imports']:
                class_info = self._get_class_context_for_fix(class_name, target_class_fqn)
                if class_info:
                    context_parts.append(class_info)
        
        # 处理构造器错误
        if error_analysis['wrong_constructors']:
            context_parts.append("## 构造器错误信息:")
            context_parts.extend(error_analysis['wrong_constructors'])
        
        # 处理参数错误
        if error_analysis['wrong_parameters']:
            context_parts.append("## 参数错误信息:")
            context_parts.extend(error_analysis['wrong_parameters'])
        
        return '\n'.join(context_parts)
    
    def _get_class_context_for_fix(self, class_name: str, target_class_fqn: str) -> Optional[str]:
        """获取用于修复的类上下文信息"""
        correct_fqn = self._find_correct_import(class_name, target_class_fqn)
        if not correct_fqn:
            return None
        
        class_index = self.db.get_class_by_fqn(correct_fqn)
        if not class_index:
            return None
        
        context_lines = [
            f"类名: {class_name}",
            f"完全限定名: {correct_fqn}",
            f"导入语句: import {correct_fqn};"
        ]
        
        # 添加构造器信息
        if class_index.constructors:
            context_lines.append("可用构造器:")
            for constructor in class_index.constructors:
                if constructor.access_modifier == "public":
                    params = ", ".join(constructor.parameters)
                    context_lines.append(f"  public {class_name}({params})")
        
        # 添加静态工厂方法
        static_methods = [m for m in class_index.methods 
                         if m.is_static and m.access_modifier == "public" 
                         and m.return_type == class_name]
        if static_methods:
            context_lines.append("静态工厂方法:")
            for method in static_methods:
                params = ", ".join(method.parameters)
                context_lines.append(f"  public static {method.return_type} {method.name}({params})")
        
        return '\n'.join(context_lines)
