# 快速开始指南

## 5分钟快速上手

### 1. 环境检查

确保你的系统满足以下要求：

```bash
# 检查Python版本
python --version  # 需要 3.8+

# 检查Java版本
java -version     # 需要 8+

# 检查Maven版本
mvn --version     # 需要 3.6+
```

### 2. 安装依赖

```bash
# 进入项目目录
cd llm4testgen

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 启动Ollama服务

```bash
# 启动Ollama服务
ollama serve

# 在新终端中拉取模型
ollama pull qwen2.5-coder:7b
ollama pull qwen3-embedding:latest

# 验证模型安装
ollama list
```

### 4. 第一次测试生成

```bash
# Context-Aware模式（推荐，极速生成）
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode context-aware \
    --debug
```

### 5. 查看结果

生成完成后，你会看到类似的输出：

```
✅ 状态: 成功
⏱️  总耗时: 0.34 秒
🧠 生成模式: context-aware
📄 测试文件: Calculator_add_Test.java
📄 测试文件已保存到: ./generated_tests
```

生成的测试文件包含：
- 完整的JUnit 5测试框架
- 自动导入的依赖
- 多种测试场景
- Mock对象配置（如需要）

## 常用命令示例

### 不同生成模式

```bash
# Context-Aware模式（极速）
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode context-aware

# 混合模式（推荐）
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode hybrid

# RAG模式（深度理解）
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode rag
```

### 使用不同修复策略

```bash
# 只修复编译错误
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Calculator \
    --method divide \
    --fix-strategy compile-only

# 只修复运行时错误
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Calculator \
    --method divide \
    --fix-strategy runtime-only

# 修复所有错误（默认）
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Calculator \
    --method divide \
    --fix-strategy both
```

### 调整生成参数

```bash
# 增加修复尝试次数
python main_test_generator.py \
    -p ../my-project \
    --class com.example.ComplexService \
    --method processData \
    --max-attempts 5

# 使用不同测试风格
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Utils \
    --method simpleMethod \
    --style minimal

# 禁用RAG检索（更快但质量可能较低）
python main_test_generator.py \
    -p ../my-project \
    --class com.example.Calculator \
    --method add \
    --no-rag
```

## 编程接口快速使用

### 单个测试生成

```python
from improved_test_generator import ImprovedTestGenerator
from pathlib import Path

# 初始化生成器
generator = ImprovedTestGenerator(
    project_path=Path("../your-java-project"),
    output_dir=Path("./generated_tests"),
    debug=True
)

# 生成测试
result = generator.generate_test_for_method(
    class_name="com.example.Calculator",
    method_name="add",
    use_rag=True,
    test_style="comprehensive",
    max_fix_attempts=3,
    fix_strategy="both"
)

# 检查结果
if result['success']:
    print(f"✅ 成功: {result.get('test_file_path', 'N/A')}")
else:
    print(f"❌ 失败: {result['error']}")
```

### 批量生成

```python
# 定义要生成测试的方法列表
test_cases = [
    ("com.example.Calculator", "add"),
    ("com.example.Calculator", "subtract"),
    ("com.example.Calculator", "multiply"),
    ("com.example.Calculator", "divide"),
]

# 批量生成
success_count = 0
for class_name, method_name in test_cases:
    print(f"🎯 生成 {class_name}#{method_name}")
    
    result = generator.generate_test_for_method(
        class_name=class_name,
        method_name=method_name,
        use_rag=True,
        test_style="comprehensive",
        fix_strategy="both"
    )
    
    if result['success']:
        print(f"   ✅ 成功")
        success_count += 1
    else:
        print(f"   ❌ 失败: {result['error']}")

print(f"\n📊 总结: {success_count}/{len(test_cases)} 成功")
```

## 常见问题快速解决

### 问题1: "找不到符号"编译错误

**现象**: 生成的测试代码编译失败，提示找不到某个类或方法

**解决方案**:
```bash
# 1. 检查项目是否能正常编译
cd your-java-project
mvn clean compile

# 2. 增加修复尝试次数
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.YourClass \
    --method yourMethod \
    --max-attempts 5
```

### 问题2: Ollama连接失败

**现象**: 提示连接错误或模型不可用

**解决方案**:
```bash
# 1. 检查Ollama服务状态
ollama ps

# 2. 重启Ollama服务
ollama serve

# 3. 验证模型是否存在
ollama list
ollama pull qwen2.5-coder:7b
```

### 问题3: 生成速度慢

**现象**: 测试生成耗时很长

**解决方案**:
```bash
# 1. 禁用RAG检索
python main_test_generator.py \
    --project ../your-project \
    --class com.example.Calculator \
    --method add \
    --no-rag

# 2. 使用更简单的测试风格
python main_test_generator.py \
    --project ../your-project \
    --class com.example.Calculator \
    --method add \
    --style minimal

# 3. 减少修复尝试次数
python main_test_generator.py \
    --project ../your-project \
    --class com.example.Calculator \
    --method add \
    --max-attempts 1
```

### 问题4: 生成的测试质量不高

**现象**: 生成的测试代码不够完善或有逻辑错误

**解决方案**:
```bash
# 1. 启用RAG检索（如果之前禁用了）
python main_test_generator.py \
    --project ../your-project \
    --class com.example.Calculator \
    --method add \
    --rag

# 2. 使用更全面的测试风格
python main_test_generator.py \
    --project ../your-project \
    --class com.example.Calculator \
    --method add \
    --style comprehensive

# 3. 增加修复尝试次数
python main_test_generator.py \
    --project ../your-project \
    --class com.example.Calculator \
    --method add \
    --max-attempts 5
```

## 下一步

现在你已经成功生成了第一个测试，可以：

1. **阅读完整文档**: 查看 [用户手册](USER_MANUAL.md) 了解更多高级功能
2. **查看API文档**: 阅读 [API文档](API.md) 了解编程接口
3. **探索示例**: 查看 `tests/examples/` 目录中的示例代码
4. **自定义配置**: 根据项目需求调整生成参数

## 获取帮助

如果遇到问题：

1. **查看调试信息**: 使用 `--debug` 参数查看详细过程
2. **检查对话记录**: 查看输出目录中的 `conversations/` 文件夹
3. **阅读故障排除**: 查看 [用户手册](USER_MANUAL.md#故障排除) 中的故障排除部分
4. **提交Issue**: 在GitHub上提交问题报告
