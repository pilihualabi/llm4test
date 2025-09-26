#!/usr/bin/env python3
"""
错误驱动的上下文增强器
从编译/运行错误中提取缺失的类和方法信息，动态补充上下文
"""

import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

@dataclass
class MissingSymbol:
    """缺失的符号信息"""
    symbol_name: str
    symbol_type: str  # 'class', 'method', 'field', 'import'
    context: str      # 错误上下文
    line_number: Optional[int] = None
    suggested_import: Optional[str] = None

class ErrorContextEnhancer:
    """错误驱动的上下文增强器"""
    
    def __init__(self, project_index, static_analyzer):
        self.project_index = project_index
        self.static_analyzer = static_analyzer
        self.logger = logging.getLogger(__name__)
        
        # 编译错误模式
        self.compilation_error_patterns = {
            'missing_symbol': [
                r'找不到符号.*?符号:\s*(\w+)\s*(\w+)\s*(.+)',
                r'cannot find symbol.*?symbol:\s*(\w+)\s*(\w+)\s*(.+)',
            ],
            'missing_import': [
                r'符号:\s*类\s*(\w+)',
                r'symbol:\s*class\s*(\w+)',
                r'找不到符号.*?类\s*(\w+)',
                r'cannot find symbol.*?class\s*(\w+)',
            ],
            'method_not_found': [
                r'符号:\s*方法\s*(\w+)\(',
                r'symbol:\s*method\s*(\w+)\(',
                r'找不到符号.*?方法\s*(\w+)\(',
                r'cannot find symbol.*?method\s*(\w+)\(',
            ],
            'void_return_error': [
                r'此处不允许使用.*?空.*?类型',
                r'void type not allowed here',
            ]
        }
        
        # 运行时错误模式
        self.runtime_error_patterns = {
            'class_not_found': [
                r'ClassNotFoundException.*?(\w+(?:\.\w+)*)',
                r'NoClassDefFoundError.*?(\w+(?:\.\w+)*)',
            ],
            'method_not_found': [
                r'NoSuchMethodException.*?(\w+)\.(\w+)',
                r'NoSuchMethodError.*?(\w+)\.(\w+)',
            ],
            'null_pointer': [
                r'NullPointerException.*?at\s+(\w+(?:\.\w+)*)\.(\w+)',
            ]
        }

    def analyze_compilation_errors(self, error_output: str) -> List[MissingSymbol]:
        """分析编译错误，提取缺失的符号"""
        missing_symbols = []
        
        for error_type, patterns in self.compilation_error_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, error_output, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    symbol = self._extract_symbol_from_compilation_error(
                        error_type, match, error_output
                    )
                    if symbol:
                        missing_symbols.append(symbol)
        
        return self._deduplicate_symbols(missing_symbols)

    def analyze_runtime_errors(self, error_output: str) -> List[MissingSymbol]:
        """分析运行时错误，提取缺失的符号"""
        missing_symbols = []
        
        for error_type, patterns in self.runtime_error_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, error_output, re.MULTILINE)
                for match in matches:
                    symbol = self._extract_symbol_from_runtime_error(
                        error_type, match, error_output
                    )
                    if symbol:
                        missing_symbols.append(symbol)
        
        return self._deduplicate_symbols(missing_symbols)

    def _extract_symbol_from_compilation_error(self, error_type: str, 
                                             match: re.Match, 
                                             full_error: str) -> Optional[MissingSymbol]:
        """从编译错误中提取符号信息"""
        try:
            if error_type == 'missing_import':
                class_name = match.group(1)
                return MissingSymbol(
                    symbol_name=class_name,
                    symbol_type='class',
                    context=match.group(0),
                    suggested_import=self._suggest_import(class_name)
                )
            
            elif error_type == 'method_not_found':
                method_name = match.group(1)
                return MissingSymbol(
                    symbol_name=method_name,
                    symbol_type='method',
                    context=match.group(0)
                )
            
            elif error_type == 'void_return_error':
                # 这通常表示对void方法使用了.thenReturn()
                return MissingSymbol(
                    symbol_name='void_method_mock',
                    symbol_type='method',
                    context=match.group(0)
                )
                
        except Exception as e:
            self.logger.warning(f"解析编译错误失败: {e}")
            
        return None

    def _extract_symbol_from_runtime_error(self, error_type: str, 
                                         match: re.Match, 
                                         full_error: str) -> Optional[MissingSymbol]:
        """从运行时错误中提取符号信息"""
        try:
            if error_type == 'class_not_found':
                class_name = match.group(1)
                return MissingSymbol(
                    symbol_name=class_name,
                    symbol_type='class',
                    context=match.group(0)
                )
            
            elif error_type == 'method_not_found':
                class_name = match.group(1)
                method_name = match.group(2)
                return MissingSymbol(
                    symbol_name=f"{class_name}.{method_name}",
                    symbol_type='method',
                    context=match.group(0)
                )
                
        except Exception as e:
            self.logger.warning(f"解析运行时错误失败: {e}")
            
        return None

    def _suggest_import(self, class_name: str) -> Optional[str]:
        """根据类名建议导入语句"""
        # 常见的类名到包的映射
        common_imports = {
            'PdfContentByte': 'com.itextpdf.text.pdf.PdfContentByte',
            'IOException': 'java.io.IOException',
            'DocumentException': 'com.itextpdf.text.DocumentException',
            'PageSize': 'com.itextpdf.text.PageSize',
            'PdfImportedPage': 'com.itextpdf.text.pdf.PdfImportedPage',
            'IntStream': 'java.util.stream.IntStream',
        }
        
        return common_imports.get(class_name)

    def _deduplicate_symbols(self, symbols: List[MissingSymbol]) -> List[MissingSymbol]:
        """去重符号列表"""
        seen = set()
        unique_symbols = []
        
        for symbol in symbols:
            key = (symbol.symbol_name, symbol.symbol_type)
            if key not in seen:
                seen.add(key)
                unique_symbols.append(symbol)
        
        return unique_symbols

    def is_local_class(self, class_name: str) -> bool:
        """判断是否为本地项目中的类"""
        try:
            # 尝试从项目索引中查找
            if self.project_index and self.project_index.get_class_by_simple_name(class_name):
                return True

            # 检查是否以项目包名开头
            if class_name.startswith('com.example.'):
                return True

            # 检查常见的第三方库包名
            third_party_prefixes = [
                'java.', 'javax.', 'org.junit.', 'org.mockito.',
                'com.itextpdf.', 'org.springframework.', 'org.apache.'
            ]

            for prefix in third_party_prefixes:
                if class_name.startswith(prefix):
                    return False

            # 对于简单类名，检查是否是常见的第三方类
            third_party_classes = {
                'PdfContentByte', 'IOException', 'DocumentException',
                'PageSize', 'PdfImportedPage', 'IntStream'
            }

            if class_name in third_party_classes:
                return False

            # 默认认为是本地类
            return True

        except Exception as e:
            self.logger.warning(f"判断本地类失败: {e}")
            return False

    def enhance_context_from_errors(self, error_output: str,
                                   error_type: str = 'compilation') -> List[Dict]:
        """从错误中增强上下文"""
        if error_type == 'compilation':
            missing_symbols = self.analyze_compilation_errors(error_output)
        else:
            missing_symbols = self.analyze_runtime_errors(error_output)

        enhanced_contexts = []

        for symbol in missing_symbols:
            if symbol.symbol_type == 'class':
                if self.is_local_class(symbol.symbol_name):
                    # 获取本地类的详细信息
                    class_context = self._get_class_context(symbol.symbol_name)
                    if class_context:
                        enhanced_contexts.append(class_context)
                elif symbol.suggested_import:
                    # 为第三方类提供导入建议
                    import_context = self._create_import_suggestion_context(symbol)
                    if import_context:
                        enhanced_contexts.append(import_context)

            elif symbol.symbol_type == 'method':
                # 获取方法签名信息
                method_context = self._get_method_context(symbol.symbol_name)
                if method_context:
                    enhanced_contexts.append(method_context)
                elif symbol.symbol_name in ['assertNotNull', 'assertThrows', 'assertEquals']:
                    # 为JUnit断言方法提供导入建议
                    junit_context = self._create_junit_import_context(symbol.symbol_name)
                    if junit_context:
                        enhanced_contexts.append(junit_context)

        return enhanced_contexts

    def _get_class_context(self, class_name: str) -> Optional[Dict]:
        """获取类的上下文信息"""
        try:
            class_info = self.project_index.get_class_by_simple_name(class_name)
            if not class_info:
                return None
            
            # 获取类的方法签名
            method_signatures = []
            for method in class_info.methods:
                params = ", ".join(method.parameters) if method.parameters else ""
                signature = f"{method.access_modifier} {method.return_type} {method.name}({params})"
                if method.exceptions:
                    signature += f" throws {', '.join(method.exceptions)}"
                method_signatures.append(signature)
            
            return {
                "content": f"Class: {class_info.fqn}\nMethods:\n" + "\n".join(method_signatures),
                "metadata": {
                    "type": "error_enhanced_context",
                    "class_name": class_info.fqn,
                    "source": "error_analysis"
                },
                "distance": 0.0
            }
            
        except Exception as e:
            self.logger.error(f"获取类上下文失败: {e}")
            return None

    def _get_method_context(self, method_identifier: str) -> Optional[Dict]:
        """获取方法的上下文信息"""
        try:
            # 解析方法标识符 (class.method 或 method)
            if '.' in method_identifier:
                class_name, method_name = method_identifier.rsplit('.', 1)
                class_info = self.project_index.get_class_by_simple_name(class_name)
            else:
                method_name = method_identifier
                # 需要在所有类中搜索该方法
                class_info = None
            
            if class_info:
                for method in class_info.methods:
                    if method.name == method_name:
                        params = ", ".join(method.parameters) if method.parameters else ""
                        signature = f"{method.access_modifier} {method.return_type} {method.name}({params})"
                        if method.exceptions:
                            signature += f" throws {', '.join(method.exceptions)}"
                        
                        return {
                            "content": f"Method signature: {signature}",
                            "metadata": {
                                "type": "error_enhanced_context",
                                "method_name": method_name,
                                "class_name": class_info.fqn,
                                "source": "error_analysis"
                            },
                            "distance": 0.0
                        }
            
        except Exception as e:
            self.logger.error(f"获取方法上下文失败: {e}")

        return None

    def _create_import_suggestion_context(self, symbol: MissingSymbol) -> Optional[Dict]:
        """为第三方类创建导入建议上下文"""
        try:
            if not symbol.suggested_import:
                return None

            content = f"Missing import for {symbol.symbol_name}:\n"
            content += f"Add this import statement: import {symbol.suggested_import};\n"
            content += f"Class: {symbol.symbol_name}\n"
            content += f"Full package: {symbol.suggested_import}"

            return {
                "content": content,
                "metadata": {
                    "type": "import_suggestion",
                    "class_name": symbol.symbol_name,
                    "import_statement": symbol.suggested_import,
                    "source": "error_analysis"
                },
                "distance": 0.0
            }

        except Exception as e:
            self.logger.error(f"创建导入建议上下文失败: {e}")
            return None

    def _create_junit_import_context(self, method_name: str) -> Optional[Dict]:
        """为JUnit断言方法创建导入建议上下文"""
        try:
            content = f"Missing JUnit assertion method: {method_name}\n"
            content += f"Add this import statement: import static org.junit.jupiter.api.Assertions.*;\n"
            content += f"This will provide access to: {method_name}, assertEquals, assertTrue, assertFalse, etc.\n"
            content += f"Alternative: import static org.junit.jupiter.api.Assertions.{method_name};"

            return {
                "content": content,
                "metadata": {
                    "type": "junit_import_suggestion",
                    "method_name": method_name,
                    "import_statement": "import static org.junit.jupiter.api.Assertions.*;",
                    "source": "error_analysis"
                },
                "distance": 0.0
            }

        except Exception as e:
            self.logger.error(f"创建JUnit导入建议上下文失败: {e}")
            return None
