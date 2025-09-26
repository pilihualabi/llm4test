# LLM4TestGen 用户指南

## 📋 目录

1. [快速开始](#快速开始)
2. [生成模式选择](#生成模式选择)
3. [命令行使用](#命令行使用)
4. [编程接口](#编程接口)
5. [修复策略](#修复策略)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)

## 🚀 快速开始

### 环境准备

1. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动Ollama服务**
   ```bash
   ollama serve
   ollama pull qwen2.5-coder:7b
   ollama pull qwen3-embedding:latest
   ```

3. **验证安装**
   ```bash
   python -c "from improved_test_generator import ImprovedTestGenerator; print('✅ 安装成功')"
   ```

### 第一个测试生成

```bash
# 使用Context-Aware模式（推荐）
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode context-aware \
    --debug
```

## 🧠 生成模式选择

### Context-Aware模式（推荐）
- ⚡ **极速生成**: 0.1-0.5秒完成测试生成
- 🎯 **100%准确**: 包路径和依赖关系完全正确
- 🔍 **智能分析**: 自动识别依赖并生成Mock
- 📦 **项目级索引**: 基于静态分析的完整项目理解

**适用场景**：
- 标准Java项目结构
- 需要快速生成测试框架
- 批量测试生成
- CI/CD集成

### 混合模式（最高成功率）
- 🏆 **最高成功率**: 结合两种模式的优势
- 🔄 **智能回退**: Context-Aware失败时自动使用RAG
- 🛡️ **生产就绪**: 适合生产环境使用
- 🎯 **最佳选择**: 适用于所有项目类型

**适用场景**：
- 生产环境使用
- 复杂或非标准项目
- 需要最高成功率
- 所有项目类型

### RAG模式（深度理解）
- 🔍 **深度上下文**: 基于向量检索的上下文理解
- 📚 **语义理解**: 理解复杂的业务逻辑
- 🎯 **精准生成**: 适合复杂业务场景

**适用场景**：
- 需要深度上下文理解
- 复杂业务逻辑
- 特殊项目结构

## 💻 命令行使用

### 基本语法

```bash
python main_test_generator.py [OPTIONS]
```

### 必需参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--project` | `-p` | Java项目路径 | `../pdfcompare` |
| `--class` | `-c` | 目标类的完全限定名 | `com.example.Calculator` |
| `--method` | `-m` | 目标方法名 | `add` |

### 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--generation-mode` | `hybrid` | 生成模式 (context-aware/hybrid/rag) |
| `--output` | `./generated_tests` | 测试输出目录 |
| `--style` | `comprehensive` | 测试风格 |
| `--max-attempts` | `3` | 最大修复尝试次数 |
| `--fix-strategy` | `both` | 修复策略 |
| `--force-reindex` | `False` | 强制重新索引项目 |
| `--debug` | `False` | 启用调试模式 |
| `--quiet` | `False` | 静默模式 |

### 使用示例

```bash
# Context-Aware模式（推荐）
python main_test_generator.py \
    --project ../myproject \
    --class com.util.StringHelper \
    --method isEmpty \
    --generation-mode context-aware

# 混合模式（最高成功率）
python main_test_generator.py \
    --project ../myproject \
    --class com.util.StringHelper \
    --method isEmpty \
    --generation-mode hybrid \
    --max-attempts 5

# 传统RAG模式
python main_test_generator.py \
    --project ../myproject \
    --class com.util.StringHelper \
    --method isEmpty \
    --generation-mode rag \
    --debug
```

## 🔧 编程接口

### 基本使用

```python
from improved_test_generator import ImprovedTestGenerator
from pathlib import Path

# 初始化生成器
generator = ImprovedTestGenerator(
    project_path=Path("./your-java-project"),
    output_dir=Path("./generated-tests"),
    debug=True
)

# 生成测试
result = generator.generate_test_for_method(
    class_name="com.example.Calculator",
    method_name="add",
    generation_mode="context-aware",  # 或 "hybrid", "rag"
    test_style="comprehensive",
    max_fix_attempts=3,
    fix_strategy="both"
)

# 检查结果
if result['success']:
    print(f"✅ 测试生成成功: {result.get('test_file_path', 'N/A')}")
    print(f"⏱️ 耗时: {result.get('total_time', 'N/A')} 秒")
else:
    print(f"❌ 生成失败: {result['error']}")
```

### 批量生成

```python
# 批量生成测试
test_cases = [
    ("com.example.Calculator", "add"),
    ("com.example.Calculator", "subtract"),
    ("com.example.StringUtils", "isEmpty"),
]

for class_name, method_name in test_cases:
    result = generator.generate_test_for_method(
        class_name=class_name,
        method_name=method_name,
        generation_mode="hybrid",
        test_style="comprehensive"
    )
    
    if result['success']:
        print(f"✅ {class_name}#{method_name}: 成功")
    else:
        print(f"❌ {class_name}#{method_name}: {result['error']}")
```

## 🛠️ 修复策略

### compile-only
- **用途**: 仅修复编译错误
- **适用场景**: 项目依赖复杂，运行时环境难以配置
- **优势**: 快速验证测试代码的语法正确性

### runtime-only
- **用途**: 修复编译和运行时错误，但专注于运行时问题
- **适用场景**: 编译环境正常，但测试逻辑需要调整
- **特点**: 会正确处理编译错误

### both（推荐）
- **用途**: 修复编译和运行时错误
- **适用场景**: 一般情况下的默认选择
- **优势**: 需要生成完整可运行的测试

## 🐛 故障排除

### 常见问题

**1. Tree-sitter解析失败**
```bash
# 重新安装Tree-sitter
pip uninstall tree-sitter tree-sitter-java
pip install tree-sitter tree-sitter-java

# 手动编译语言包
python -c "from tree_sitter import Language; Language.build_library('build/my-languages.so', ['tree-sitter-java'])"
```

**2. Ollama连接失败**
```bash
# 检查Ollama服务状态
ollama list
ollama ps

# 重启Ollama服务
ollama serve
```

**3. Maven编译错误**
```bash
# 检查Maven配置
mvn clean compile
mvn dependency:tree

# 更新依赖
mvn clean install -U
```

**4. ChromaDB权限问题**
```bash
# 清理ChromaDB数据
rm -rf ./chroma_db

# 重新创建向量存储
python -c "from rag.vector_store import CodeVectorStore; CodeVectorStore('test').reset_collection()"
```

### 调试模式

```python
# 启用详细调试
generator = ImprovedTestGenerator(
    project_path=Path("./project"),
    output_dir=Path("./output"),
    debug=True  # 显示详细的调试信息
)

# 查看生成过程
result = generator.generate_test_for_method(
    class_name="com.example.Test",
    method_name="testMethod",
    generation_mode="context-aware",
    test_style="comprehensive"
)

# 检查对话记录
conversation_file = result.get('conversation_file')
if conversation_file:
    print(f"对话记录: {conversation_file}")
```

## 🎯 最佳实践

1. **首次使用**: 建议启用调试模式 `--debug` 查看详细过程
2. **编译问题**: 先确保项目可以正常编译 `mvn clean compile`
3. **性能优化**: 使用Context-Aware模式获得最佳性能
4. **生产环境**: 推荐使用混合模式获得最高成功率
5. **批量处理**: 使用编程接口进行批量测试生成
6. **错误排查**: 查看错误分析建议，按步骤排查问题

## 📈 性能优化

### 1. 模式选择优化
- **快速原型**: 使用Context-Aware模式
- **生产环境**: 使用混合模式
- **复杂项目**: 使用RAG模式

### 2. 生成效率优化
- **批量生成**: 一次性生成多个测试方法
- **智能重试**: 根据错误类型调整重试策略
- **模型预热**: 预先加载常用模型

### 3. 资源管理
- **内存控制**: 限制向量存储的内存使用
- **磁盘清理**: 定期清理临时文件和缓存
- **连接池**: 复用LLM服务连接

---

📚 **更多详细信息请参考 [docs/](docs/) 目录下的其他文档**
