#!/usr/bin/env python3
"""
生成纯代码的脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def generate_pure_code():
    """生成纯代码"""
    print(" 生成纯代码")
    print("=" * 50)
    
    try:
        # 构建更好的提示
        prompt = """You are a Java test code generator. Generate ONLY the Java test code without any explanations, comments, or thinking process.

Generate a JUnit 5 test class for HashUtilityClass.hashBytes method.

Requirements:
- Package: com.example.pdfcompare.util
- Method: public String hashBytes(byte[] data)
- Use JUnit 5 annotations
- Include comprehensive test cases
- Follow Java naming conventions
- Add necessary imports

Generate the complete test class starting with package declaration:"""
        
        print("1. 发送提示到LLM...")
        
        # 调用LLM
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen3:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 降低温度以获得更确定的输出
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            generated_code = data.get('response', '').strip()
            
            print(f"2. 代码生成成功，长度: {len(generated_code)} 字符")
            
            # 保存代码
            output_dir = Path("./pure_code_output")
            output_dir.mkdir(exist_ok=True)
            
            test_file = output_dir / "HashUtilityClassTest.java"
            test_file.write_text(generated_code, encoding='utf-8')
            print(f"3. 测试文件已保存: {test_file}")
            
            # 显示代码
            print(f"4. 生成的代码:")
            print("=" * 50)
            print(generated_code)
            print("=" * 50)
            
            return True
        else:
            print(f" 代码生成失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f" 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_pure_code()
