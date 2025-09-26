#!/usr/bin/env python3
"""
演示不同修复策略的区别和特点
"""

import sys
from pathlib import Path

def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title, content):
    """打印章节"""
    print(f"\n {title}")
    print("-" * 40)
    print(content)

def main():
    """主演示函数"""
    print(" LLM4TestGen 修复策略演示")
    print("本演示将展示编译修复和运行时修复的区别")
    
    # 1. 编译修复策略演示
    print_header("编译修复策略 (compile-only)")
    
    print_section("目标", """
     只关注编译阶段的错误修复
     确保生成的测试代码能够成功编译为字节码
    ⚡ 快速生成可编译的测试框架
    """)
    
    print_section("检查内容", """
    • 语法错误 (syntax errors)
    • 类型错误 (type errors)  
    • 导入语句错误 (import errors)
    • 方法签名不匹配 (method signature mismatch)
    • 依赖缺失 (missing dependencies)
    """)
    
    print_section("常见错误示例", """
     cannot find symbol: class ImageComparator
     package com.example.util does not exist
     incompatible types: String cannot be converted to int
     method compareImages(PdfContentByte,List,List,float,boolean) not found
    """)
    
    print_section("修复策略", """
     添加正确的import语句
     修正类名和包名
     调整方法参数类型
     添加类型转换
     修复语法结构
    """)
    
    print_section("使用命令", """
    python main_test_generator.py \\
      --project ../pdfcompare \\
      --class com.example.pdfcompare.util.ImageComparator \\
      --method compareImages \\
      --fix-strategy compile-only \\
      --max-attempts 3
    """)
    
    # 2. 运行时修复策略演示
    print_header("运行时修复策略 (runtime-only)")
    
    print_section("目标", """
     关注测试执行阶段的错误修复
     确保测试逻辑正确且能够通过
    🎭 修复Mock配置和断言问题
    """)
    
    print_section("检查内容", """
    • 逻辑错误 (logic errors)
    • 运行时异常 (runtime exceptions)
    • 测试断言失败 (assertion failures)
    • Mock对象配置错误 (mock setup issues)
    • 资源访问问题 (resource access issues)
    """)
    
    print_section("常见错误示例", """
     java.lang.NullPointerException
     AssertionFailedError: expected: <true> but was: <false>
     IllegalArgumentException: Parameter cannot be null
     Test failed: Mock setup incomplete
    """)
    
    print_section("修复策略", """
     初始化Mock对象
     调整断言的期望值
     处理空指针异常
     配置when().thenReturn()
     添加异常处理逻辑
    """)
    
    print_section("使用命令", """
    python main_test_generator.py \\
      --project ../pdfcompare \\
      --class com.example.pdfcompare.util.ImageComparator \\
      --method compareImages \\
      --fix-strategy runtime-only \\
      --max-attempts 3
    """)
    
    # 3. 完整修复策略演示
    print_header("完整修复策略 (both)")
    
    print_section("目标", """
     提供完整的测试生成体验
     先修复编译问题，再修复运行时问题
     生成既能编译又能正确运行的测试
    """)
    
    print_section("执行流程", """
    1⃣ 阶段1: 编译修复
       • 修复语法、类型、导入等问题
       • 确保代码能够编译成功
    
    2⃣ 阶段2: 运行时修复  
       • 修复测试逻辑和断言问题
       • 确保测试能够正确执行
    """)
    
    print_section("使用命令", """
    python main_test_generator.py \\
      --project ../pdfcompare \\
      --class com.example.pdfcompare.util.ImageComparator \\
      --method compareImages \\
      --fix-strategy both \\
      --max-attempts 4
    """)
    
    # 4. 对比总结
    print_header("策略对比总结")
    
    print("""
    ┌─────────────────┬──────────────────┬──────────────────┬──────────────────┐
    │     特性        │   compile-only   │   runtime-only   │      both        │
    ├─────────────────┼──────────────────┼──────────────────┼──────────────────┤
    │ 编译检查        │                │                │                │
    │ 运行时检查      │                │                │                │
    │ 执行速度        │       快速       │       中等       │       较慢       │
    │ 测试完整性      │       基础       │       中等       │       完整       │
    │ 适用场景        │   快速原型开发   │   修复现有测试   │   完整测试生成   │
    └─────────────────┴──────────────────┴──────────────────┴──────────────────┘
    """)
    
    # 5. 实际运行建议
    print_header("实际使用建议")
    
    print_section("场景选择", """
     快速开发阶段: 使用 compile-only
       • 需要快速生成测试框架
       • 暂时不关心测试逻辑正确性
    
     测试修复阶段: 使用 runtime-only  
       • 测试已经能编译但运行失败
       • 需要修复具体的测试逻辑问题
    
    ✨ 完整开发阶段: 使用 both
       • 从零开始生成完整可用的测试
       • 需要高质量的测试代码
    """)
    
    print_section("性能优化建议", """
    • 根据项目复杂度调整 --max-attempts 参数
    • 使用 --debug 模式查看详细修复过程
    • 启用 --rag 获得更好的上下文信息
    • 使用 --quiet 模式减少输出信息
    """)
    
    print("\n 演示完成！现在你可以根据需要选择合适的修复策略了。")
    print(" 建议先尝试 compile-only 策略，然后根据需要升级到 both 策略。")

if __name__ == "__main__":
    main()
