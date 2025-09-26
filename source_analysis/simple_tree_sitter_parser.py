"""
简化版Tree-sitter解析器
专注于Java支持，使用更简单的解析方法
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class ParsedMethod:
    """解析的方法信息"""
    name: str
    signature: str
    body: str
    start_line: int
    end_line: int
    access_modifier: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []

@dataclass
class ParsedClass:
    """解析的类信息"""
    name: str
    package: Optional[str] = None
    imports: List[str] = None
    methods: List[ParsedMethod] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.methods is None:
            self.methods = []

class SimpleTreeSitterParser:
    """简化版Tree-sitter解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.java_parser = None
        self._init_java_parser()
    
    def _init_java_parser(self):
        """初始化Java解析器"""
        try:
            import tree_sitter
            import tree_sitter_java
            
            # 创建Java语言对象
            java_language = tree_sitter.Language(tree_sitter_java.language())
            
            # 创建解析器
            self.java_parser = tree_sitter.Parser(java_language)
            
            logger.info("成功初始化Tree-sitter Java解析器")
        except ImportError as e:
            logger.warning(f"Tree-sitter Java未安装: {e}")
        except Exception as e:
            logger.error(f"初始化Java解析器失败: {e}")
    
    def parse_java_file(self, file_path: Union[str, Path]) -> Optional[ParsedClass]:
        """解析Java文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None
        
        if not self.java_parser:
            logger.error("Java解析器未初始化")
            return None
        
        try:
            # 读取文件内容
            content = file_path.read_text(encoding='utf-8')
            return self.parse_java_content(content)
        except Exception as e:
            logger.error(f"解析Java文件失败 {file_path}: {e}")
            return None
    
    def parse_java_content(self, content: str) -> Optional[ParsedClass]:
        """解析Java代码内容"""
        if not self.java_parser:
            logger.error("Java解析器未初始化")
            return None
        
        try:
            # 解析代码
            tree = self.java_parser.parse(content.encode('utf-8'))
            root_node = tree.root_node
            
            # 使用简单的方法解析
            return self._parse_java_simple(root_node, content)
            
        except Exception as e:
            logger.error(f"解析Java代码失败: {e}")
            return None
    
    def _parse_java_simple(self, root_node, content: str) -> Optional[ParsedClass]:
        """简单的Java解析方法"""
        lines = content.split('\n')
        
        # 使用正则表达式解析基本信息
        package = self._extract_package(content)
        imports = self._extract_imports(content)
        class_name = self._extract_class_name(content)
        
        if not class_name:
            logger.warning("未找到类名")
            return None
        
        # 使用Tree-sitter查找方法
        methods = self._extract_methods_with_tree_sitter(root_node, content)
        
        return ParsedClass(
            name=class_name,
            package=package,
            imports=imports,
            methods=methods
        )
    
    def _extract_package(self, content: str) -> Optional[str]:
        """提取包名"""
        match = re.search(r'package\s+([\w.]+)\s*;', content)
        return match.group(1) if match else None
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取导入语句"""
        imports = []
        for match in re.finditer(r'import\s+([\w.*]+)\s*;', content):
            imports.append(match.group(1))
        return imports
    
    def _extract_class_name(self, content: str) -> Optional[str]:
        """提取类名"""
        # 查找类声明（支持class、record、interface、enum）
        patterns = [
            r'(?:public\s+)?record\s+(\w+)',      # Java record
            r'(?:public\s+)?class\s+(\w+)',       # 普通类
            r'(?:public\s+)?interface\s+(\w+)',   # 接口
            r'(?:public\s+)?enum\s+(\w+)',        # 枚举
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None
    
    def _extract_methods_with_tree_sitter(self, root_node, content: str) -> List[ParsedMethod]:
        """使用Tree-sitter提取方法"""
        methods = []
        
        try:
            # 递归查找方法声明节点
            self._find_method_nodes(root_node, content, methods)
        except Exception as e:
            logger.debug(f"Tree-sitter方法提取失败，使用正则表达式: {e}")
            # 回退到正则表达式
            methods = self._extract_methods_with_regex(content)
        
        return methods
    
    def _find_method_nodes(self, node, content: str, methods: List[ParsedMethod]):
        """递归查找方法节点"""
        if node.type == 'method_declaration':
            method = self._parse_method_node(node, content)
            if method:
                methods.append(method)
        
        # 递归处理子节点
        for child in node.children:
            self._find_method_nodes(child, content, methods)
    
    def _parse_method_node(self, method_node, content: str) -> Optional[ParsedMethod]:
        """解析方法节点"""
        try:
            # 获取方法文本
            method_text = self._get_node_text(method_node, content)
            
            # 获取行号
            start_line = method_node.start_point[0] + 1
            end_line = method_node.end_point[0] + 1
            
            # 查找方法名
            method_name = None
            for child in method_node.children:
                if child.type == 'identifier':
                    method_name = self._get_node_text(child, content)
                    break
            
            if not method_name:
                return None
            
            # 提取访问修饰符
            access_modifier = self._extract_access_modifier(method_text)
            
            # 构建签名
            signature = self._build_method_signature(method_text, method_name)
            
            return ParsedMethod(
                name=method_name,
                signature=signature,
                body=method_text,
                start_line=start_line,
                end_line=end_line,
                access_modifier=access_modifier
            )
            
        except Exception as e:
            logger.debug(f"解析方法节点失败: {e}")
            return None
    
    def _extract_methods_with_regex(self, content: str) -> List[ParsedMethod]:
        """使用正则表达式提取方法（回退方案）"""
        methods = []
        lines = content.split('\n')
        
        # 查找方法声明
        method_pattern = r'((?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{)'
        
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            method_name = match.group(2)
            start_pos = match.start()
            
            # 计算行号
            start_line = content[:start_pos].count('\n') + 1
            
            # 查找方法结束位置（简化版）
            brace_count = 0
            end_pos = start_pos
            in_method = False
            
            for i, char in enumerate(content[start_pos:], start_pos):
                if char == '{':
                    brace_count += 1
                    in_method = True
                elif char == '}' and in_method:
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            end_line = content[:end_pos].count('\n') + 1
            method_text = content[start_pos:end_pos]
            
            # 提取访问修饰符
            access_modifier = self._extract_access_modifier(method_text)
            
            # 构建签名
            signature = self._build_method_signature(method_text, method_name)
            
            methods.append(ParsedMethod(
                name=method_name,
                signature=signature,
                body=method_text,
                start_line=start_line,
                end_line=end_line,
                access_modifier=access_modifier
            ))
        
        return methods
    
    def _extract_access_modifier(self, method_text: str) -> Optional[str]:
        """提取访问修饰符"""
        if 'public' in method_text:
            return 'public'
        elif 'private' in method_text:
            return 'private'
        elif 'protected' in method_text:
            return 'protected'
        return None
    
    def _build_method_signature(self, method_text: str, method_name: str) -> str:
        """构建方法签名"""
        # 简化版签名构建
        lines = method_text.split('\n')
        first_line = lines[0].strip()
        
        # 查找方法声明行
        for line in lines[:3]:  # 通常在前几行
            if method_name in line and '(' in line:
                # 清理并返回
                signature = re.sub(r'\s+', ' ', line.strip())
                if signature.endswith('{'):
                    signature = signature[:-1].strip()
                return signature
        
        return f"public {method_name}()"
    
    def _get_node_text(self, node, content: str) -> str:
        """获取节点对应的文本"""
        return content[node.start_byte:node.end_byte]
    
    def is_available(self) -> bool:
        """检查解析器是否可用"""
        return self.java_parser is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取解析器统计信息"""
        return {
            'java_parser_available': self.java_parser is not None,
            'supported_languages': ['java'] if self.java_parser else [],
            'supported_extensions': ['.java'] if self.java_parser else []
        }
