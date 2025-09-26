"""
ChromaDB向量存储系统
集成Ollama嵌入模型，提供代码语义搜索功能
"""

import requests
import chromadb
import logging
import time
from typing import List, Dict, Optional, Any
from pathlib import Path
import hashlib
import json

from config.remote_ollama_config import remote_config

logger = logging.getLogger(__name__)

class OllamaEmbeddingFunction:
    """Ollama嵌入函数，集成到ChromaDB中"""
    
    def __init__(self, model_name: str = None, base_url: str = None):
        self.model_name = model_name or remote_config.get_embedding_model()
        self.base_url = base_url or remote_config.get_base_url()
        # ChromaDB需要的属性
        self._name = f"ollama_{self.model_name}"

    def name(self) -> str:
        """返回嵌入函数名称"""
        return self._name
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        """生成嵌入向量"""
        embeddings = []
        
        for text in input:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'embedding' in data:
                        embeddings.append(data['embedding'])
                    else:
                        logger.error(f"嵌入响应格式错误: {data}")
                        embeddings.append([0.0] * 768)  # 默认768维零向量
                else:
                    logger.error(f"嵌入请求失败: {response.status_code}")
                    embeddings.append([0.0] * 768)
                    
            except Exception as e:
                logger.error(f"嵌入生成异常: {e}")
                embeddings.append([0.0] * 768)
        
        return embeddings

class CodeVectorStore:
    """代码向量存储系统"""
    
    def __init__(self, collection_name: str = "java_code_context", 
                 persist_directory: str = "./chroma_db"):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        
        # 初始化嵌入函数
        self.embedding_function = OllamaEmbeddingFunction()
        
        # 尝试获取现有集合，如果不存在则创建新的
        try:
            self.collection = self.client.get_collection(name=collection_name)

            #  检查嵌入维度兼容性
            if self.collection.count() > 0:
                try:
                    # 测试嵌入维度兼容性
                    test_embedding = self.embedding_function(["test"])
                    if test_embedding and len(test_embedding) > 0:
                        current_dim = len(test_embedding[0])
                        logger.info(f"当前嵌入维度: {current_dim}")

                        # 尝试添加测试文档来检查兼容性
                        test_id = "dimension_test_" + str(hash("test"))
                        try:
                            self.collection.add(
                                documents=["test"],
                                ids=[test_id],
                                embeddings=test_embedding
                            )
                            # 如果成功，删除测试文档
                            self.collection.delete(ids=[test_id])
                            logger.info(f"使用现有集合: {collection_name} (文档数: {self.collection.count()})")
                        except Exception as dim_error:
                            if "dimension" in str(dim_error).lower():
                                logger.warning(f"嵌入维度不匹配，重新创建集合: {dim_error}")
                                self._recreate_collection()
                            else:
                                raise dim_error
                    else:
                        logger.info(f"使用现有集合: {collection_name} (文档数: {self.collection.count()})")
                except Exception as test_error:
                    logger.warning(f"嵌入测试失败，使用现有集合: {test_error}")
                    logger.info(f"使用现有集合: {collection_name} (文档数: {self.collection.count()})")
            else:
                logger.info(f"使用现有空集合: {collection_name}")

        except:
            # 集合不存在，创建新的
            self._create_new_collection()

    def _recreate_collection(self):
        """重新创建集合（解决维度不匹配问题）"""
        try:
            # 删除旧集合
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"已删除旧集合: {self.collection_name}")
        except Exception as e:
            logger.debug(f"删除旧集合失败（可能不存在）: {e}")

        # 创建新集合
        self._create_new_collection()

    def _create_new_collection(self):
        """创建新集合"""
        try:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"创建新集合: {self.collection_name} (使用Ollama嵌入)")
        except Exception as e:
            if "already exists" in str(e):
                # 集合已存在，直接获取
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"获取已存在集合: {self.collection_name}")
            else:
                raise e

    def add_code_snippet(self, code: str, metadata: Dict[str, Any]) -> str:
        """
        添加代码片段到向量存储
        
        Args:
            code: 代码内容
            metadata: 元数据（如文件路径、方法名、类名等）
            
        Returns:
            文档ID
        """
        # 生成唯一ID
        doc_id = self._generate_doc_id(code, metadata)
        
        # 添加到集合
        try:
            self.collection.add(
                documents=[code],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.debug(f"添加代码片段: {doc_id}")
            return doc_id
        except Exception as e:
            error_msg = str(e)
            if "dimension" in error_msg.lower():
                logger.error(f"嵌入维度不匹配，尝试重新创建集合: {e}")
                try:
                    self._recreate_collection()
                    # 重试添加
                    self.collection.add(
                        documents=[code],
                        metadatas=[metadata],
                        ids=[doc_id]
                    )
                    logger.info(f"重新创建集合后添加成功: {doc_id}")
                    return doc_id
                except Exception as retry_error:
                    logger.error(f"重试添加失败: {retry_error}")
                    return None
            else:
                logger.error(f"添加代码片段失败: {e}")
                return None
    
    def add_batch_code_snippets(self, codes: List[str], metadatas: List[Dict[str, Any]]) -> List[str]:
        """
        批量添加代码片段
        
        Args:
            codes: 代码列表
            metadatas: 元数据列表
            
        Returns:
            文档ID列表
        """
        if len(codes) != len(metadatas):
            raise ValueError("代码和元数据数量不匹配")
        
        # 生成ID
        doc_ids = [self._generate_doc_id(code, meta) for code, meta in zip(codes, metadatas)]
        
        try:
            self.collection.add(
                documents=codes,
                metadatas=metadatas,
                ids=doc_ids
            )
            logger.info(f"批量添加 {len(codes)} 个代码片段")
            return doc_ids
        except Exception as e:
            logger.error(f"批量添加失败: {e}")
            return []
    
    def search_similar_code(self, query: str, top_k: int = 5, 
                           filter_metadata: Dict[str, Any] = None) -> List[Dict]:
        """
        搜索相似代码片段
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            相似代码片段列表
        """
        try:
            # 构建查询参数
            query_params = {
                "query_texts": [query],
                "n_results": top_k
            }
            
            # 添加过滤条件 - 使用ChromaDB正确的查询语法
            if filter_metadata:
                # 将多个条件转换为$and操作符
                if len(filter_metadata) > 1:
                    where_conditions = []
                    for key, value in filter_metadata.items():
                        where_conditions.append({key: {"$eq": value}})
                    query_params["where"] = {"$and": where_conditions}
                else:
                    # 单个条件
                    key, value = next(iter(filter_metadata.items()))
                    query_params["where"] = {key: {"$eq": value}}
            
            # 执行搜索
            results = self.collection.query(**query_params)
            
            # 格式化结果
            formatted_results = []

            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'content': results['documents'][0][i],  # 修复：使用'content'而不是'code'
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0,
                        'id': results['ids'][0][i] if results['ids'] else None
                    }
                    formatted_results.append(result)
            
            logger.debug(f"搜索到 {len(formatted_results)} 个相似代码片段")
            return formatted_results
            
        except Exception as e:
            error_msg = str(e)
            if "dimension" in error_msg.lower():
                logger.error(f"搜索时嵌入维度不匹配: {e}")
                # 不自动重新创建集合，因为这会丢失数据
                # 建议用户手动处理
                logger.warning("建议使用 --force-reindex 重新索引项目")
            else:
                logger.error(f"搜索失败: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
            return {
                'name': self.collection_name,
                'document_count': count,
                'embedding_model': self.embedding_function.model_name,
                'persist_directory': str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def clear_collection(self):
        """清空集合"""
        try:
            # 删除现有集合
            self.client.delete_collection(name=self.collection_name)
            
            # 重新创建空集合
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"集合已清空: {self.collection_name}")
        except Exception as e:
            logger.error(f"清空集合失败: {e}")
    
    def delete_by_metadata(self, filter_metadata: Dict[str, Any]) -> int:
        """
        根据元数据删除文档
        
        Args:
            filter_metadata: 过滤条件
            
        Returns:
            删除的文档数量
        """
        try:
            # 构建正确的where条件
            where_condition = None
            if filter_metadata:
                if len(filter_metadata) > 1:
                    where_conditions = []
                    for key, value in filter_metadata.items():
                        where_conditions.append({key: {"$eq": value}})
                    where_condition = {"$and": where_conditions}
                else:
                    key, value = next(iter(filter_metadata.items()))
                    where_condition = {key: {"$eq": value}}
            
            # 先查询要删除的文档
            results = self.collection.get(where=where_condition)
            
            if results['ids']:
                # 删除文档
                self.collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                logger.info(f"删除了 {deleted_count} 个文档")
                return deleted_count
            else:
                logger.info("没有找到匹配的文档")
                return 0
                
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return 0
    
    def _generate_doc_id(self, code: str, metadata: Dict[str, Any]) -> str:
        """生成文档ID"""
        # 使用代码内容和关键元数据生成唯一ID
        content = code + json.dumps(metadata, sort_keys=True)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def update_embedding_model(self, model_name: str):
        """更新嵌入模型"""
        self.embedding_function.model_name = model_name
        logger.info(f"嵌入模型已更新为: {model_name}")
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            # 测试基本操作
            stats = self.get_collection_stats()
            
            # 测试嵌入功能
            test_embedding = self.embedding_function(["test connection"])
            
            if test_embedding and len(test_embedding) > 0 and len(test_embedding[0]) > 0:
                logger.info("向量存储连接测试成功")
                return True
            else:
                logger.error("嵌入功能测试失败")
                return False
                
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False

# 注释掉全局实例，避免导入时创建
# code_vector_store = CodeVectorStore()
