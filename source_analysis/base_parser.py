"""
基础解析器抽象类
定义了所有语言解析器必须实现的接口
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Set, Tuple, List, Optional, Any
import tree_sitter
from tree_sitter import Language, Parser, Node

class ParsedMethod:
    """解析后的方法信息"""
    def __init__(self, name: str, signature: str, body: str, 
                 start_line: int, end_line: int, access_modifier: str = "public"):
        self.name = name
        self.signature = signature
        self.body = body
        self.start_line = start_line
        self.end_line = end_line
        self.access_modifier = access_modifier

class ParsedClass:
    """解析后的类信息"""
    def __init__(self, name: str, package: str, imports: List[str], 
                 methods: List[ParsedMethod], full_code: str):
        self.name = name
        self.package = package
        self.imports = imports
        self.methods = methods
        self.full_code = full_code

class BaseLanguageParser(ABC):
    """基础语言解析器抽象类"""
    
    def __init__(self, language: str):
        self.language = language
        self.parser = self._init_parser()
        
    @abstractmethod
    def _init_parser(self) -> Parser:
        """初始化Tree-sitter解析器"""
        pass
    
    @abstractmethod
    def get_language_extensions(self) -> List[str]:
        """获取语言的文件扩展名"""
        pass
    
    @abstractmethod
    def get_test_framework(self) -> str:
        """获取测试框架名称"""
        pass
    
    def parse_file(self, file_path: Path) -> ParsedClass:
        """解析文件并返回结构化信息"""
        content = file_path.read_text(encoding='utf-8')
        tree = self.parser.parse(content.encode('utf-8'))
        return self._extract_class_info(tree.root_node, content)
    
    @abstractmethod
    def _extract_class_info(self, root_node: Node, content: str) -> ParsedClass:
        """从AST提取类信息"""
        pass
    
    @abstractmethod
    def extract_dependencies(self, parsed_class: ParsedClass, method_name: str) -> Dict[str, Set[str]]:
        """提取方法的依赖关系"""
        pass
    
    @abstractmethod
    def extract_method_slice(self, parsed_class: ParsedClass, method_name: str) -> Optional[str]:
        """提取方法的代码切片"""
        pass
    
    @abstractmethod
    def generate_test_scaffold(self, parsed_class: ParsedClass, output_dir: Path) -> Tuple[str, Path]:
        """生成测试脚手架"""
        pass
    
    @abstractmethod
    def compile_test(self, test_file: Path, project_path: Path) -> Tuple[bool, str]:
        """编译测试文件"""
        pass
    
    @abstractmethod
    def run_test(self, test_file: Path, project_path: Path) -> Tuple[bool, str]:
        """运行测试文件"""
        pass
    
    def find_method(self, parsed_class: ParsedClass, method_name: str) -> Optional[ParsedMethod]:
        """查找指定的方法"""
        for method in parsed_class.methods:
            if method.name == method_name:
                return method
        return None
    
    def get_node_text(self, node: Node, content: str) -> str:
        """获取节点的文本内容"""
        return content[node.start_byte:node.end_byte]
    
    def find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """递归查找指定类型的所有节点"""
        result = []
        
        if node.type == node_type:
            result.append(node)
        
        for child in node.children:
            result.extend(self.find_nodes_by_type(child, node_type))
        
        return result

class LanguageDetector:
    """语言检测器"""
    
    def __init__(self):
        self.language_map = {
            '.java': 'java',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp'
        }
    
    def detect_language(self, file_path: Path) -> Optional[str]:
        """根据文件扩展名检测编程语言"""
        suffix = file_path.suffix.lower()
        return self.language_map.get(suffix)
    
    def detect_project_language(self, project_path: Path) -> Dict[str, int]:
        """检测项目中各语言的文件数量"""
        language_counts = {}
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                language = self.detect_language(file_path)
                if language:
                    language_counts[language] = language_counts.get(language, 0) + 1
        
        return language_counts
    
    def get_primary_language(self, project_path: Path) -> Optional[str]:
        """获取项目的主要编程语言"""
        language_counts = self.detect_project_language(project_path)
        if not language_counts:
            return None
        
        return max(language_counts.items(), key=lambda x: x[1])[0]

class ParserFactory:
    """解析器工厂"""
    
    _parsers = {}
    
    @classmethod
    def register_parser(cls, language: str, parser_class):
        """注册解析器"""
        cls._parsers[language] = parser_class
    
    @classmethod
    def create_parser(cls, language: str) -> Optional[BaseLanguageParser]:
        """创建指定语言的解析器"""
        parser_class = cls._parsers.get(language)
        if parser_class:
            return parser_class(language)
        return None
    
    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """获取支持的语言列表"""
        return list(cls._parsers.keys())
    
    @classmethod
    def is_language_supported(cls, language: str) -> bool:
        """检查是否支持指定语言"""
        return language in cls._parsers
