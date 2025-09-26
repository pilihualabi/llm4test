"""
远程Ollama配置
支持自定义Ollama服务器地址和嵌入模型
"""

import os
from typing import Optional

class RemoteOllamaConfig:
    """远程Ollama配置管理"""
    
    def __init__(self):
        # 默认配置
        self.default_base_url = "http://localhost:11434"
        self.default_embedding_model = "qwen3-embedding:latest"
        self.default_code_model = "qwen3:8b"
        self.default_fix_model = "qwen3:8b"
    
    def get_base_url(self) -> str:
        """获取Ollama服务器地址"""
        return os.getenv("OLLAMA_BASE_URL", self.default_base_url)
    
    def get_embedding_model(self) -> str:
        """获取嵌入模型名称"""
        return os.getenv("OLLAMA_EMBEDDING_MODEL", self.default_embedding_model)
    
    def get_code_model(self) -> str:
        """获取代码生成模型"""
        return os.getenv("OLLAMA_CODE_MODEL", self.default_code_model)
    
    def get_fix_model(self) -> str:
        """获取代码修复模型"""
        return os.getenv("OLLAMA_FIX_MODEL", self.default_fix_model)
    
    def get_request_timeout(self) -> int:
        """获取请求超时时间"""
        return int(os.getenv("OLLAMA_REQUEST_TIMEOUT", "120"))  # 增加到2分钟
    
    def set_remote_config(self, base_url: str, embedding_model: str, 
                         code_model: Optional[str] = None, 
                         fix_model: Optional[str] = None):
        """设置远程配置"""
        os.environ["OLLAMA_BASE_URL"] = base_url
        os.environ["OLLAMA_EMBEDDING_MODEL"] = embedding_model
        
        if code_model:
            os.environ["OLLAMA_CODE_MODEL"] = code_model
        if fix_model:
            os.environ["OLLAMA_FIX_MODEL"] = fix_model
    
    def get_api_endpoints(self) -> dict:
        """获取API端点"""
        base_url = self.get_base_url()
        return {
            "tags": f"{base_url}/api/tags",
            "chat": f"{base_url}/api/chat", 
            "embeddings": f"{base_url}/api/embeddings",
            "generate": f"{base_url}/api/generate"
        }
    
    def print_config(self):
        """打印当前配置"""
        print(" 当前Ollama配置:")
        print(f"   📍 服务器地址: {self.get_base_url()}")
        print(f"   🔤 嵌入模型: {self.get_embedding_model()}")
        print(f"   💻 代码模型: {self.get_code_model()}")
        print(f"    修复模型: {self.get_fix_model()}")

# 全局配置实例
remote_config = RemoteOllamaConfig()
