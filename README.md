# LLM4TestGen - 智能测试生成系统

🚀 **基于大语言模型的Java单元测试自动生成工具**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tree-sitter](https://img.shields.io/badge/Tree--sitter-Enabled-green.svg)](https://tree-sitter.github.io/tree-sitter/)

LLM4TestGen 是一个先进的测试生成系统，结合了大语言模型(LLM)、检索增强生成(RAG)技术和智能修复机制，能够为Java项目自动生成高质量的单元测试。

## ✨ 核心特性

### 🧠 智能测试生成
- **完整方法体分析**: 使用Tree-sitter解析器提取完整的方法实现
- **上下文感知生成**: 支持RAG和Context-Aware两种生成模式
- **多种测试风格**: 支持comprehensive、minimal、BDD等测试风格
- **智能修复机制**: 自动修复编译错误和运行时错误

### 🔍 双模式生成技术
- **RAG模式**: 基于向量检索的上下文增强生成
- **Context-Aware模式**: 基于静态分析的快速生成（600倍速度提升）
- **混合模式**: 结合两种模式优势，自动回退机制
- **增量索引**: 支持项目变更的增量更新

### 🛠️ 强大的修复能力
- **多种修复策略**: 支持 `compile-only`、`runtime-only`、`both` 三种修复策略
- **编译错误修复**: 自动识别和修复导入、类型等编译问题
- **运行时错误修复**: 处理空指针、断言失败等运行时问题
- **智能重试机制**: 多轮修复尝试，提高成功率
- **详细错误分析**: 提供具体的错误原因和修复建议

### 📊 完善的监控和日志
- **实时进度显示**: 清晰的步骤划分和状态更新
- **对话记录**: 完整记录与大模型的交互过程
- **统计分析**: 详细的生成统计和成功率分析
- **调试支持**: 丰富的调试信息和错误追踪

## 🏗️ 系统架构

```
LLM4TestGen
├── 🧠 核心生成器 (ImprovedTestGenerator)
├── 🔍 RAG系统 (ProjectAnalyzer + VectorStore)
├── 🧠 Context-Aware系统 (StaticAnalyzer + ProjectIndex)
├── 🌳 源码分析 (Tree-sitter Parser)
├── 🔧 智能修复 (CompileFixLoop + RuntimeFixLoop)
├── 📝 提示工程 (EnhancedTestPrompt)
└── 📊 监控日志 (ConversationLogger)
```

## 📋 系统要求

### 基础环境
- **Python**: 3.8+
- **Java**: 8+ (用于编译和运行生成的测试)
- **Maven**: 3.6+ (Java项目构建工具)

### 大语言模型服务
- **Ollama**: 本地LLM服务
  - 代码生成模型: `qwen2.5-coder:7b` 或更高版本
  - 嵌入模型: `qwen3-embedding:latest`

### Python依赖
```bash
# 核心依赖
ollama>=0.1.0
chromadb>=0.4.0
tree-sitter>=0.20.0
tree-sitter-java>=0.20.0

# 数据处理
numpy>=1.21.0
pandas>=1.3.0

# 其他工具
pathlib
argparse
logging
```

## 🚀 快速开始

### 1. 环境准备

**安装Python依赖**
```bash
pip install -r requirements.txt
```

**安装Tree-sitter语言包**
```bash
# 自动安装（推荐）
python -c "from source_analysis.simple_tree_sitter_parser import SimpleTreeSitterParser; SimpleTreeSitterParser()"

# 手动安装
git clone https://github.com/tree-sitter/tree-sitter-java
# 按照Tree-sitter文档配置
```

**配置Ollama服务**
```bash
# 启动Ollama服务
ollama serve

# 拉取所需模型
ollama pull qwen2.5-coder:7b
ollama pull qwen3-embedding:latest
```

### 2. 基础使用

#### 命令行使用（推荐）

```bash
# Context-Aware模式（推荐，极速生成）
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode context-aware

# 混合模式（最高成功率）
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode hybrid

# 传统RAG模式
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --generation-mode rag

# 使用不同的修复策略
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --fix-strategy runtime-only \
    --max-attempts 5

# 启用调试模式
python main_test_generator.py \
    --project ../your-java-project \
    --class com.example.Calculator \
    --method add \
    --debug
```

#### 编程接口使用

```python
from improved_test_generator import ImprovedTestGenerator
from pathlib import Path

# 初始化生成器
generator = ImprovedTestGenerator(
    project_path=Path("./your-java-project"),
    output_dir=Path("./generated-tests"),
    debug=True  # 启用调试模式
)

# Context-Aware模式生成测试（推荐）
result = generator.generate_test_for_method(
    class_name="com.example.Calculator",
    method_name="add",
    generation_mode="context-aware",  # 或 "hybrid", "rag"
    test_style="comprehensive",
    max_fix_attempts=3,
    fix_strategy="both"  # 可选: "compile-only", "runtime-only", "both"
)

# 检查结果
if result['success']:
    print(f"✅ 测试生成成功: {result.get('test_file_path', 'N/A')}")
    print(f"⏱️ 耗时: {result.get('total_time', 'N/A')} 秒")
else:
    print(f"❌ 生成失败: {result['error']}")
```

## 📁 项目结构

```
llm4testgen/
├── 📄 main_test_generator.py      # 🌟 主程序入口
├── 📄 improved_test_generator.py  # 🌟 核心测试生成器
├── 📁 source_analysis/           # 源码分析模块
│   ├── simple_tree_sitter_parser.py  # Tree-sitter解析器
│   ├── method_parser.py              # 方法解析器
│   └── ...
├── 📁 rag/                       # RAG检索系统
│   ├── project_analyzer.py           # 项目分析器
│   └── vector_store.py               # 向量存储
├── 📁 prompting/                 # 提示工程
│   ├── enhanced_test_prompt.py       # 增强测试提示
│   ├── compile_fix_prompt.py         # 编译修复提示
│   └── runtime_fix_prompt.py         # 运行时修复提示
├── 📁 utils/                     # 工具模块
│   ├── improved_compilation_manager.py  # 编译管理器
│   ├── conversation_logger.py           # 对话记录器
│   └── ...
├── 📁 llm/                       # LLM接口
│   └── ollama_client.py              # Ollama客户端
├── 📁 config/                    # 配置文件
├── 📁 tests/                     # 测试和示例
│   ├── examples/                     # 使用示例
│   ├── unit/                         # 单元测试
│   ├── integration/                  # 集成测试
│   └── output/                       # 测试输出
├── 📁 docs/                      # 文档
└── 📄 requirements.txt           # Python依赖
```

## 📊 命令行参数详解

### 必需参数
- `--project, -p`: Java项目路径 (必需)
- `--class`: 目标类的完整包名 (必需)
- `--method`: 目标方法名 (必需)

### 可选参数
- `--output`: 输出目录 (默认: ./generated_tests)
- `--generation-mode`: 生成模式 (默认: hybrid)
  - `context-aware`: Context-Aware模式（极速）
  - `hybrid`: 混合模式（推荐）
  - `rag`: 传统RAG模式
- `--style`: 测试风格 (默认: comprehensive)
- `--max-attempts`: 最大修复尝试次数 (默认: 3)
- `--fix-strategy`: 修复策略 (默认: both)
  - `compile-only`: 仅修复编译错误
  - `runtime-only`: 仅修复运行时错误
  - `both`: 修复编译和运行时错误
- `--force-reindex`: 强制重新索引项目
- `--debug`: 启用调试模式
- `--quiet, -q`: 静默模式，减少输出

### 使用示例

```bash
# Context-Aware模式（推荐）
python main_test_generator.py \
    --project ../pdfcompare \
    --class com.example.pdfcompare.util.ImageComparator \
    --method compareImages \
    --generation-mode context-aware \
    --debug

# 混合模式（最高成功率）
python main_test_generator.py \
    --project ../pdfcompare \
    --class com.example.Calculator \
    --method add \
    --generation-mode hybrid \
    --max-attempts 5
```

## 🔧 高级配置

### RAG系统配置

```python
# 自定义RAG配置
from rag.project_analyzer import SmartProjectAnalyzer
from rag.vector_store import CodeVectorStore

# 创建自定义向量存储
vector_store = CodeVectorStore(
    collection_name="my_project",
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
```

### 批量生成测试

```python
from improved_test_generator import ImprovedTestGenerator
from pathlib import Path

# 创建生成器实例
generator = ImprovedTestGenerator(
    project_path=Path("../your-java-project"),
    output_dir=Path("./generated_tests"),
    debug=True
)

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
        use_rag=True,
        test_style="comprehensive",
        fix_strategy="both"
    )

    if result['success']:
        print(f"✅ {class_name}#{method_name}: 成功")
    else:
        print(f"❌ {class_name}#{method_name}: {result['error']}")
```

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
    use_rag=True,
    test_style="comprehensive"
)

# 检查对话记录
conversation_file = result.get('conversation_file')
if conversation_file:
    print(f"对话记录: {conversation_file}")
```

## 📈 性能优化

### 1. RAG索引优化
- **增量更新**: 只重新索引变更的文件
- **并行处理**: 多线程分析大型项目
- **缓存机制**: 缓存频繁访问的上下文

### 2. 生成效率优化
- **批量生成**: 一次性生成多个测试方法
- **智能重试**: 根据错误类型调整重试策略
- **模型预热**: 预先加载常用模型

### 3. 资源管理
- **内存控制**: 限制向量存储的内存使用
- **磁盘清理**: 定期清理临时文件和缓存
- **连接池**: 复用LLM服务连接

## 📚 文档

- 📖 [快速开始指南](docs/QUICK_START.md) - 5分钟快速上手
- 📋 [用户手册](docs/USER_MANUAL.md) - 详细的使用说明
- 🔧 [API文档](docs/API.md) - 完整的API参考
- 🏗️ [项目结构](docs/PROJECT_STRUCTURE.md) - 项目架构说明
- 🧠 [Context-Aware指南](docs/context_aware_guide.md) - Context-Aware模式详解

## 📊 性能对比

| 指标 | RAG模式 | Context-Aware模式 | 混合模式 |
|------|---------|-------------------|----------|
| **速度** | 60-80秒 | **0.1-0.5秒** | 0.5-10秒 |
| **包路径准确率** | 70-80% | **100%** | **100%** |
| **依赖识别率** | 60-70% | **95%+** | **95%+** |
| **编译成功率** | 60-70% | **90%+** | **95%+** |
| **稳定性** | 不稳定 | **非常稳定** | **最稳定** |

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **Tree-sitter**: 强大的语法解析框架
- **ChromaDB**: 高效的向量数据库
- **Ollama**: 便捷的本地LLM服务
- **OpenAI**: GPT模型的启发和参考

---

🌟 **如果这个项目对你有帮助，请给我们一个Star！** ⭐
