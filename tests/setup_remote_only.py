#!/usr/bin/env python3
"""
远程Ollama专项配置
适用于本地开发 + 远程Ollama服务器的架构
"""

import sys
import requests
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config.remote_ollama_config import remote_config

def input_remote_config():
    """输入远程服务器配置"""
    print("🌐 远程Ollama服务器配置")
    print("="*50)
    
    # 获取服务器地址
    print("请输入远程Ollama服务器信息:")
    server_host = input("🌐 服务器IP或域名: ").strip()
    if not server_host:
        print(" 服务器地址不能为空")
        return None
    
    # 获取端口
    port = input("🔌 端口 (默认11434): ").strip()
    if not port:
        port = "11434"
    
    # 构建基础URL
    base_url = f"http://{server_host}:{port}"
    
    print(f"\n📍 远程服务器地址: {base_url}")
    
    return base_url

def detect_remote_models(base_url):
    """检测远程服务器上的模型"""
    print(f"\n 检测远程服务器模型...")
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=15)
        if response.status_code != 200:
            print(f" 无法连接到远程Ollama服务器")
            print(f"   请检查:")
            print(f"   1. 服务器地址是否正确: {base_url}")
            print(f"   2. Ollama是否在远程服务器上运行")
            print(f"   3. 防火墙是否允许11434端口")
            return None
        
        models_data = response.json()
        available_models = [model.get('name', '') for model in models_data.get('models', [])]
        
        if not available_models:
            print(" 远程服务器上没有找到任何模型")
            return None
        
        print(f" 远程服务器连接成功！")
        print(f" 找到 {len(available_models)} 个模型:")
        
        # 分类显示模型
        generation_models = []
        embedding_models = []
        qwen_models = []
        other_models = []
        
        for model in available_models:
            model_lower = model.lower()
            if any(x in model_lower for x in ['embed', 'embedding']):
                embedding_models.append(model)
            elif 'qwen' in model_lower:
                qwen_models.append(model)
                generation_models.append(model)
            elif any(x in model_lower for x in ['coder', 'code', 'deepseek']):
                generation_models.append(model)
            else:
                other_models.append(model)
        
        print(f"\n🤖 代码生成模型:")
        for model in generation_models:
            print(f"   - {model}")
        
        print(f"\n🔤 嵌入模型:")
        for model in embedding_models:
            print(f"   - {model}")
        
        if other_models:
            print(f"\n 其他模型:")
            for model in other_models[:5]:  # 只显示前5个
                print(f"   - {model}")
            if len(other_models) > 5:
                print(f"   ... 还有 {len(other_models) - 5} 个模型")
        
        return {
            'all_models': available_models,
            'generation_models': generation_models,
            'embedding_models': embedding_models,
            'qwen_models': qwen_models
        }
        
    except requests.exceptions.RequestException as e:
        print(f" 连接远程服务器失败: {e}")
        print(f"   请检查网络连接和服务器状态")
        return None
    except Exception as e:
        print(f" 检测模型异常: {e}")
        return None

def select_models(models_info):
    """选择要使用的模型"""
    print(f"\n 选择模型配置")
    print("="*50)
    
    generation_models = models_info['generation_models']
    embedding_models = models_info['embedding_models']
    all_models = models_info['all_models']
    
    # 选择代码生成模型
    print(f"1. 选择代码生成模型:")
    if generation_models:
        for i, model in enumerate(generation_models, 1):
            print(f"   {i}. {model}")
        print(f"   {len(generation_models) + 1}. 手动输入模型名")
        
        while True:
            choice = input(f"请选择 (1-{len(generation_models) + 1}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(generation_models):
                    code_model = generation_models[idx]
                    break
                elif idx == len(generation_models):
                    code_model = input("请输入代码生成模型名: ").strip()
                    break
                else:
                    print("选择无效，请重新输入")
            except ValueError:
                print("请输入数字")
    else:
        code_model = input("请输入代码生成模型名: ").strip()
    
    # 选择嵌入模型
    print(f"\n2. 选择嵌入模型:")
    if embedding_models:
        for i, model in enumerate(embedding_models, 1):
            print(f"   {i}. {model}")
        print(f"   {len(embedding_models) + 1}. 使用代码生成模型作为嵌入模型")
        print(f"   {len(embedding_models) + 2}. 手动输入模型名")
        
        while True:
            choice = input(f"请选择 (1-{len(embedding_models) + 2}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(embedding_models):
                    embed_model = embedding_models[idx]
                    break
                elif idx == len(embedding_models):
                    embed_model = code_model
                    break
                elif idx == len(embedding_models) + 1:
                    embed_model = input("请输入嵌入模型名: ").strip()
                    break
                else:
                    print("选择无效，请重新输入")
            except ValueError:
                print("请输入数字")
    else:
        print("   1. 使用代码生成模型作为嵌入模型")
        print("   2. 手动输入嵌入模型名")
        
        choice = input("请选择 (1-2): ").strip()
        if choice == "2":
            embed_model = input("请输入嵌入模型名: ").strip()
        else:
            embed_model = code_model
    
    # 选择修复模型（通常使用代码生成模型）
    print(f"\n3. 选择代码修复模型:")
    print(f"   1. 使用代码生成模型 ({code_model})")
    print(f"   2. 手动输入其他模型")
    
    choice = input("请选择 (1-2, 默认1): ").strip()
    if choice == "2":
        fix_model = input("请输入修复模型名: ").strip()
    else:
        fix_model = code_model
    
    return code_model, embed_model, fix_model

def test_remote_models(base_url, code_model, embed_model):
    """测试远程模型功能"""
    print(f"\n 测试远程模型功能...")
    
    # 测试代码生成
    print(f"💻 测试代码生成模型: {code_model}")
    try:
        chat_request = {
            "model": code_model,
            "messages": [
                {
                    "role": "user", 
                    "content": "写一个Java方法计算两个数的和，方法名add"
                }
            ],
            "stream": False
        }
        
        chat_response = requests.post(
            f"{base_url}/api/chat",
            json=chat_request,
            timeout=60
        )
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            if 'message' in chat_data and 'content' in chat_data['message']:
                content = chat_data['message']['content']
                print(f"    代码生成正常，响应长度: {len(content)} 字符")
                
                # 检查是否包含Java代码
                if any(keyword in content for keyword in ['public', 'int', 'add', 'return']):
                    print(f"    Java代码生成质量良好")
                else:
                    print(f"    代码生成可能需要优化提示词")
            else:
                print(f"    代码生成响应格式错误")
                return False
        else:
            print(f"    代码生成失败: {chat_response.status_code}")
            return False
            
    except Exception as e:
        print(f"    代码生成测试异常: {e}")
        return False
    
    # 测试嵌入功能
    print(f"\n🔤 测试嵌入模型: {embed_model}")
    try:
        embed_request = {
            "model": embed_model,
            "prompt": "public int add(int a, int b) { return a + b; }"
        }
        
        embed_response = requests.post(
            f"{base_url}/api/embeddings",
            json=embed_request,
            timeout=30
        )
        
        if embed_response.status_code == 200:
            embed_data = embed_response.json()
            if 'embedding' in embed_data:
                embedding = embed_data['embedding']
                print(f"    嵌入功能正常: {len(embedding)} 维向量")
                print(f"    前5个值: {[round(x, 4) for x in embedding[:5]]}")
                return True
            else:
                print(f"    嵌入响应格式错误")
                return False
        else:
            print(f"    嵌入功能失败: {embed_response.status_code}")
            print(f"   错误信息: {embed_response.text}")
            return False
            
    except Exception as e:
        print(f"    嵌入测试异常: {e}")
        return False

def save_remote_config(base_url, code_model, embed_model, fix_model):
    """保存远程配置"""
    print(f"\n 保存远程配置...")
    
    # 设置配置
    remote_config.set_remote_config(
        base_url=base_url,
        embedding_model=embed_model,
        code_model=code_model,
        fix_model=fix_model
    )
    
    # 显示配置
    print(f"\n 最终配置:")
    remote_config.print_config()
    
    # 保存环境变量文件
    config_content = f'''# 远程Ollama配置文件
# 使用方法: source remote_ollama_env.sh

export OLLAMA_BASE_URL="{base_url}"
export OLLAMA_CODE_MODEL="{code_model}"
export OLLAMA_EMBEDDING_MODEL="{embed_model}"
export OLLAMA_FIX_MODEL="{fix_model}"

echo " 远程Ollama环境变量已设置"
echo "   服务器: $OLLAMA_BASE_URL"
echo "   代码模型: $OLLAMA_CODE_MODEL"
echo "   嵌入模型: $OLLAMA_EMBEDDING_MODEL"
echo "   修复模型: $OLLAMA_FIX_MODEL"
'''
    
    env_file = Path("remote_ollama_env.sh")
    env_file.write_text(config_content)
    
    print(f" 配置已保存到: {env_file}")
    
    # 保存Python配置文件
    py_config_content = f'''# 远程Ollama Python配置
import os

# 设置环境变量
os.environ["OLLAMA_BASE_URL"] = "{base_url}"
os.environ["OLLAMA_CODE_MODEL"] = "{code_model}"
os.environ["OLLAMA_EMBEDDING_MODEL"] = "{embed_model}"
os.environ["OLLAMA_FIX_MODEL"] = "{fix_model}"

print("远程Ollama配置已加载")
'''
    
    py_config_file = Path("remote_config.py")
    py_config_file.write_text(py_config_content)
    
    print(f" Python配置已保存到: {py_config_file}")

def provide_usage_instructions():
    """提供使用说明"""
    print(f"\n 使用说明")
    print("="*50)
    
    print("方法1: 使用Shell环境变量")
    print("   source remote_ollama_env.sh")
    print("   python test_java_only.py")
    
    print("\n方法2: 使用Python配置文件")
    print("   在脚本开头添加: import remote_config")
    print("   python test_java_only.py")
    
    print("\n方法3: 手动设置环境变量")
    print("   export OLLAMA_BASE_URL=\"...\"")
    print("   export OLLAMA_CODE_MODEL=\"...\"")
    print("   export OLLAMA_EMBEDDING_MODEL=\"...\"")
    print("   python test_java_only.py")
    
    print(f"\n 下一步:")
    print("1. source remote_ollama_env.sh")
    print("2. python test_java_only.py")
    print("3. 开始RAG系统开发")

def main():
    """主函数"""
    print("🌐 远程Ollama专项配置助手")
    print("="*60)
    print("适用于: 本地开发 + 远程Ollama服务器架构")
    print("="*60)
    
    # 1. 输入远程配置
    base_url = input_remote_config()
    if not base_url:
        return False
    
    # 2. 检测远程模型
    models_info = detect_remote_models(base_url)
    if not models_info:
        return False
    
    # 3. 选择模型
    code_model, embed_model, fix_model = select_models(models_info)
    
    print(f"\n 您的选择:")
    print(f"   🌐 服务器: {base_url}")
    print(f"   💻 代码生成: {code_model}")
    print(f"   🔤 嵌入模型: {embed_model}")
    print(f"    修复模型: {fix_model}")
    
    # 4. 测试模型功能
    if test_remote_models(base_url, code_model, embed_model):
        print(f"\n 远程模型测试通过！")
        
        # 5. 保存配置
        save_remote_config(base_url, code_model, embed_model, fix_model)
        
        # 6. 提供使用说明
        provide_usage_instructions()
        
        return True
    else:
        print(f"\n 远程模型测试失败")
        print("建议检查:")
        print("1. 模型名称是否正确")
        print("2. 远程服务器上模型是否正常工作")
        print("3. 网络连接是否稳定")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
