"""
外部库类映射器
用于映射外部库类的正确包路径
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ExternalLibraryMapper:
    """外部库类映射器"""
    
    def __init__(self):
        # 常见外部库类的包路径映射
        self.library_mappings = {
            # iText PDF库
            'PdfContentByte': 'com.itextpdf.text.pdf.PdfContentByte',
            'BaseColor': 'com.itextpdf.text.BaseColor',
            'Document': 'com.itextpdf.text.Document',
            'PdfWriter': 'com.itextpdf.text.pdf.PdfWriter',
            'PdfReader': 'com.itextpdf.text.pdf.PdfReader',
            'PdfStamper': 'com.itextpdf.text.pdf.PdfStamper',
            
            # Java标准库
            'Rectangle': 'java.awt.Rectangle',
            'Color': 'java.awt.Color',
            'BufferedImage': 'java.awt.image.BufferedImage',
            'File': 'java.io.File',
            'IOException': 'java.io.IOException',
            'List': 'java.util.List',
            'ArrayList': 'java.util.ArrayList',
            'Map': 'java.util.Map',
            'HashMap': 'java.util.HashMap',
            'Set': 'java.util.Set',
            'HashSet': 'java.util.HashSet',
            'Optional': 'java.util.Optional',
            'Stream': 'java.util.stream.Stream',
            
            # Spring框架
            'Component': 'org.springframework.stereotype.Component',
            'Service': 'org.springframework.stereotype.Service',
            'Repository': 'org.springframework.stereotype.Repository',
            'Controller': 'org.springframework.stereotype.Controller',
            'RestController': 'org.springframework.web.bind.annotation.RestController',
            'Autowired': 'org.springframework.beans.factory.annotation.Autowired',
            
            # Lombok
            'RequiredArgsConstructor': 'lombok.RequiredArgsConstructor',
            'AllArgsConstructor': 'lombok.AllArgsConstructor',
            'NoArgsConstructor': 'lombok.NoArgsConstructor',
            'Data': 'lombok.Data',
            'Getter': 'lombok.Getter',
            'Setter': 'lombok.Setter',
            
            # JUnit 5
            'Test': 'org.junit.jupiter.api.Test',
            'BeforeEach': 'org.junit.jupiter.api.BeforeEach',
            'AfterEach': 'org.junit.jupiter.api.AfterEach',
            'BeforeAll': 'org.junit.jupiter.api.BeforeAll',
            'AfterAll': 'org.junit.jupiter.api.AfterAll',
            'ExtendWith': 'org.junit.jupiter.api.extension.ExtendWith',
            'Assertions': 'org.junit.jupiter.api.Assertions',
            
            # Mockito
            'Mock': 'org.mockito.Mock',
            'InjectMocks': 'org.mockito.InjectMocks',
            'MockitoExtension': 'org.mockito.junit.jupiter.MockitoExtension',
            'Mockito': 'org.mockito.Mockito',
            
            # Diff库
            'DiffUtils': 'com.github.difflib.DiffUtils',
            'Patch': 'com.github.difflib.patch.Patch',
            'Delta': 'com.github.difflib.patch.Delta',
            'AbstractDelta': 'com.github.difflib.patch.AbstractDelta',
            'Chunk': 'com.github.difflib.patch.Chunk',
        }
    
    def get_import_statement(self, class_name: str) -> Optional[str]:
        """
        获取类的导入语句
        
        Args:
            class_name: 类名
            
        Returns:
            导入语句，如果找不到则返回None
        """
        full_class_name = self.library_mappings.get(class_name)
        if full_class_name:
            return f"import {full_class_name};"
        return None
    
    def get_package_path(self, class_name: str) -> Optional[str]:
        """
        获取类的包路径
        
        Args:
            class_name: 类名
            
        Returns:
            包路径，如果找不到则返回None
        """
        full_class_name = self.library_mappings.get(class_name)
        if full_class_name:
            return full_class_name.rsplit('.', 1)[0]
        return None
    
    def is_external_library_class(self, class_name: str) -> bool:
        """
        检查是否是外部库类
        
        Args:
            class_name: 类名
            
        Returns:
            是否是外部库类
        """
        return class_name in self.library_mappings
    
    def get_all_import_hints(self, class_names: list) -> Dict[str, str]:
        """
        获取多个类的导入提示
        
        Args:
            class_names: 类名列表
            
        Returns:
            类名到导入语句的映射
        """
        hints = {}
        for class_name in class_names:
            import_stmt = self.get_import_statement(class_name)
            if import_stmt:
                hints[class_name] = import_stmt
        return hints
    
    def add_custom_mapping(self, class_name: str, full_class_name: str):
        """
        添加自定义映射
        
        Args:
            class_name: 简单类名
            full_class_name: 完整类名（包含包路径）
        """
        self.library_mappings[class_name] = full_class_name
        logger.debug(f"添加自定义映射: {class_name} -> {full_class_name}")
    
    def get_constructor_hints(self, class_name: str) -> Optional[str]:
        """
        获取构造函数提示
        
        Args:
            class_name: 类名
            
        Returns:
            构造函数提示
        """
        constructor_hints = {
            'Rectangle': 'new Rectangle(x, y, width, height)',
            'BaseColor': 'BaseColor.RED, BaseColor.GREEN, BaseColor.BLUE',
            'ArrayList': 'new ArrayList<>()',
            'HashMap': 'new HashMap<>()',
            'HashSet': 'new HashSet<>()',
            'File': 'new File("path")',
        }
        return constructor_hints.get(class_name)


# 全局实例
external_library_mapper = ExternalLibraryMapper()
