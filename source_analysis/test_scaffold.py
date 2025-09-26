"""
Test scaffold generation module for creating test class templates with necessary imports.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
# 移除对已删除模块的导入
# from config import test_config

logger = logging.getLogger(__name__)

class TestScaffoldGenerator:
    """测试脚手架生成器"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    def generate_test_scaffold(
        self,
        class_name: str,
        method_name: str,
        package_name: str = None,
        test_style: str = "comprehensive"
    ) -> str:
        """
        生成测试脚手架
        
        Args:
            class_name: 类名
            method_name: 方法名
            package_name: 包名
            test_style: 测试风格
            
        Returns:
            生成的测试代码
        """
        if not package_name:
            package_name = self._detect_package_name()
        
        # 生成测试类名
        test_class_name = f"{class_name}Test"
        
        # 生成测试代码
        test_code = self._generate_test_class(
            package_name, test_class_name, class_name, method_name, test_style
        )
        
        return test_code
    
    def _detect_package_name(self) -> str:
        """检测包名"""
        # 尝试从项目结构推断包名
        src_dirs = [
            self.project_path / "src" / "main" / "java",
            self.project_path / "src" / "main" / "kotlin",
            self.project_path / "src" / "main" / "groovy"
        ]
        
        for src_dir in src_dirs:
            if src_dir.exists():
                # 查找第一个Java文件来推断包名
                java_files = list(src_dir.rglob("*.java"))
                if java_files:
                    # 从文件路径推断包名
                    relative_path = java_files[0].relative_to(src_dir)
                    package_parts = relative_path.parent.parts
                    if package_parts:
                        return ".".join(package_parts)
        
        # 默认包名
        return "com.example.test"
    
    def _generate_test_class(
        self,
        package_name: str,
        test_class_name: str,
        class_name: str,
        method_name: str,
        test_style: str
    ) -> str:
        """生成测试类"""
        
        # 基础导入
        imports = [
            "import org.junit.jupiter.api.Test;",
            "import org.junit.jupiter.api.BeforeEach;",
            "import org.junit.jupiter.api.AfterEach;",
            "import org.junit.jupiter.api.DisplayName;",
            "import org.junit.jupiter.params.ParameterizedTest;",
            "import org.junit.jupiter.params.provider.ValueSource;",
            "import org.junit.jupiter.params.provider.Arguments;",
            "import org.junit.jupiter.params.provider.MethodSource;",
            "import static org.junit.jupiter.api.Assertions.*;",
            "import java.util.stream.Stream;"
        ]
        
        # 根据测试风格添加特定导入
        if test_style == "performance":
            imports.extend([
                "import org.junit.jupiter.api.Timeout;",
                "import java.util.concurrent.TimeUnit;"
            ])
        
        # 生成测试类
        test_class = f"""package {package_name};

{chr(10).join(imports)}

@DisplayName("{class_name} Tests")
class {test_class_name} {{
    
    private {class_name} {self._get_instance_name(class_name)};
    
    @BeforeEach
    void setUp() {{
        {self._get_instance_name(class_name)} = new {class_name}();
    }}
    
    @AfterEach
    void tearDown() {{
        {self._get_instance_name(class_name)} = null;
    }}
    
    {self._generate_test_methods(class_name, method_name, test_style)}
    
    {self._generate_utility_methods(test_style)}
}}
"""
        
        return test_class
    
    def _get_instance_name(self, class_name: str) -> str:
        """获取实例变量名"""
        return class_name[0].lower() + class_name[1:]
    
    def _generate_test_methods(
        self,
        class_name: str,
        method_name: str,
        test_style: str
    ) -> str:
        """生成测试方法"""
        instance_name = self._get_instance_name(class_name)
        
        if test_style == "comprehensive":
            return self._generate_comprehensive_tests(instance_name, method_name)
        elif test_style == "minimal":
            return self._generate_minimal_tests(instance_name, method_name)
        elif test_style == "bdd":
            return self._generate_bdd_tests(instance_name, method_name)
        elif test_style == "performance":
            return self._generate_performance_tests(instance_name, method_name)
        elif test_style == "security":
            return self._generate_security_tests(instance_name, method_name)
        else:
            return self._generate_comprehensive_tests(instance_name, method_name)
    
    def _generate_comprehensive_tests(self, instance_name: str, method_name: str) -> str:
        """生成全面的测试"""
        return f"""
    @Test
    @DisplayName("Should handle normal case")
    void test{method_name.capitalize()}_NormalCase() {{
        // TODO: Implement test for normal case
        assertTrue(true, "Test not implemented yet");
    }}
    
    @Test
    @DisplayName("Should handle edge case")
    void test{method_name.capitalize()}_EdgeCase() {{
        // TODO: Implement test for edge case
        assertTrue(true, "Test not implemented yet");
    }}
    
    @Test
    @DisplayName("Should handle error case")
    void test{method_name.capitalize()}_ErrorCase() {{
        // TODO: Implement test for error case
        assertTrue(true, "Test not implemented yet");
    }}
    
    @ParameterizedTest
    @ValueSource(strings = {{"test1", "test2", "test3"}})
    @DisplayName("Should handle multiple inputs")
    void test{method_name.capitalize()}_MultipleInputs(String input) {{
        // TODO: Implement parameterized test
        assertTrue(true, "Test not implemented yet");
    }}
"""
    
    def _generate_minimal_tests(self, instance_name: str, method_name: str) -> str:
        """生成最小化测试"""
        return f"""
    @Test
    @DisplayName("Basic functionality test")
    void test{method_name.capitalize()}_Basic() {{
        // TODO: Implement basic test
        assertTrue(true, "Test not implemented yet");
    }}
"""
    
    def _generate_bdd_tests(self, instance_name: str, method_name: str) -> str:
        """生成BDD风格测试"""
        return f"""
    @Test
    @DisplayName("Given valid input, when {method_name} is called, then it should succeed")
    void givenValidInput_when{method_name.capitalize()}_thenShouldSucceed() {{
        // Given
        // TODO: Set up test data
        
        // When
        // TODO: Call the method
        
        // Then
        // TODO: Verify result
        assertTrue(true, "Test not implemented yet");
    }}
"""
    
    def _generate_performance_tests(self, instance_name: str, method_name: str) -> str:
        """生成性能测试"""
        return f"""
    @Test
    @Timeout(value = 1, unit = TimeUnit.SECONDS)
    @DisplayName("Should complete within reasonable time")
    void test{method_name.capitalize()}_Performance() {{
        // TODO: Implement performance test
        assertTrue(true, "Test not implemented yet");
    }}
"""
    
    def _generate_security_tests(self, instance_name: str, method_name: str) -> str:
        """生成安全测试"""
        return f"""
    @Test
    @DisplayName("Should handle malicious input safely")
    void test{method_name.capitalize()}_Security() {{
        // TODO: Implement security test
        assertTrue(true, "Test not implemented yet");
    }}
"""
    
    def _generate_utility_methods(self, test_style: str) -> str:
        """生成工具方法"""
        if test_style == "comprehensive":
            return """
    /**
     * Helper method to create test data
     */
    private Object createTestData() {{
        // TODO: Implement test data creation
        return null;
    }}
    
    /**
     * Helper method to verify test results
     */
    private void verifyResult(Object actual, Object expected) {{
        // TODO: Implement result verification
        assertEquals(expected, actual);
    }}
"""
        else:
            return "" 