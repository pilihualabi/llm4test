#!/usr/bin/env python3
"""
模型预热脚本
解决首次使用模型时的加载延迟问题
"""

import requests
import time
import sys

def warm_up_model(base_url, model_name, test_type="generate"):
    """预热指定模型"""
    print(f" 预热模型: {model_name} ({test_type})")
    
    if test_type == "generate":
        # 代码生成模型预热
        request_data = {
            "model": model_name,
            "prompt": "hi",
            "stream": False,
            "options": {
                "num_predict": 3,
                "temperature": 0.1
            }
        }
        endpoint = f"{base_url}/api/generate"
        
    elif test_type == "embedding":
        # 嵌入模型预热
        request_data = {
            "model": model_name,
            "prompt": "test"
        }
        endpoint = f"{base_url}/api/embeddings"
    
    else:
        print(f"    未知的测试类型: {test_type}")
        return False
    
    try:
        print(f"   发送预热请求...")
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            json=request_data,
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"    预热成功 ({elapsed:.1f}秒)")
            return True
        else:
            print(f"    预热失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 预热超时 (>120秒)")
        return False
    except Exception as e:
        print(f"    预热异常: {e}")
        return False

def main():
    """主函数"""
    print(" 模型预热助手")
    print("="*40)
    
    base_url = "http://localhost:11434"
    
    # 预热模型列表
    models_to_warm = [
        ("qwen3-embedding:latest", "embedding"),
        ("qwen3-8b-q4:latest", "generate"),
    ]
    
    success_count = 0
    
    for model_name, test_type in models_to_warm:
        print(f"\n{'-'*40}")
        if warm_up_model(base_url, model_name, test_type):
            success_count += 1
        
        # 模型间等待2秒
        time.sleep(2)
    
    print(f"\n{'='*40}")
    print(f"预热完成: {success_count}/{len(models_to_warm)} 成功")
    
    if success_count == len(models_to_warm):
        print(" 所有模型预热成功！现在可以正常使用了。")
        return True
    else:
        print(" 部分模型预热失败，可能会影响使用体验。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
