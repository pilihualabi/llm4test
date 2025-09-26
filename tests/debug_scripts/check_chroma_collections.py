#!/usr/bin/env python3
"""
检查ChromaDB集合详细信息
"""

import sys
import os
import chromadb
from pathlib import Path

def check_all_collections():
    """检查所有ChromaDB集合"""
    print(" 检查所有ChromaDB集合")
    print("=" * 60)
    
    try:
        # 连接到ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # 获取所有集合
        collections = client.list_collections()
        print(f" 找到 {len(collections)} 个集合:")
        
        for collection in collections:
            print(f"\n 集合: {collection.name}")
            print(f"    文档数量: {collection.count()}")
            
            # 获取集合元数据
            try:
                metadata = collection.metadata
                if metadata:
                    print(f"    元数据: {metadata}")
                
                # 尝试获取一个文档来检查维度
                if collection.count() > 0:
                    results = collection.peek(limit=1)
                    if results and 'embeddings' in results and results['embeddings']:
                        embedding = results['embeddings'][0]
                        if embedding:
                            dimension = len(embedding)
                            print(f"   📏 嵌入维度: {dimension}")
                            print(f"    前3个值: {embedding[:3]}")
                        else:
                            print("     嵌入为空")
                    else:
                        print("     无法获取嵌入数据")
                        
                    # 获取一些文档ID
                    try:
                        sample_results = collection.get(limit=3)
                        if sample_results and 'ids' in sample_results:
                            print(f"    示例文档ID: {sample_results['ids'][:3]}")
                    except Exception as e:
                        print(f"     获取文档ID失败: {e}")
                        
            except Exception as e:
                print(f"    获取集合详情失败: {e}")
                
    except Exception as e:
        print(f" 连接ChromaDB失败: {e}")

def check_specific_collection(collection_name: str):
    """检查特定集合的详细信息"""
    print(f"\n 检查集合: {collection_name}")
    print("=" * 60)
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        
        try:
            collection = client.get_collection(collection_name)
            print(f" 集合存在")
            print(f" 文档数量: {collection.count()}")
            
            # 获取所有文档
            if collection.count() > 0:
                all_results = collection.get()
                
                if all_results:
                    print(f" 文档详情:")
                    
                    # 检查嵌入维度
                    if 'embeddings' in all_results and all_results['embeddings']:
                        embeddings = all_results['embeddings']
                        dimensions = [len(emb) if emb else 0 for emb in embeddings]
                        unique_dimensions = set(dimensions)
                        print(f"   📏 嵌入维度: {unique_dimensions}")
                        
                        if len(unique_dimensions) > 1:
                            print(f"     维度不一致！详情: {dict(zip(all_results['ids'], dimensions))}")
                    
                    # 检查元数据
                    if 'metadatas' in all_results and all_results['metadatas']:
                        metadata_types = set()
                        for metadata in all_results['metadatas']:
                            if metadata and 'type' in metadata:
                                metadata_types.add(metadata['type'])
                        print(f"    元数据类型: {metadata_types}")
                    
                    # 显示前几个文档
                    print(f"    前3个文档:")
                    for i in range(min(3, len(all_results['ids']))):
                        doc_id = all_results['ids'][i]
                        content = all_results['documents'][i] if 'documents' in all_results else "无内容"
                        metadata = all_results['metadatas'][i] if 'metadatas' in all_results else {}
                        embedding_dim = len(all_results['embeddings'][i]) if 'embeddings' in all_results and all_results['embeddings'][i] else 0
                        
                        print(f"      {i+1}. ID: {doc_id}")
                        print(f"         内容: {content[:50]}...")
                        print(f"         元数据: {metadata}")
                        print(f"         嵌入维度: {embedding_dim}")
            else:
                print("📭 集合为空")
                
        except Exception as e:
            print(f" 获取集合失败: {e}")
            
    except Exception as e:
        print(f" 连接ChromaDB失败: {e}")

def delete_problematic_collections():
    """删除有问题的集合"""
    print(f"\n🗑  删除有问题的集合")
    print("=" * 60)
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        
        for collection in collections:
            try:
                # 检查集合是否有维度问题
                if collection.count() > 0:
                    results = collection.peek(limit=1)
                    if results and 'embeddings' in results and results['embeddings']:
                        embedding = results['embeddings'][0]
                        if embedding:
                            dimension = len(embedding)
                            # 如果维度不是1024，删除集合
                            if dimension != 1024:
                                print(f"🗑  删除维度不匹配的集合: {collection.name} (维度: {dimension})")
                                client.delete_collection(collection.name)
                            else:
                                print(f" 保留正确维度的集合: {collection.name} (维度: {dimension})")
                        else:
                            print(f"🗑  删除空嵌入的集合: {collection.name}")
                            client.delete_collection(collection.name)
                    else:
                        print(f"🗑  删除无嵌入数据的集合: {collection.name}")
                        client.delete_collection(collection.name)
                else:
                    print(f"🗑  删除空集合: {collection.name}")
                    client.delete_collection(collection.name)
                    
            except Exception as e:
                print(f" 处理集合 {collection.name} 失败: {e}")
                
    except Exception as e:
        print(f" 删除操作失败: {e}")

def main():
    """主函数"""
    print(" ChromaDB集合检查工具")
    print("=" * 80)
    
    # 1. 检查所有集合
    check_all_collections()
    
    # 2. 检查特定集合
    check_specific_collection("java_code_context")
    
    # 3. 询问是否删除有问题的集合
    print(f"\n❓ 是否删除有维度问题的集合？(y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        delete_problematic_collections()
        print(f"\n 清理完成，重新检查:")
        check_all_collections()
    else:
        print(f"  跳过清理")
    
    print("\n" + "=" * 80)
    print(" 检查完成")

if __name__ == "__main__":
    main()
