# LLM4TestGen 用户手册

## 目录
1. [快速开始](#快速开始)
2. [生成模式详解](#生成模式详解)
3. [命令行使用](#命令行使用)
4. [编程接口](#编程接口)
5. [修复策略](#修复策略)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)

## 快速开始

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
# 推荐使用混合模式
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode hybrid \
    --debug
```

## 生成模式详解

### Context-Aware模式（极速）
- ⚡ **极速生成**: 0.1-0.5秒完成测试生成
- 🎯 **100%准确**: 包路径和依赖关系完全正确
- 🔍 **智能分析**: 自动识别依赖并生成Mock
- 📦 **项目级索引**: 基于静态分析的完整项目理解

**使用场景**：
- 标准Java项目结构
- 需要快速生成测试框架
- 批量测试生成
- CI/CD集成

### 混合模式（推荐）
- 🏆 **最高成功率**: 结合两种模式的优势
- 🔄 **智能回退**: Context-Aware失败时自动使用RAG
- 🛡️ **生产就绪**: 适合生产环境使用
- 🎯 **最佳选择**: 适用于所有项目类型

**使用场景**：
- 生产环境使用
- 复杂或非标准项目
- 需要最高成功率
- 所有项目类型

### RAG模式（深度理解）
- 🔍 **深度上下文**: 基于向量检索的上下文理解
- 📚 **语义理解**: 理解复杂的业务逻辑
- 🎯 **精准生成**: 适合复杂业务场景

**使用场景**：
- 需要深度上下文理解
- 复杂业务逻辑
- 特殊项目结构

## 命令行使用

### 基本语法

```bash
python main_test_generator.py [OPTIONS]
```

### 必需参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--project` | `-p` | Java项目路径 | `../my-project` |
| `--class` | | 目标类的完整包名 | `com.example.Calculator` |
| `--method` | | 目标方法名 | `add` |

### 可选参数

| 参数 | 默认值 | 说明 | 可选值 |
|------|--------|------|--------|
| `--output` | `./generated_tests` | 输出目录 | 任意路径 |
| `--style` | `comprehensive` | 测试风格 | `comprehensive`, `minimal`, `bdd` |
| `--max-attempts` | `3` | 最大修复尝试次数 | 1-10 |
| `--fix-strategy` | `both` | 修复策略 | `compile-only`, `runtime-only`, `both` |
| `--rag/--no-rag` | `--rag` | 启用/禁用RAG检索 | - |
| `--debug` | `False` | 启用调试模式 | - |
| `--quiet` | `False` | 静默模式 | - |

### 使用示例

#### 基础使用
```bash
# 最简单的使用方式
python main_test_generator.py \
    --project ../calculator-project \
    --class com.example.Calculator \
    --method add
```

#### 高级使用
```bash
# 使用所有高级选项
python main_test_generator.py \
    --project ../complex-project \
    --class com.example.service.UserService \
    --method validateUser \
    --output ./user_service_tests \
    --style comprehensive \
    --max-attempts 5 \
    --fix-strategy both \
    --debug
```

#### 批量生成脚本
```bash
#!/bin/bash
# batch_generate.sh

PROJECT="../my-project"
OUTPUT="./generated_tests"

# 生成多个测试
python main_test_generator.py -p $PROJECT --class com.example.Calculator --method add --output $OUTPUT
python main_test_generator.py -p $PROJECT --class com.example.Calculator --method subtract --output $OUTPUT
python main_test_generator.py -p $PROJECT --class com.example.StringUtils --method isEmpty --output $OUTPUT
```

## 编程接口

### 基本使用

```python
from improved_test_generator import ImprovedTestGenerator
from pathlib import Path

# 初始化生成器
generator = ImprovedTestGenerator(
    project_path=Path("../your-java-project"),
    output_dir=Path("./generated_tests"),
    debug=True
)

# 生成单个测试
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
    print(f"✅ 测试生成成功")
    print(f"📄 测试文件: {result.get('test_file_path', 'N/A')}")
    print(f"🔧 修复次数: {result.get('attempts', 0)}")
else:
    print(f"❌ 生成失败: {result['error']}")
```

### 批量生成

```python
def batch_generate_tests(generator, test_cases):
    """批量生成测试用例"""
    results = []
    
    for class_name, method_name in test_cases:
        print(f"🎯 生成测试: {class_name}#{method_name}")
        
        result = generator.generate_test_for_method(
            class_name=class_name,
            method_name=method_name,
            use_rag=True,
            test_style="comprehensive",
            fix_strategy="both"
        )
        
        results.append({
            'class': class_name,
            'method': method_name,
            'success': result['success'],
            'error': result.get('error'),
            'attempts': result.get('attempts', 0)
        })
        
        if result['success']:
            print(f"   ✅ 成功")
        else:
            print(f"   ❌ 失败: {result['error']}")
    
    return results

# 使用示例
test_cases = [
    ("com.example.Calculator", "add"),
    ("com.example.Calculator", "subtract"),
    ("com.example.StringUtils", "isEmpty"),
    ("com.example.DateUtils", "formatDate"),
]

results = batch_generate_tests(generator, test_cases)

# 统计结果
success_count = sum(1 for r in results if r['success'])
total_count = len(results)
print(f"\n📊 生成统计: {success_count}/{total_count} 成功 ({success_count/total_count*100:.1f}%)")
```

### 自定义配置

```python
# 自定义RAG配置
from rag.project_analyzer import SmartProjectAnalyzer
from rag.vector_store import CodeVectorStore

# 创建自定义向量存储
vector_store = CodeVectorStore(
    collection_name="my_custom_project",
    persist_directory="./custom_chroma_db"
)

# 创建项目分析器
analyzer = SmartProjectAnalyzer(
    project_path=Path("./my-project"),
    vector_store=vector_store,
    chunk_size=1000,
    chunk_overlap=200
)

# 强制重新索引
analyzer.analyze_project(force_reindex=True)

# 使用自定义配置的生成器
generator = ImprovedTestGenerator(
    project_path=Path("./my-project"),
    output_dir=Path("./custom_tests"),
    debug=True
)

# 可以通过替换内部组件来使用自定义配置
generator.project_analyzer = analyzer
```

## 配置选项

### 测试风格 (test_style)

| 风格 | 描述 | 适用场景 |
|------|------|----------|
| `comprehensive` | 全面测试，包含多种测试场景 | 重要的业务逻辑方法 |
| `minimal` | 最小化测试，只测试基本功能 | 简单的工具方法 |
| `bdd` | 行为驱动开发风格测试 | 业务需求明确的方法 |

### 修复策略 (fix_strategy)

| 策略 | 描述 | 使用场景 |
|------|------|----------|
| `compile-only` | 只修复编译错误 | 项目编译环境复杂，运行时测试困难 |
| `runtime-only` | 只修复运行时错误 | 编译没问题，但测试逻辑需要调整 |
| `both` | 修复编译和运行时错误 | 一般情况下的推荐选择 |

### RAG检索配置

```python
# 在代码中配置RAG参数
result = generator.generate_test_for_method(
    class_name="com.example.Calculator",
    method_name="add",
    use_rag=True,  # 启用RAG
    test_style="comprehensive",
    max_fix_attempts=5,  # 增加修复尝试次数
    fix_strategy="both"
)
```

## 修复策略

### compile-only 策略

**适用场景**：
- 项目依赖复杂，运行时环境难以配置
- 只需要确保生成的测试代码能够编译通过
- 快速验证测试代码的语法正确性

**使用示例**：
```bash
python main_test_generator.py \
    --project ../complex-project \
    --class com.example.ComplexService \
    --method processData \
    --fix-strategy compile-only \
    --max-attempts 3
```

### runtime-only 策略

**适用场景**：
- 编译环境正常，但测试逻辑需要调整
- 专注于修复测试断言和业务逻辑错误
- 已知编译没有问题的情况

**使用示例**：
```bash
python main_test_generator.py \
    --project ../stable-project \
    --class com.example.Calculator \
    --method divide \
    --fix-strategy runtime-only \
    --max-attempts 5
```

### both 策略（推荐）

**适用场景**：
- 一般情况下的默认选择
- 需要生成完整可运行的测试
- 对测试质量要求较高

**使用示例**：
```bash
python main_test_generator.py \
    --project ../my-project \
    --class com.example.UserService \
    --method createUser \
    --fix-strategy both \
    --max-attempts 5
```

## 故障排除

### 常见错误及解决方案

#### 1. "找不到符号" 编译错误

**错误示例**：
```
[ERROR] 找不到符号
[ERROR]   符号:   类 ImageChunk
[ERROR]   位置: 程序包 com.example.pdfcompare.util
```

**解决方案**：
1. 检查项目依赖是否完整
2. 确认Maven配置正确
3. 尝试增加修复尝试次数：`--max-attempts 5`

#### 2. Ollama连接失败

**错误示例**：
```
❌ 运行失败: Connection error
```

**解决方案**：
```bash
# 检查Ollama服务状态
ollama list
ollama ps

# 重启Ollama服务
ollama serve

# 验证模型是否存在
ollama pull qwen2.5-coder:7b
```

#### 3. Tree-sitter解析失败

**错误示例**：
```
❌ 解析类文件失败
```

**解决方案**：
```bash
# 重新安装Tree-sitter
pip uninstall tree-sitter tree-sitter-java
pip install tree-sitter tree-sitter-java

# 验证安装
python -c "from source_analysis.simple_tree_sitter_parser import SimpleTreeSitterParser; SimpleTreeSitterParser()"
```

#### 4. Maven编译错误

**解决方案**：
```bash
# 清理并重新编译项目
cd your-java-project
mvn clean compile

# 检查依赖
mvn dependency:tree

# 更新依赖
mvn clean install -U
```

### 调试技巧

#### 启用详细调试
```bash
python main_test_generator.py \
    --project ../your-project \
    --class com.example.Calculator \
    --method add \
    --debug
```

#### 查看对话记录
生成的对话记录保存在输出目录的 `conversations/` 子目录中，可以查看详细的LLM交互过程。

#### 检查生成的测试代码
即使生成失败，也会在输出目录中保存中间生成的测试代码，可以手动检查和修改。

## 最佳实践

### 1. 项目准备
- 确保Java项目能够正常编译
- 配置好Maven依赖，特别是JUnit 5
- 清理项目中的编译错误

### 2. 参数选择
- 对于复杂方法，使用 `--max-attempts 5` 增加修复机会
- 对于简单方法，使用 `--style minimal` 节省时间
- 开发阶段建议使用 `--debug` 查看详细过程

### 3. 批量生成
- 使用脚本批量生成多个测试
- 先测试简单方法，再处理复杂方法
- 定期清理ChromaDB缓存以获得最新的项目信息

### 4. 结果验证
- 生成后手动检查测试代码的合理性
- 运行生成的测试确保其正确性
- 根据需要调整测试断言和测试数据

### 5. 性能优化
- 对于大型项目，考虑分批处理
- 使用 `--no-rag` 跳过RAG检索以提高速度（但可能影响质量）
- 定期清理输出目录中的临时文件
