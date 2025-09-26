#!/usr/bin/env python3
"""
远程连接快速检查脚本
验证远程Ollama服务器连接状态
"""

import sys
import requests
import os
from pathlib import Path

def check_environment_variables():
    """检查环境变量设置"""
    print(" 检查环境变量设置...")
    
    env_vars = {
        'OLLAMA_BASE_URL': os.getenv('OLLAMA_BASE_URL'),
        'OLLAMA_CODE_MODEL': os.getenv('OLLAMA_CODE_MODEL'),
        'OLLAMA_EMBEDDING_MODEL': os.getenv('OLLAMA_EMBEDDING_MODEL'),
        'OLLAMA_FIX_MODEL': os.getenv('OLLAMA_FIX_MODEL')
    }
    
    all_set = True
    for var_name, var_value in env_vars.items():
        if var_value:
            print(f"    {var_name}: {var_value}")
        else:
            print(f"    {var_name}: 未设置")
            all_set = False
    
    if not all_set:
        print(f"\n 设置建议:")
        print(f"   1. 运行配置脚本: python setup_remote_only.py")
        print(f"   2. 或手动设置环境变量:")
        print(f"      export OLLAMA_BASE_URL=\"http://your-server:11434\"")
        print(f"      export OLLAMA_CODE_MODEL=\"your-code-model\"")
        print(f"      export OLLAMA_EMBEDDING_MODEL=\"your-embed-model\"")
        print(f"   3. 或加载配置文件: source remote_ollama_env.sh")
        return False
    
    return env_vars

def quick_connection_test(base_url):
    """快速连接测试"""
    print(f"\n🌐 测试连接到: {base_url}")
    
    try:
        # 基本连接测试
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        
        if response.status_code == 200:
            print(f"    远程服务器连接成功")
            
            # 解析模型列表
            models_data = response.json()
            models = [model.get('name', '') for model in models_data.get('models', [])]
            
            print(f"    远程服务器有 {len(models)} 个模型")
            if len(models) <= 5:
                for model in models:
                    print(f"      - {model}")
            else:
                for model in models[:3]:
                    print(f"      - {model}")
                print(f"      - ... 还有 {len(models) - 3} 个模型")
            
            return True
        else:
            print(f"    连接失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print(f"    连接超时")
        print(f"   检查: 服务器地址和端口是否正确")
        return False
    except requests.exceptions.ConnectionError:
        print(f"    连接错误")
        print(f"   检查: 网络连接和防火墙设置")
        return False
    except Exception as e:
        print(f"    连接异常: {e}")
        return False

def test_specific_models(base_url, code_model, embed_model):
    """测试特定模型"""
    print(f"\n 测试指定模型...")
    
    # 测试代码模型
    print(f"💻 测试代码模型: {code_model}")
    try:
        chat_request = {
            "model": code_model,
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False
        }
        
        response = requests.post(
            f"{base_url}/api/chat",
            json=chat_request,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"    代码模型响应正常")
        else:
            print(f"    代码模型失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"    代码模型测试异常: {e}")
        return False
    
    # 测试嵌入模型
    print(f"\n🔤 测试嵌入模型: {embed_model}")
    try:
        embed_request = {
            "model": embed_model,
            "prompt": "test embedding"
        }
        
        response = requests.post(
            f"{base_url}/api/embeddings",
            json=embed_request,
            timeout=30
        )
        
        if response.status_code == 200:
            embed_data = response.json()
            if 'embedding' in embed_data:
                print(f"    嵌入模型响应正常: {len(embed_data['embedding'])} 维")
                return True
            else:
                print(f"    嵌入响应格式错误")
                return False
        else:
            print(f"    嵌入模型失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"    嵌入模型测试异常: {e}")
        return False

def provide_troubleshooting():
    """提供故障排除建议"""
    print(f"\n 故障排除建议:")
    print("="*50)
    
    print("1. 检查远程服务器:")
    print("   - Ollama是否正在运行: ollama serve")
    print("   - 是否绑定到正确的地址: OLLAMA_HOST=0.0.0.0:11434 ollama serve")
    print("   - 防火墙是否开放11434端口")
    
    print("\n2. 检查网络连接:")
    print("   - ping 远程服务器IP")
    print("   - telnet 远程服务器IP 11434")
    print("   - curl http://远程服务器IP:11434/api/tags")
    
    print("\n3. 检查模型:")
    print("   - 在远程服务器运行: ollama list")
    print("   - 确保模型名称拼写正确")
    print("   - 测试模型: ollama run 模型名")
    
    print("\n4. 检查本地配置:")
    print("   - 重新运行: python setup_remote_only.py")
    print("   - 检查环境变量: env | grep OLLAMA")

def main():
    """主函数"""
    print("🌐 远程Ollama连接检查")
    print("="*50)
    
    # 1. 检查环境变量
    env_vars = check_environment_variables()
    if not env_vars:
        return False
    
    # 2. 快速连接测试
    base_url = env_vars['OLLAMA_BASE_URL']
    if not quick_connection_test(base_url):
        provide_troubleshooting()
        return False
    
    # 3. 测试指定模型
    code_model = env_vars['OLLAMA_CODE_MODEL']
    embed_model = env_vars['OLLAMA_EMBEDDING_MODEL']
    
    if test_specific_models(base_url, code_model, embed_model):
        print(f"\n 远程Ollama连接检查通过！")
        print(f"\n 下一步:")
        print(f"   python test_java_only.py")
        return True
    else:
        print(f"\n 模型测试失败")
        provide_troubleshooting()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
