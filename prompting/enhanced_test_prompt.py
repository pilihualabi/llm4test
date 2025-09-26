"""
增强的测试生成提示模板
确保生成纯Java测试代码，不包含思考过程
"""

from typing import Dict, List, Any

class EnhancedTestPrompt:
    """增强的测试生成提示模板"""
    
    @staticmethod
    def create_method_test_prompt(class_info: Dict[str, Any], method_info: Dict[str, Any],
                                context_info: List[Dict] = None, test_style: str = "comprehensive") -> str:
        """
        创建方法测试提示

        Args:
            class_info: 类信息
            method_info: 方法信息 (包含完整的方法体)
            context_info: 相关上下文信息
            test_style: 测试风格

        Returns:
            格式化的提示字符串
        """

        # 先格式化上下文
        context_text = EnhancedTestPrompt._format_context(context_info) if context_info else ""

        # 格式化方法实现
        method_implementation = method_info.get('method_body', 'Implementation not available')

        # 基础提示结构
        prompt = f"""Generate a complete JUnit 5 test class for the Java method below.

CRITICAL INSTRUCTION:
- Generate ONLY pure Java test code
- Do NOT include any explanations, comments, or thinking process
- Do NOT use <think> tags or any XML tags
- Do NOT add any text before or after the Java code
- Start directly with "package" declaration
- End with the closing brace of the test class

Target Class: {class_info['name']}
Package: {class_info.get('package', 'com.example')}
Target Method: {method_info.get('name', 'unknownMethod')}

Requirements:
1. Use JUnit 5 annotations (@Test, @BeforeEach, @AfterEach)
2. Include comprehensive test cases covering normal, edge, and error conditions
3. Use descriptive test method names following the pattern: testMethodName_scenario_expectedResult
4. Include proper assertions with meaningful messages
5. Handle exceptions appropriately using assertThrows
6. Follow Java naming conventions
7. Add necessary imports
8. Do NOT use @ParameterizedTest or @ValueSource - create separate @Test methods instead
9. Analyze the method implementation to understand its behavior and create appropriate tests

TESTING STRATEGY GUIDELINES:
- For classes with dependencies: Mock the dependencies and verify their method calls when needed
- For methods that call other objects: Mock the called objects appropriately
- Always verify the ACTUAL method calls made by the implementation, not assumed calls
- Use appropriate test setup based on the class structure shown in the context information

Test Style: {test_style.upper()}

{context_text}

Generate the complete test class starting with package declaration and imports:"""

        return prompt
    
    @staticmethod
    def create_compile_fix_prompt(method_info: Dict[str, Any], context_info: List[Dict],
                                generated_test: str, compile_error: str) -> str:
        """
        创建编译修复提示 - 专门针对编译阶段的错误

        Args:
            method_info: 方法信息（包含完整方法体）
            context_info: 相关上下文信息
            generated_test: 生成的测试代码
            compile_error: 编译错误信息
        """

        # 格式化上下文
        context_text = EnhancedTestPrompt._format_context(context_info) if context_info else ""

        # 格式化方法实现
        method_implementation = method_info.get('method_body', 'Implementation not available')

        # 分析编译错误类型
        error_analysis = EnhancedTestPrompt._analyze_compile_errors(compile_error)

        prompt = f""" COMPILATION ERROR FIXING TASK

You are a Java compilation expert. The following JUnit 5 test code has compilation errors that prevent it from being compiled into bytecode.

=== TARGET METHOD IMPLEMENTATION ===
```java
{method_implementation}
```

=== CONTEXT INFORMATION ===
{context_text}

=== FAILING TEST CODE ===
```java
{generated_test}
```

=== COMPILATION ERRORS ===
```
{compile_error}
```

=== ERROR ANALYSIS ===
{error_analysis}

=== COMPILATION FIX REQUIREMENTS ===
1.  PRIMARY GOAL: Make the code compile successfully (javac/mvn compile)
2.  Fix import statements - ensure all classes are properly imported
3.  Fix syntax errors - correct Java language syntax issues
4.   Fix type errors - ensure type compatibility and casting
5.  Fix method signatures - match actual method names and parameters
6.  Fix dependency issues - ensure all required libraries are available
7.  Keep test logic structure intact - don't change the test intent
8.  Use JUnit 5 annotations and assertions correctly
9.  Do NOT worry about test logic correctness - focus only on compilation
10.  Return ONLY the corrected Java code without explanations

 CRITICAL OUTPUT INSTRUCTION:
- Generate ONLY pure Java test code
- Do NOT include any explanations, comments, or thinking process
- Do NOT use <think> tags or any XML tags
- Do NOT add any text before or after the Java code
- Start directly with "package" declaration
- End with the closing brace of the test class

=== COMMON COMPILATION FIXES ===
- Missing imports: Add proper import statements
- Wrong class names: Use correct class names from the target method
- Type mismatches: Add explicit casting or use correct types
- Method not found: Use correct method names and signatures
- Package issues: Ensure correct package declarations
- Annotation errors: Use proper JUnit 5 annotations
- Syntax errors: Check for incomplete statements, missing parentheses, or truncated code
- Field dependency issues: Ensure mock objects are properly configured for dependencies

=== SPECIFIC FIXES FOR PDF COMPARISON TESTS ===
- PageComparator should be PDFPageComparator
- Add missing I/O imports: InputStream, OutputStream, ByteArrayInputStream, ByteArrayOutputStream, IOException
- Add missing PDF imports: DocumentException, Document, PdfReader, PdfWriter, PdfImportedPage
- Use correct method signatures for comparePage method
- Ensure proper exception handling for IOException and DocumentException

Fixed Test Code:"""

        return prompt
    
    @staticmethod
    def create_runtime_fix_prompt(method_info: Dict[str, Any], context_info: List[Dict],
                                generated_test: str, runtime_error: str) -> str:
        """
        创建运行时修复提示 - 专门针对运行时阶段的错误

        Args:
            method_info: 方法信息
            context_info: 相关上下文信息
            generated_test: 生成的测试代码
            runtime_error: 运行时错误信息
        """

        # 格式化上下文
        context_text = EnhancedTestPrompt._format_context(context_info) if context_info else ""

        # 格式化方法实现
        method_implementation = method_info.get('method_body', 'Implementation not available')

        # 分析运行时错误类型
        error_analysis = EnhancedTestPrompt._analyze_runtime_errors(runtime_error)

        prompt = f""" RUNTIME ERROR FIXING TASK

You are a Java testing expert. The following JUnit 5 test code compiles successfully but fails during execution with runtime errors.

=== TARGET METHOD IMPLEMENTATION ===
```java
{method_implementation}
```

=== CONTEXT INFORMATION ===
{context_text}

=== FAILING TEST CODE (Compiles but fails at runtime) ===
```java
{generated_test}
```

=== RUNTIME ERRORS ===
```
{runtime_error}
```

=== ERROR ANALYSIS ===
{error_analysis}

=== RUNTIME FIX REQUIREMENTS ===
1.  PRIMARY GOAL: Make the test pass during execution (mvn test)
2.  Fix test logic errors - ensure assertions match expected behavior
3.  Fix mock configurations - properly setup mock objects and behaviors
4.  Fix setup/teardown issues - ensure proper test environment initialization
5.  Handle exceptions properly - use assertThrows for expected exceptions
6.  Fix assertion values - ensure expected vs actual values are correct
7.  Fix dependency injection - ensure all required dependencies are available
8.  Handle edge cases - null values, empty collections, boundary conditions
9.  Maintain test intent - keep the original testing purpose
10. Return ONLY the corrected Java code without explanations

CRITICAL OUTPUT INSTRUCTION:
- Generate ONLY pure Java test code
- Do NOT include any explanations, comments, or thinking process
- Do NOT use <think> tags or any XML tags
- Do NOT add any text before or after the Java code
- Start directly with "package" declaration
- End with the closing brace of the test class

=== COMMON RUNTIME FIXES ===
- NullPointerException: Initialize objects, setup mocks properly
- AssertionFailedError: Adjust expected values, fix test logic
- IllegalArgumentException: Validate input parameters, handle edge cases
- Mock setup issues: Configure when().thenReturn() properly
- Resource not found: Setup test resources, mock external dependencies
- Timeout issues: Optimize test execution, mock slow operations

=== TESTING BEST PRACTICES ===
- Use descriptive assertion messages
- Setup mocks before using them
- Clean up resources in @AfterEach
- Test one thing at a time
- Use appropriate assertion methods (assertEquals, assertTrue, etc.)

Fixed Test Code:"""

        return prompt

    @staticmethod
    def _analyze_compile_errors(compile_error: str) -> str:
        """分析编译错误并提供针对性建议"""
        if not compile_error:
            return "No specific error analysis available."

        error_lower = compile_error.lower()
        analysis = []

        # 检查常见编译错误类型
        if "cannot find symbol" in error_lower:
            analysis.append(" SYMBOL NOT FOUND: Missing imports or incorrect class/method names")

        if "package does not exist" in error_lower:
            analysis.append(" PACKAGE ERROR: Incorrect package imports or missing dependencies")

        if "incompatible types" in error_lower:
            analysis.append(" TYPE MISMATCH: Type casting or generic type issues")

        if "method not found" in error_lower or "cannot resolve method" in error_lower:
            analysis.append(" METHOD ERROR: Incorrect method names or signatures")

        if "duplicate" in error_lower:
            analysis.append(" DUPLICATE ERROR: Duplicate imports, methods, or variables")

        if "syntax error" in error_lower or "expected" in error_lower:
            analysis.append(" SYNTAX ERROR: Missing semicolons, brackets, or incorrect Java syntax")

        if not analysis:
            analysis.append(" GENERAL COMPILATION ERROR: Review the error message for specific issues")

        return "\n".join(analysis)

    @staticmethod
    def _analyze_runtime_errors(runtime_error: str) -> str:
        """分析运行时错误并提供针对性建议"""
        if not runtime_error:
            return "No specific error analysis available."

        error_lower = runtime_error.lower()
        analysis = []

        # 检查常见运行时错误类型
        if "nullpointerexception" in error_lower:
            analysis.append(" NULL POINTER: Objects not initialized or mock setup missing")

        if "assertionfailederror" in error_lower or "expected" in error_lower and "actual" in error_lower:
            analysis.append(" ASSERTION FAILED: Expected vs actual values don't match")

        if "illegalargumentexception" in error_lower:
            analysis.append(" ILLEGAL ARGUMENT: Invalid parameters passed to methods")

        if "classcastexception" in error_lower:
            analysis.append(" CLASS CAST: Incorrect type casting in test code")

        if "mockito" in error_lower or "mock" in error_lower:
            analysis.append("  MOCK ERROR: Mockito configuration or usage issues")

        if "timeout" in error_lower:
            analysis.append(" TIMEOUT: Test execution taking too long")

        if "filenotfound" in error_lower or "resource" in error_lower:
            analysis.append(" RESOURCE ERROR: Missing test resources or files")

        if "security" in error_lower or "access" in error_lower:
            analysis.append(" ACCESS ERROR: Security or permission issues")

        if not analysis:
            analysis.append(" GENERAL RUNTIME ERROR: Review the stack trace for specific issues")

        return "\n".join(analysis)

    @staticmethod
    def _format_context(context_info):
        """格式化上下文信息，包含导入提示（支持RAG和Context-Aware格式）"""
        if not context_info:
            return ""

        # 检测上下文类型（RAG或Context-Aware）
        first_ctx = context_info[0] if context_info else {}
        is_context_aware = first_ctx.get('metadata', {}).get('type') in ['core_context', 'imports', 'dependency_context']

        if is_context_aware:
            return EnhancedTestPrompt._format_context_aware_context(context_info)
        else:
            return EnhancedTestPrompt._format_rag_context(context_info)

    @staticmethod
    def _format_context_aware_context(context_info):
        """格式化Context-Aware上下文信息，专注于构造函数、依赖和类结构信息"""
        formatted = []

        for i, ctx in enumerate(context_info, 1):
            metadata = ctx.get('metadata', {})
            content = ctx.get('content', '')
            ctx_type = metadata.get('type', 'unknown')

            if ctx_type == 'core_context':
                class_name = metadata.get('class_name', 'Unknown').split('.')[-1]
                method_name = metadata.get('method_name', 'Unknown')
                formatted.append(f"{i}. {class_name}.{method_name}:")
                formatted.append(f"   Method: {metadata.get('method_signature', 'Unknown signature')}")
                formatted.append(f"   Implementation:")
                formatted.append(f"   {content}")

            elif ctx_type == 'class_info':
                # 保留类的基本信息和字段信息
                formatted.append(f"{i}. Class Information:")
                formatted.append(f"   {content}")

            elif ctx_type == 'dependency_context':
                # 保留依赖上下文，这对构造函数和Mock很重要
                formatted.append(f"{i}. Dependencies:")
                formatted.append(f"   {content}")

            elif ctx_type == 'imports':
                formatted.append(f"{i}. Required Imports:")
                formatted.append(f"   {content}")

        return "\n".join(formatted)

    @staticmethod
    def _format_rag_context(context_info):
        """格式化RAG上下文信息"""
        formatted = []
        import_hints = {}  # {class_name: package}
        constructor_hints = []  # 构造函数提示
        dependency_hints = []  # 依赖注入提示
        external_library_hints = []  # 外部库提示

        for i, ctx in enumerate(context_info[:5], 1):  # 增加到5个最相关的
            metadata = ctx.get('metadata', {})
            code_snippet = ctx.get('content', ctx.get('code', ''))  # 兼容两种键名

            # 收集类和包信息用于导入提示
            class_name = metadata.get('class_name')
            package = metadata.get('package')
            if class_name and package:
                import_hints[class_name] = package

            #  新增：分析构造函数和依赖信息
            EnhancedTestPrompt._analyze_class_info(code_snippet, class_name, constructor_hints, dependency_hints)

            #  新增：分析外部库信息
            if metadata.get('type') == 'external_library':
                external_library_hints.append(f"External library: {class_name} - {code_snippet}")

            # 对于类定义，显示更多信息
            if metadata.get('type') == 'class':
                # 显示完整的类定义（record类通常很短）
                formatted.append(f"{i}. {metadata.get('class_name', 'Unknown')} (Class):")
                formatted.append(f"   Package: {metadata.get('package', 'Unknown')}")
                if len(code_snippet) <= 500:  # 短类显示完整内容
                    formatted.append(f"   {code_snippet}")
                else:
                    formatted.append(f"   {code_snippet[:300]}...")
            else:
                # 方法显示签名和部分实现
                method_name = metadata.get('method_name', 'Unknown')
                class_name = metadata.get('class_name', 'Unknown')
                formatted.append(f"{i}. {class_name}.{method_name}:")

                # 提取方法签名
                lines = code_snippet.split('\n')
                signature_lines = []
                for line in lines[:3]:  # 前3行通常包含签名
                    if line.strip():
                        signature_lines.append(line.strip())

                if signature_lines:
                    formatted.append(f"   Method: {' '.join(signature_lines)}")

                # 显示实现预览
                if len(code_snippet) <= 400:
                    formatted.append(f"   Implementation: {code_snippet}")
                else:
                    formatted.append(f"   Implementation: {code_snippet[:200]}...")

        #  新增：生成导入提示
        if import_hints:
            formatted.append("\n=== CRITICAL IMPORT INFORMATION ===")
            formatted.append("  ATTENTION: Use the EXACT package paths shown below for imports!")
            for class_name, package in import_hints.items():
                formatted.append(f"- {class_name}: import {package}.{class_name};")
            formatted.append(" DO NOT assume classes are in the same package as the target class!")
            formatted.append(" Always use the package information provided above!")
            formatted.append(" EXTERNAL LIBRARIES:")
            formatted.append("- PdfContentByte: import com.itextpdf.text.pdf.PdfContentByte;")
            formatted.append("- BaseColor: import com.itextpdf.text.BaseColor;")
            formatted.append("- Rectangle: import java.awt.Rectangle;")

        #  构造函数和依赖信息
        if constructor_hints:
            formatted.append("\n=== CONSTRUCTOR INFORMATION ===")
            for hint in set(constructor_hints):  # 去重
                formatted.append(f"  {hint}")

        #  依赖对象信息
        if dependency_hints:
            formatted.append("\n=== DEPENDENCY INFORMATION ===")
            for hint in set(dependency_hints):  # 去重
                formatted.append(f"  {hint}")

        #  外部库信息
        if external_library_hints:
            formatted.append("\n=== EXTERNAL LIBRARY INFORMATION ===")
            for hint in set(external_library_hints):  # 去重
                formatted.append(f"  {hint}")

        return "\n".join(formatted)

    @staticmethod
    def _analyze_class_info(code_snippet: str, class_name: str, constructor_hints: list, dependency_hints: list):
        """
        分析类信息，提取构造函数和依赖提示

        Args:
            code_snippet: 代码片段
            class_name: 类名
            constructor_hints: 构造函数提示列表
            dependency_hints: 依赖提示列表
        """
        if not code_snippet or not class_name:
            return

        try:
            import re

            # 检查record类
            if re.search(r'\brecord\s+' + re.escape(class_name), code_snippet):
                # 提取record构造函数参数
                record_match = re.search(rf'record\s+{re.escape(class_name)}\s*\(([^)]*)\)', code_snippet)
                if record_match:
                    params = record_match.group(1).strip()
                    if params:
                        param_count = len([p for p in params.split(',') if p.strip()])
                        constructor_hints.append(f"{class_name} is a record class with {param_count} parameters: {params}")
                    else:
                        constructor_hints.append(f"{class_name} is a record class with no parameters")

            # 检查构造函数
            constructor_patterns = [
                r'public\s+' + re.escape(class_name) + r'\s*\(([^)]*)\)',
                r'private\s+final\s+(\w+)\s+(\w+)'  # final字段通常需要构造函数参数
            ]

            # 查找显式构造函数
            constructor_match = re.search(constructor_patterns[0], code_snippet)
            if constructor_match:
                params = constructor_match.group(1).strip()
                if params:
                    constructor_hints.append(f"{class_name} has constructor with parameters: {params}")
                else:
                    constructor_hints.append(f"{class_name} has default constructor")

            # 查找final字段（通常需要构造函数参数）
            final_fields = re.findall(constructor_patterns[1], code_snippet)
            if final_fields:
                field_info = ', '.join([f"{ftype} {fname}" for ftype, fname in final_fields])
                constructor_hints.append(f"{class_name} has final fields: {field_info}")
                dependency_hints.append(f"{class_name} requires constructor parameters for final fields")

            # 查找私有字段（可能需要Mock）
            private_fields = re.findall(r'private\s+(\w+)\s+(\w+)', code_snippet)
            if private_fields:
                field_info = ', '.join([f"{ftype} {fname}" for ftype, fname in private_fields])
                dependency_hints.append(f"{class_name} has private fields: {field_info} - consider mocking if they are dependencies")

            # 检查方法调用模式，推断可能的依赖
            method_calls = re.findall(r'(\w+)\.(\w+)\s*\(', code_snippet)
            potential_dependencies = set()
            for obj, _ in method_calls:  # 忽略method参数
                if obj[0].islower() and obj not in ['this', 'super', 'System', 'Math']:
                    potential_dependencies.add(obj)

            if potential_dependencies:
                deps = ', '.join(potential_dependencies)
                dependency_hints.append(f"{class_name} calls methods on objects: {deps} - these may be dependencies that need mocking")

        except Exception:
            # 静默处理错误，不影响主流程
            pass

    @staticmethod
    def create_custom_prompt(template, **kwargs):
        """
        创建自定义提示
        
        Args:
            template: 提示模板字符串
            **kwargs: 模板变量
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板中缺少必要的变量: {e}")
    
    @staticmethod
    def get_default_templates():
        """获取默认提示模板"""
        return {
            "comprehensive": """Generate comprehensive JUnit 5 tests covering:
- Normal cases with various inputs (2-3 test methods)
- Edge cases (null, empty, boundary values) (1-2 test methods)
- Error conditions and exceptions (1-2 test methods)
- Proper setup and teardown
LIMIT: Generate maximum 8-10 test methods total to ensure code quality and maintainability""",
            
            "minimal": """Generate minimal JUnit 5 tests covering:
- Basic functionality
- Essential error cases
- Simple assertions""",
            
            "bdd": """Generate BDD-style JUnit 5 tests using:
- Given/When/Then structure in comments
- Descriptive test method names
- Behavior-focused test cases
- Clear scenario descriptions""",
            
            "performance": """Generate performance-focused JUnit 5 tests including:
- Timing assertions
- Memory usage checks
- Load testing scenarios
- Performance benchmarks""",
            
            "security": """Generate security-focused JUnit 5 tests covering:
- Input validation
- Authentication scenarios
- Authorization checks
- Security edge cases"""
        }
