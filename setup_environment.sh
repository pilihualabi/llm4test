#!/bin/bash

# LLM4TestGen 环境设置脚本
# 用于重新创建和配置虚拟环境

echo "🔧 LLM4TestGen 环境设置"
echo "========================"

# 检查是否在正确的目录
if [ ! -f "main_test_generator.py" ]; then
    echo "❌ 错误：请在 llm4testgen 项目根目录中运行此脚本"
    exit 1
fi

# 1. 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ -d "llm4testgen" ]; then
    echo "⚠️  虚拟环境目录已存在，删除旧环境..."
    rm -rf llm4testgen
fi

python3 -m venv llm4testgen
if [ $? -ne 0 ]; then
    echo "❌ 创建虚拟环境失败"
    exit 1
fi

echo "✅ 虚拟环境创建成功"

# 2. 激活虚拟环境
echo "🔄 激活虚拟环境..."
source llm4testgen/bin/activate

# 3. 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip

# 4. 安装依赖
echo "📚 安装项目依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 安装依赖失败"
        exit 1
    fi
else
    echo "⚠️  requirements.txt 不存在，手动安装核心依赖..."
    pip install ollama chromadb tree-sitter tree-sitter-java numpy pandas requests pathlib2
fi

# 5. 验证安装
echo "🔍 验证安装..."
python -c "import requests; print('✅ requests installed')" 2>/dev/null || echo "❌ requests 安装失败"
python -c "import ollama; print('✅ ollama installed')" 2>/dev/null || echo "❌ ollama 安装失败"
python -c "import chromadb; print('✅ chromadb installed')" 2>/dev/null || echo "❌ chromadb 安装失败"
python -c "import tree_sitter; print('✅ tree_sitter installed')" 2>/dev/null || echo "❌ tree_sitter 安装失败"

# 6. 测试导入
echo "🧪 测试项目导入..."
python -c "from improved_test_generator import ImprovedTestGenerator; print('✅ 项目模块导入成功')" 2>/dev/null || echo "❌ 项目模块导入失败"

echo ""
echo "🎉 环境设置完成！"
echo ""
echo "📋 使用说明："
echo "1. 激活虚拟环境: source llm4testgen/bin/activate"
echo "2. 运行项目: python main_test_generator.py [参数]"
echo "3. 退出虚拟环境: deactivate"
echo ""
echo "💡 示例命令："
echo "python main_test_generator.py \\"
echo "    --project ../pdfcompare \\"
echo "    --class com.example.pdfcompare.util.PDFHighlighter \\"
echo "    --method highlightEntirePage \\"
echo "    --generation-mode context-aware"
