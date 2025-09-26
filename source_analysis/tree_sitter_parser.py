"""
基于Tree-sitter的多语言AST解析器
支持Java、Python、JavaScript等多种语言
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import tree_sitter
from tree_sitter import Language, Parser, Node

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
    annotations: List[str] = None
    docstring: Optional[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.annotations is None:
            self.annotations = []

@dataclass
class ParsedClass:
    """解析的类信息"""
    name: str
    package: Optional[str] = None
    imports: List[str] = None
    methods: List[ParsedMethod] = None
    fields: List[str] = None
    annotations: List[str] = None
    superclass: Optional[str] = None
    interfaces: List[str] = None
    docstring: Optional[str] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.methods is None:
            self.methods = []
        if self.fields is None:
            self.fields = []
        if self.annotations is None:
            self.annotations = []
        if self.interfaces is None:
            self.interfaces = []

class TreeSitterParser:
    """基于Tree-sitter的多语言解析器"""
    
    # 支持的语言映射
    SUPPORTED_LANGUAGES = {
        '.java': 'java',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'c_sharp',
        '.kt': 'kotlin',
        '.scala': 'scala'
    }
    
    def __init__(self):
        """初始化解析器"""
        self.parsers = {}
        self.languages = {}
        self._init_languages()
    
    def _init_languages(self):
        """初始化支持的语言"""
        try:
            # 尝试加载Java语言
            import tree_sitter_java
            self.languages['java'] = Language(tree_sitter_java.language())
            self.parsers['java'] = Parser(self.languages['java'])
            logger.info("成功初始化Tree-sitter Java解析器")
        except ImportError:
            logger.warning("tree_sitter_java未安装，跳过Java支持")
        except Exception as e:
            logger.error(f"初始化Java解析器失败: {e}")
        
        # 尝试加载其他语言
        language_modules = {
            'python': 'tree_sitter_python',
            'javascript': 'tree_sitter_javascript',
            'typescript': 'tree_sitter_typescript',
            'cpp': 'tree_sitter_cpp',
            'c': 'tree_sitter_c',
            'go': 'tree_sitter_go',
            'rust': 'tree_sitter_rust'
        }
        
        for lang_name, module_name in language_modules.items():
            try:
                module = __import__(module_name)
                self.languages[lang_name] = Language(module.language())
                self.parsers[lang_name] = Parser(self.languages[lang_name])
                logger.debug(f"成功初始化Tree-sitter {lang_name}解析器")
            except ImportError:
                logger.debug(f"{module_name}未安装，跳过{lang_name}支持")
            except Exception as e:
                logger.debug(f"初始化{lang_name}解析器失败: {e}")
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        supported = []
        for ext, lang in self.SUPPORTED_LANGUAGES.items():
            if lang in self.parsers:
                supported.append(ext)
        return supported
    
    def detect_language(self, file_path: Union[str, Path]) -> Optional[str]:
        """检测文件语言"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        return self.SUPPORTED_LANGUAGES.get(extension)
    
    def parse_file(self, file_path: Union[str, Path]) -> Optional[ParsedClass]:
        """解析文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None
        
        # 检测语言
        language = self.detect_language(file_path)
        if not language:
            logger.warning(f"不支持的文件类型: {file_path.suffix}")
            return None
        
        if language not in self.parsers:
            logger.warning(f"未初始化{language}解析器")
            return None
        
        try:
            # 读取文件内容
            content = file_path.read_text(encoding='utf-8')
            return self.parse_content(content, language, file_path)
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
            return None
    
    def parse_content(self, content: str, language: str, file_path: Optional[Path] = None) -> Optional[ParsedClass]:
        """解析代码内容"""
        if language not in self.parsers:
            logger.error(f"不支持的语言: {language}")
            return None
        
        try:
            # 解析代码
            parser = self.parsers[language]
            tree = parser.parse(content.encode('utf-8'))
            
            # 根据语言选择解析方法
            if language == 'java':
                return self._parse_java(tree.root_node, content, file_path)
            elif language == 'python':
                return self._parse_python(tree.root_node, content, file_path)
            elif language in ['javascript', 'typescript']:
                return self._parse_javascript(tree.root_node, content, file_path)
            else:
                logger.warning(f"暂不支持解析{language}语言的详细结构")
                return self._parse_generic(tree.root_node, content, file_path, language)
                
        except Exception as e:
            logger.error(f"解析{language}代码失败: {e}")
            return None
    
    def _parse_java(self, root_node: Node, content: str, file_path: Optional[Path] = None) -> Optional[ParsedClass]:
        """解析Java代码"""
        lines = content.split('\n')
        
        # 查找包声明
        package = None
        try:
            package_query = self.languages['java'].query("(package_declaration (scoped_identifier) @package)")
            captures = package_query.captures(root_node)
            for node, capture_name in captures:
                if capture_name == "package":
                    package = self._get_node_text(node, content)
                    break
        except Exception as e:
            logger.debug(f"查找包声明失败: {e}")
        
        # 查找导入语句
        imports = []
        try:
            import_query = self.languages['java'].query("(import_declaration (scoped_identifier) @import)")
            captures = import_query.captures(root_node)
            for node, capture_name in captures:
                if capture_name == "import":
                    imports.append(self._get_node_text(node, content))
        except Exception as e:
            logger.debug(f"查找导入语句失败: {e}")
        
        # 查找类声明
        class_name = None
        class_node = None
        try:
            class_query = self.languages['java'].query("(class_declaration name: (identifier) @class_name)")
            captures = class_query.captures(root_node)
            for node, capture_name in captures:
                if capture_name == "class_name":
                    class_name = self._get_node_text(node, content)
                    class_node = node.parent
                    break
        except Exception as e:
            logger.debug(f"查找类声明失败: {e}")
        
        if not class_name:
            logger.warning("未找到类声明")
            return None
        
        # 解析方法
        methods = []
        if class_node:
            try:
                method_query = self.languages['java'].query("""
                    (method_declaration
                        name: (identifier) @method_name
                    ) @method
                """)

                captures = method_query.captures(class_node)
                method_nodes = {}

                for node, capture_name in captures:
                    if capture_name == "method_name":
                        method_name = self._get_node_text(node, content)
                        method_nodes[method_name] = {'name': method_name, 'name_node': node}
                    elif capture_name == "method":
                        # 找到对应的方法名
                        for child in node.children:
                            if child.type == "identifier":
                                method_name = self._get_node_text(child, content)
                                if method_name in method_nodes:
                                    method_nodes[method_name]['method_node'] = node
                                break

                for method_info in method_nodes.values():
                    if 'method_node' in method_info:
                        method = self._parse_java_method(method_info['method_node'], content, method_info['name'])
                        if method:
                            methods.append(method)
            except Exception as e:
                logger.debug(f"解析方法失败: {e}")
        
        return ParsedClass(
            name=class_name,
            package=package,
            imports=imports,
            methods=methods
        )
    
    def _parse_java_method(self, method_node: Node, content: str, method_name: str) -> Optional[ParsedMethod]:
        """解析Java方法"""
        try:
            # 获取方法文本
            method_text = self._get_node_text(method_node, content)
            
            # 获取行号
            start_line = method_node.start_point[0] + 1
            end_line = method_node.end_point[0] + 1
            
            # 提取访问修饰符
            access_modifier = None
            try:
                modifiers_query = self.languages['java'].query("(modifiers) @modifiers")
                captures = modifiers_query.captures(method_node)
                for node, capture_name in captures:
                    if capture_name == "modifiers":
                        modifiers_text = self._get_node_text(node, content)
                        if 'public' in modifiers_text:
                            access_modifier = 'public'
                        elif 'private' in modifiers_text:
                            access_modifier = 'private'
                        elif 'protected' in modifiers_text:
                            access_modifier = 'protected'
                        break
            except Exception as e:
                logger.debug(f"提取访问修饰符失败: {e}")
            
            # 构建方法签名（简化版）
            signature = f"{access_modifier or ''} {method_name}()".strip()
            
            return ParsedMethod(
                name=method_name,
                signature=signature,
                body=method_text,
                start_line=start_line,
                end_line=end_line,
                access_modifier=access_modifier
            )
            
        except Exception as e:
            logger.error(f"解析Java方法失败: {e}")
            return None
    
    def _parse_python(self, root_node: Node, content: str, file_path: Optional[Path] = None) -> Optional[ParsedClass]:
        """解析Python代码"""
        # Python解析逻辑（简化版）
        class_name = file_path.stem if file_path else "PythonModule"
        methods = []
        
        # 查找函数定义
        if 'python' in self.languages:
            function_query = self.languages['python'].query("(function_definition name: (identifier) @func_name) @func")
            
            for match in function_query.matches(root_node):
                func_node = None
                func_name = None
                
                for node_id, node in match:
                    if node_id == "func_name":
                        func_name = self._get_node_text(node, content)
                    elif node_id == "func":
                        func_node = node
                
                if func_name and func_node:
                    method = self._parse_python_function(func_node, content, func_name)
                    if method:
                        methods.append(method)
        
        return ParsedClass(
            name=class_name,
            methods=methods
        )
    
    def _parse_python_function(self, func_node: Node, content: str, func_name: str) -> Optional[ParsedMethod]:
        """解析Python函数"""
        try:
            func_text = self._get_node_text(func_node, content)
            start_line = func_node.start_point[0] + 1
            end_line = func_node.end_point[0] + 1
            
            signature = f"def {func_name}()"
            
            return ParsedMethod(
                name=func_name,
                signature=signature,
                body=func_text,
                start_line=start_line,
                end_line=end_line
            )
            
        except Exception as e:
            logger.error(f"解析Python函数失败: {e}")
            return None
    
    def _parse_javascript(self, root_node: Node, content: str, file_path: Optional[Path] = None) -> Optional[ParsedClass]:
        """解析JavaScript/TypeScript代码"""
        # JavaScript解析逻辑（简化版）
        class_name = file_path.stem if file_path else "JSModule"
        methods = []
        
        # 查找函数声明
        if 'javascript' in self.languages:
            function_query = self.languages['javascript'].query("(function_declaration name: (identifier) @func_name) @func")
            
            for match in function_query.matches(root_node):
                func_node = None
                func_name = None
                
                for node_id, node in match:
                    if node_id == "func_name":
                        func_name = self._get_node_text(node, content)
                    elif node_id == "func":
                        func_node = node
                
                if func_name and func_node:
                    method = self._parse_js_function(func_node, content, func_name)
                    if method:
                        methods.append(method)
        
        return ParsedClass(
            name=class_name,
            methods=methods
        )
    
    def _parse_js_function(self, func_node: Node, content: str, func_name: str) -> Optional[ParsedMethod]:
        """解析JavaScript函数"""
        try:
            func_text = self._get_node_text(func_node, content)
            start_line = func_node.start_point[0] + 1
            end_line = func_node.end_point[0] + 1
            
            signature = f"function {func_name}()"
            
            return ParsedMethod(
                name=func_name,
                signature=signature,
                body=func_text,
                start_line=start_line,
                end_line=end_line
            )
            
        except Exception as e:
            logger.error(f"解析JavaScript函数失败: {e}")
            return None
    
    def _parse_generic(self, root_node: Node, content: str, file_path: Optional[Path] = None, language: str = "unknown") -> Optional[ParsedClass]:
        """通用解析方法"""
        class_name = f"{file_path.stem if file_path else 'GenericFile'}_{language}"
        
        return ParsedClass(
            name=class_name,
            methods=[]
        )
    
    def _get_node_text(self, node: Node, content: str) -> str:
        """获取节点对应的文本"""
        return content[node.start_byte:node.end_byte]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取解析器统计信息"""
        return {
            'supported_languages': list(self.parsers.keys()),
            'supported_extensions': self.get_supported_extensions(),
            'total_parsers': len(self.parsers)
        }
