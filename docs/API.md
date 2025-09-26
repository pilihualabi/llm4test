# API 文档

## 核心类和方法

### ImprovedTestGenerator

主要的测试生成器类，提供完整的测试生成功能。

#### 构造函数

```python
ImprovedTestGenerator(project_path: Path, output_dir: Path, debug: bool = False)
```

**参数：**
- `project_path`: Java项目路径
- `output_dir`: 测试输出目录
- `debug`: 是否启用调试模式

#### 主要方法

##### generate_test_for_method

```python
def generate_test_for_method(
    self, 
    class_name: str, 
    method_name: str,
    use_rag: bool = True, 
    test_style: str = "comprehensive",
    max_fix_attempts: int = 3,
    fix_strategy: str = "both"
) -> Dict[str, Any]
```

为指定方法生成测试代码。

**参数：**
- `class_name`: 完整的类名（包含包名）
- `method_name`: 方法名
- `use_rag`: 是否使用RAG技术增强上下文
- `test_style`: 测试风格（comprehensive, minimal, bdd等）
- `max_fix_attempts`: 最大修复尝试次数
- `fix_strategy`: 修复策略（compile-only, runtime-only, both）

**返回值：**
```python
{
    'success': bool,           # 是否成功
    'test_file_path': str,     # 生成的测试文件路径（如果成功）
    'generated_test': str,     # 生成的测试代码（如果成功）
    'error': str,              # 错误信息（如果失败）
    'attempts': int,           # 修复尝试次数
    'context_used': int,       # 使用的上下文数量
    'rag_enabled': bool,       # 是否启用了RAG
    'phases': List[str]        # 执行的修复阶段
}
```

### SmartProjectAnalyzer

智能项目分析器，用于分析Java项目结构和建立向量索引。

#### 构造函数

```python
SmartProjectAnalyzer(
    project_path: Path,
    vector_store: CodeVectorStore = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
)
```

#### 主要方法

##### analyze_project

```python
def analyze_project(self, force_reindex: bool = False) -> Dict[str, Any]
```

分析项目并建立向量索引。

**参数：**
- `force_reindex`: 是否强制重新索引

**返回值：**
```python
{
    'stats': {
        'total_files': int,
        'total_classes': int,
        'total_methods': int,
        'indexed_chunks': int
    },
    'files': List[str],
    'classes': List[str],
    'methods': List[str]
}
```

##### get_relevant_context

```python
def get_relevant_context(
    self, 
    class_name: str, 
    method_name: str, 
    max_results: int = 5
) -> List[Dict[str, Any]]
```

获取与指定方法相关的上下文信息。

### CodeVectorStore

代码向量存储，基于ChromaDB实现。

#### 构造函数

```python
CodeVectorStore(
    collection_name: str = "code_chunks",
    persist_directory: str = "./chroma_db"
)
```

#### 主要方法

##### add_code_chunk

```python
def add_code_chunk(
    self, 
    chunk_id: str, 
    code: str, 
    metadata: Dict[str, Any]
) -> None
```

添加代码片段到向量存储。

##### search_similar

```python
def search_similar(
    self, 
    query: str, 
    max_results: int = 5
) -> List[Dict[str, Any]]
```

搜索相似的代码片段。

### SimpleTreeSitterParser

简化的Tree-sitter解析器，用于Java代码解析。

#### 主要方法

##### parse_java_file

```python
def parse_java_file(self, file_path: str) -> Dict[str, Any]
```

解析Java文件并提取类和方法信息。

##### extract_method_body

```python
def extract_method_body(
    self, 
    source_code: str, 
    method_name: str
) -> Optional[str]
```

从源代码中提取指定方法的完整实现。

## 命令行接口

### main_test_generator.py

主程序入口，提供完整的命令行接口。

#### 基本语法

```bash
python main_test_generator.py [OPTIONS]
```

#### 参数说明

**必需参数：**
- `--project, -p`: Java项目路径
- `--class`: 目标类的完整包名
- `--method`: 目标方法名

**可选参数：**
- `--output`: 输出目录（默认: ./generated_tests）
- `--style`: 测试风格（默认: comprehensive）
- `--max-attempts`: 最大修复尝试次数（默认: 3）
- `--fix-strategy`: 修复策略（默认: both）
- `--rag/--no-rag`: 启用/禁用RAG检索（默认: 启用）
- `--debug`: 启用调试模式
- `--quiet, -q`: 静默模式

#### 返回码

- `0`: 成功
- `1`: 失败

## 使用示例

### 基础使用

```python
from pathlib import Path
from improved_test_generator import ImprovedTestGenerator

# 初始化
generator = ImprovedTestGenerator(
    project_path=Path("./my-project"),
    output_dir=Path("./generated_tests"),
    debug=True
)

# 单个方法
result = generator.generate_test_for_method(
    class_name="com.example.Calculator", 
    method_name="add",
    use_rag=True,
    test_style="comprehensive",
    max_fix_attempts=3,
    fix_strategy="both"
)

if result['success']:
    print(f"✅ 测试生成成功: {result['test_file_path']}")
else:
    print(f"❌ 生成失败: {result['error']}")
```

### 高级使用

```python
from rag.project_analyzer import SmartProjectAnalyzer
from rag.vector_store import CodeVectorStore

# 自定义向量存储
vector_store = CodeVectorStore("custom_collection")

# 自定义分析器
analyzer = SmartProjectAnalyzer(
    project_path=Path("./project"),
    vector_store=vector_store
)

# 强制重新索引
analyzer.analyze_project(force_reindex=True)
```

### 批量生成

```python
def batch_generate(generator, test_cases):
    """批量生成测试"""
    results = []
    
    for class_name, method_name in test_cases:
        result = generator.generate_test_for_method(
            class_name=class_name,
            method_name=method_name,
            use_rag=True,
            test_style="comprehensive",
            fix_strategy="both"
        )
        results.append(result)
    
    return results

# 使用示例
test_cases = [
    ("com.example.Calculator", "add"),
    ("com.example.Calculator", "subtract"),
    ("com.example.StringUtils", "isEmpty"),
]

results = batch_generate(generator, test_cases)
```

## 配置选项

### 修复策略 (fix_strategy)

| 策略 | 描述 | 使用场景 |
|------|------|----------|
| `compile-only` | 只修复编译错误 | 项目编译环境复杂，运行时测试困难 |
| `runtime-only` | 只修复运行时错误 | 编译没问题，但测试逻辑需要调整 |
| `both` | 修复编译和运行时错误 | 一般情况下的推荐选择 |

### 测试风格 (test_style)

| 风格 | 描述 | 适用场景 |
|------|------|----------|
| `comprehensive` | 全面测试，包含多种测试场景 | 重要的业务逻辑方法 |
| `minimal` | 最小化测试，只测试基本功能 | 简单的工具方法 |
| `bdd` | 行为驱动开发风格测试 | 业务需求明确的方法 |

## 错误处理

### 常见错误类型

1. **编译错误**: 导入缺失、类型不匹配等
2. **运行时错误**: 空指针异常、断言失败等
3. **RAG检索错误**: 向量存储访问失败
4. **LLM调用错误**: 模型服务不可用

### 错误恢复机制

- **自动重试**: 对于临时性错误自动重试
- **降级处理**: RAG失败时使用基础模式
- **详细日志**: 提供完整的错误追踪信息
