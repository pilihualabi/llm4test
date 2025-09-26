# 项目结构说明

## 📁 **目录结构概览**

```
llm4testgen/
├── 📄 main_test_generator.py      # 🌟 主程序入口 (推荐使用)
├── 📄 improved_test_generator.py  # 🌟 核心测试生成器
├── 📄 USER_GUIDE.md              # 📚 统一用户指南
├── 📁 config/                     # 配置文件
│   ├── remote_ollama_config.py        # Ollama远程配置管理
│   └── test_config.py                 # 测试配置
├── 📁 context_aware/              # 🧠 Context-Aware生成系统
│   ├── static_analyzer.py             # 静态代码分析器
│   ├── project_index.py               # 项目索引数据库
│   ├── context_generator.py           # 上下文生成器
│   ├── package_validator.py           # 包验证器
│   └── test_generator.py              # Context-Aware测试生成器
├── 📁 rag/                        # RAG检索增强生成系统
│   ├── project_analyzer.py            # 智能项目分析器
│   ├── vector_store.py                # ChromaDB向量存储
│   ├── code_analyzer.py               # 代码分析器
│   ├── type_resolver.py               # 类型解析器
│   └── external_library_mapper.py     # 外部库映射器
├── 📁 source_analysis/            # 源码分析模块
│   ├── simple_tree_sitter_parser.py   # 🌟 简化Tree-sitter解析器
│   ├── tree_sitter_parser.py          # 完整Tree-sitter解析器
│   ├── ast_analyzer.py                # AST分析器
│   ├── method_parser.py               # 方法解析器
│   ├── java_parser.py                 # Java专用解析器
│   ├── base_parser.py                 # 解析器基类
│   ├── dependency_extractor.py        # 依赖提取器
│   └── parser_manager.py              # 解析器管理器
├── 📁 prompting/                  # 提示工程系统
│   ├── enhanced_test_prompt.py        # 增强测试生成提示
│   ├── test_case_prompt.py            # 测试用例生成提示
│   ├── compile_fix_prompt.py          # 编译修复提示
│   ├── runtime_fix_prompt.py          # 运行时修复提示
│   ├── clustering_prompt.py           # 聚类分析提示
│   └── scenario_list_prompt.py        # 场景列表提示
├── 📁 utils/                      # 工具模块
│   ├── improved_compilation_manager.py # 🌟 改进编译管理器
│   ├── smart_fix_loop.py              # 智能修复循环
│   ├── conversation_logger.py         # 对话日志记录
│   ├── test_compilation_manager.py    # 测试编译管理器
│   ├── test_executor.py               # 测试执行器
│   ├── execution_manager.py           # 执行管理器
│   └── enhanced_fix_loops.py          # 增强修复循环
├── 📁 llm/                        # LLM客户端
│   └── ollama_client.py               # Ollama API客户端
├── 📁 docs/                       # 项目文档
│   ├── QUICK_START.md                 # 快速开始指南
│   ├── USER_MANUAL.md                 # 详细用户手册
│   ├── API.md                         # API参考
│   ├── PROJECT_STRUCTURE.md           # 本文档
│   └── context_aware_guide.md         # Context-Aware模式指南
├── 📁 examples/                   # 使用示例
│   ├── basic_usage.py                 # 基础使用示例
│   ├── advanced_usage.py              # 高级使用示例
│   ├── context_aware_usage.py         # Context-Aware使用示例
│   └── improved_usage.py              # 改进使用示例
├── 📁 tests/                      # 测试和演示文件
│   ├── 📁 unit/                       # 单元测试
│   ├── 📁 integration/                # 集成测试
│   ├── 📁 examples/                   # 测试示例
│   ├── 📁 output/                     # 测试输出
│   ├── 📁 debug_scripts/              # 调试脚本
│   ├── 📁 demo_scripts/               # 演示脚本
│   ├── 📁 generated_output/           # 生成的测试输出
│   ├── quick_check.py                 # 快速环境检查
│   ├── test_rag_simple.py             # RAG系统测试
│   ├── test_project_analyzer.py       # 项目分析器测试
│   ├── demo_full_system.py            # 完整系统演示
│   └── ...                            # 其他测试文件
├── 📁 real_project_example/   # 演示项目
│   └── src/main/java/com/company/utils/
│       ├── MathCalculator.java    # 数学计算工具类
│       └── StringHelper.java      # 字符串处理工具类
├── 📁 requirements.txt         # Python依赖
├── 📁 README.md               # 项目主文档
├── 📁 LICENSE                 # MIT许可证
└── 📁 .gitignore              # Git忽略文件
```

## 🔧 **核心文件说明**

### **主要入口文件**

- **`enhanced_test_generator.py`** - 系统主入口，协调整个测试生成流程
- **`llm4testgen_cli.py`** - 命令行接口 (已删除，功能集成到主生成器)

### **核心模块**

#### **1. RAG系统 (`rag/`)**
- **`project_analyzer.py`** - 智能项目分析，自动提取代码结构和依赖关系
- **`vector_store.py`** - ChromaDB向量存储，支持语义代码检索

#### **2. 源码分析 (`source_analysis/`)**
- **`java_parser.py`** - Java代码解析，提取类、方法、依赖信息
- **`parser_manager.py`** - 解析器工厂，支持多语言扩展
- **`test_scaffold.py`** - 测试脚手架生成，创建测试文件结构

#### **3. 提示系统 (`prompting/`)**
- **`enhanced_test_prompt.py`** - 增强的测试生成提示模板
- **`test_case_prompt.py`** - 基础测试用例生成提示
- **`compile_fix_prompt.py`** - 编译错误修复提示
- **`runtime_fix_prompt.py`** - 运行时错误修复提示

#### **4. 工具模块 (`utils/`)**
- **`smart_fix_loop.py`** - 智能修复循环，自动处理编译和运行时错误
- **`test_compilation_manager.py`** - 测试编译和运行管理

#### **5. LLM客户端 (`llm/`)**
- **`ollama_client.py`** - Ollama API客户端，支持代码生成和修复

### **配置文件**

- **`config/remote_ollama_config.py`** - Ollama服务器配置管理
- **`config/test_config.py`** - 测试相关配置

## 🗂️ **已删除的无用文件**

### **临时文件**
- `chroma_db/` - ChromaDB临时数据目录
- `test_generation_output/` - 测试生成输出目录
- `smart_fix_demo_tests/` - 演示测试目录
- `generated_tests/` - 生成的测试目录
- `real_project_tests/` - 项目测试目录
- `__pycache__/` - Python缓存目录

### **过时文件**
- `generate_test_suite.py` - 旧的测试套件生成器
- `llm4testgen_cli.py` - 命令行接口 (功能已集成)

### **无用目录**
- `input/` - 空输入目录
- `init/` - 构建系统相关 (不在当前使用范围内)
- `coverage/` - 覆盖率分析 (不在当前使用范围内)
- `cli/` - 命令行工具 (不在当前使用范围内)

## 📊 **文件统计**

- **Python文件**: 约25个
- **核心模块**: 8个主要模块
- **配置文件**: 2个
- **文档文件**: 4个
- **示例文件**: 2个
- **测试文件**: 约10个

## 🎯 **模块依赖关系**

```
enhanced_test_generator.py (主入口)
    ├── rag.project_analyzer
    ├── rag.vector_store
    ├── source_analysis.java_parser
    ├── prompting.enhanced_test_prompt
    ├── utils.smart_fix_loop
    └── config.remote_ollama_config

smart_fix_loop.py
    ├── llm.ollama_client
    ├── prompting.enhanced_test_prompt
    └── utils.test_compilation_manager

project_analyzer.py
    ├── rag.vector_store
    └── source_analysis.java_parser
```

## 🚀 **扩展建议**

### **添加新语言支持**
1. 在 `source_analysis/` 下创建新的语言解析器
2. 实现 `BaseLanguageParser` 接口
3. 在 `parser_manager.py` 中注册新解析器

### **添加新的LLM提供商**
1. 在 `llm/` 下创建新的客户端
2. 实现统一的接口
3. 在配置中支持新提供商

### **添加新的测试框架**
1. 在 `source_analysis/` 下创建测试框架适配器
2. 支持不同的测试注解和断言
3. 扩展测试脚手架生成

## 📝 **维护说明**

### **定期清理**
- 删除 `__pycache__/` 目录
- 清理临时生成的文件
- 更新过时的依赖

### **代码质量**
- 保持模块间的低耦合
- 遵循单一职责原则
- 添加适当的错误处理和日志

### **文档更新**
- 及时更新API文档
- 维护使用示例
- 记录重要的架构变更
