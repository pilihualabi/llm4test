#!/usr/bin/env python3
"""
优化的远程Ollama配置脚本
处理模型加载慢和超时问题
"""

import sys
import requests
import json
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config.remote_ollama_config import remote_config

def test_connection_with_patience(base_url, timeout_seconds=15):
    """耐心地测试连接"""
    print(f"🌐 测试连接到: {base_url}")
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=timeout_seconds)
        if response.status_code == 200:
            models_data = response.json()
            models = [model.get('name', '') for model in models_data.get('models', [])]
            print(f" 连接成功，找到 {len(models)} 个模型")
            return models
        else:
            print(f" 连接失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f" 连接失败: {e}")
        return None

def warm_up_model(base_url, model_name, max_wait_time=120):
    """预热模型（避免首次使用超时）"""
    print(f" 预热模型: {model_name}")
    print("   这可能需要1-2分钟，请耐心等待...")
    
    # 使用简单的generate API进行预热
    warm_up_request = {
        "model": model_name,
        "prompt": "hi",
        "stream": False,
        "options": {
            "num_predict": 5  # 只生成5个token，快速预热
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/generate",
            json=warm_up_request,
            timeout=max_wait_time
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"    模型预热成功 ({elapsed:.1f}秒)")
            return True
        else:
            print(f"    模型预热失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 模型预热超时 (>{max_wait_time}秒)")
        print(f"    模型可能需要更长时间加载，建议在远程服务器上手动预热:")
        print(f"       ollama run {model_name}")
        return False
    except Exception as e:
        print(f"    预热异常: {e}")
        return False

def test_embedding_with_retry(base_url, model_name, max_retries=3):
    """带重试的嵌入测试"""
    print(f"🔤 测试嵌入模型: {model_name}")
    
    for attempt in range(1, max_retries + 1):
        print(f"   尝试 {attempt}/{max_retries}...")
        
        try:
            embed_request = {
                "model": model_name,
                "prompt": "test"
            }
            
            response = requests.post(
                f"{base_url}/api/embeddings",
                json=embed_request,
                timeout=60
            )
            
            if response.status_code == 200:
                embed_data = response.json()
                if 'embedding' in embed_data:
                    embedding = embed_data['embedding']
                    print(f"    嵌入测试成功: {len(embedding)} 维向量")
                    return True
                else:
                    print(f"    嵌入响应格式错误")
                    return False
            else:
                print(f"    嵌入请求失败: {response.status_code}")
                if attempt < max_retries:
                    print(f"   等待3秒后重试...")
                    time.sleep(3)
                else:
                    print(f"   错误信息: {response.text}")
                    return False
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ 请求超时")
            if attempt < max_retries:
                print(f"   等待5秒后重试...")
                time.sleep(5)
            else:
                return False
        except Exception as e:
            print(f"    请求异常: {e}")
            if attempt < max_retries:
                print(f"   等待3秒后重试...")
                time.sleep(3)
            else:
                return False
    
    return False

def test_chat_lightweight(base_url, model_name):
    """轻量级聊天测试"""
    print(f" 测试代码生成模型: {model_name}")
    
    # 使用更短的提示和更少的输出
    lightweight_request = {
        "model": model_name,
        "prompt": "写一个add方法",
        "stream": False,
        "options": {
            "num_predict": 50,  # 限制输出长度
            "temperature": 0.1  # 低温度，更确定性
        }
    }
    
    try:
        print("   发送轻量级测试请求...")
        response = requests.post(
            f"{base_url}/api/generate",
            json=lightweight_request,
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'response' in data:
                content = data['response']
                print(f"    代码生成测试成功，响应长度: {len(content)} 字符")
                if any(keyword in content.lower() for keyword in ['public', 'int', 'add', 'return']):
                    print(f"    包含预期的Java代码关键词")
                return True
            else:
                print(f"    响应格式错误")
                return False
        else:
            print(f"    请求失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 请求超时，模型响应太慢")
        print(f"    建议: 在远程服务器检查模型状态")
        return False
    except Exception as e:
        print(f"    请求异常: {e}")
        return False

def setup_optimized_remote():
    """设置优化的远程配置"""
    print(" 优化的远程Ollama配置")
    print("="*60)
    
    # 从之前的配置中读取信息，或重新输入
    print("检测到您的模型配置:")
    print("🤖 代码生成: qwen3-8b-q4:latest")
    print("🔤 嵌入模型: qwen3-embedding:latest")
    print("🌐 服务器: http://localhost:11434")
    
    confirm = input("\n使用这个配置继续吗? (y/n, 默认y): ").strip().lower()
    if confirm == 'n':
        print("请重新运行 setup_remote_only.py 进行配置")
        return False
    
    base_url = "http://localhost:11434"
    code_model = "qwen3-8b-q4:latest"
    embed_model = "qwen3-embedding:latest"
    
    # 1. 测试基本连接
    models = test_connection_with_patience(base_url)
    if not models:
        return False
    
    # 2. 预热嵌入模型（通常更快）
    print(f"\n 预热嵌入模型...")
    if warm_up_model(base_url, embed_model, max_wait_time=60):
        # 3. 测试嵌入功能
        embed_success = test_embedding_with_retry(base_url, embed_model)
    else:
        print("    嵌入模型预热失败，跳过嵌入测试")
        embed_success = False
    
    # 4. 预热代码生成模型
    print(f"\n 预热代码生成模型...")
    if warm_up_model(base_url, code_model, max_wait_time=120):
        # 5. 测试代码生成功能
        chat_success = test_chat_lightweight(base_url, code_model)
    else:
        print("    代码模型预热失败，跳过聊天测试")
        chat_success = False
    
    # 6. 评估结果
    if embed_success and chat_success:
        status = "完全正常"
        config_type = "full"
    elif embed_success:
        status = "嵌入正常，代码生成需要优化"
        config_type = "embed_only"
    elif chat_success:
        status = "代码生成正常，嵌入需要优化"
        config_type = "chat_only"
    else:
        status = "需要排查问题"
        config_type = "needs_fix"
    
    print(f"\n 测试结果总结:")
    print(f"   🔤 嵌入功能: {'' if embed_success else ''}")
    print(f"   💻 代码生成: {'' if chat_success else ''}")
    print(f"    状态: {status}")
    
    # 7. 保存配置
    if config_type != "needs_fix":
        save_optimized_config(base_url, code_model, embed_model, config_type)
        return True
    else:
        provide_troubleshooting_guide()
        return False

def save_optimized_config(base_url, code_model, embed_model, config_type):
    """保存优化配置"""
    print(f"\n 保存优化配置...")
    
    # 设置环境变量
    remote_config.set_remote_config(
        base_url=base_url,
        embedding_model=embed_model,
        code_model=code_model,
        fix_model=code_model
    )
    
    # 保存配置文件
    config_content = f'''# 优化的远程Ollama配置
# 配置类型: {config_type}
# 生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}

export OLLAMA_BASE_URL="{base_url}"
export OLLAMA_CODE_MODEL="{code_model}"
export OLLAMA_EMBEDDING_MODEL="{embed_model}"
export OLLAMA_FIX_MODEL="{code_model}"

# 性能优化设置
export OLLAMA_REQUEST_TIMEOUT="120"  # 请求超时时间
export OLLAMA_EMBED_TIMEOUT="60"     # 嵌入超时时间

echo " 优化的Ollama环境已设置 (配置类型: {config_type})"
echo "   服务器: $OLLAMA_BASE_URL"
echo "   代码模型: $OLLAMA_CODE_MODEL"
echo "   嵌入模型: $OLLAMA_EMBEDDING_MODEL"

# 预热建议
echo " 首次使用建议预热模型:"
echo "   curl -X POST \\$OLLAMA_BASE_URL/api/generate -d '{\\\"model\\\":\\\"{code_model}\\\",\\\"prompt\\\":\\\"hi\\\",\\\"stream\\\":false}'"
'''
    
    env_file = Path("optimized_ollama_env.sh")
    env_file.write_text(config_content)
    
    print(f" 优化配置已保存到: {env_file}")
    
    # 提供使用建议
    print(f"\n 使用建议:")
    if config_type == "full":
        print(" 所有功能正常，可以开始RAG开发")
        print("1. source optimized_ollama_env.sh")
        print("2. python test_java_only.py")
    elif config_type == "embed_only":
        print(" 代码生成模型响应慢，建议:")
        print("1. 在远程服务器预热: ollama run qwen3-8b-q4:latest")
        print("2. source optimized_ollama_env.sh")
        print("3. python test_java_only.py")
    elif config_type == "chat_only":
        print(" 嵌入模型有问题，建议:")
        print("1. 检查嵌入模型: ollama run qwen3-embedding:latest")
        print("2. source optimized_ollama_env.sh")
        print("3. python test_java_only.py")

def provide_troubleshooting_guide():
    """提供故障排除指南"""
    print(f"\n 故障排除指南:")
    print("="*50)
    
    print("1. 远程服务器操作:")
    print("   # 检查Ollama状态")
    print("   ps aux | grep ollama")
    print("   ")
    print("   # 重启Ollama (如果需要)")
    print("   pkill ollama")
    print("   OLLAMA_HOST=0.0.0.0:11434 ollama serve")
    print("   ")
    print("   # 预热模型")
    print("   ollama run qwen3-8b-q4:latest")
    print("   ollama run qwen3-embedding:latest")
    
    print("\n2. 性能优化:")
    print("   # 检查GPU/CPU使用情况")
    print("   nvidia-smi  # 如果使用GPU")
    print("   htop        # 检查CPU使用")
    print("   ")
    print("   # 调整模型参数 (在Modelfile中)")
    print("   PARAMETER num_ctx 2048      # 减少上下文长度")
    print("   PARAMETER num_predict 100   # 限制输出长度")
    
    print("\n3. 网络优化:")
    print("   # 增加超时时间")
    print("   export OLLAMA_REQUEST_TIMEOUT=180")
    print("   ")
    print("   # 检查网络延迟")
    print("   ping 远程服务器IP")

def main():
    """主函数"""
    print(" 远程Ollama优化配置助手")
    print("专门解决模型响应慢和超时问题")
    print("="*60)
    
    if setup_optimized_remote():
        print(f"\n 优化配置完成！")
        return True
    else:
        print(f"\n 配置失败，请参考故障排除指南")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
