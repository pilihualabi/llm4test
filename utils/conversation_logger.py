#!/usr/bin/env python3
"""
对话记录器
保存与大模型的完整对话内容
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid

logger = logging.getLogger(__name__)

class ConversationLogger:
    """对话记录器，保存与大模型的完整对话"""
    
    def __init__(self, output_dir: Path, project_name: str = "unknown"):
        """
        初始化对话记录器
        
        Args:
            output_dir: 输出目录
            project_name: 项目名称
        """
        self.output_dir = Path(output_dir)
        self.project_name = project_name
        self.conversations_dir = self.output_dir / "conversations"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建项目特定的对话目录
        self.project_conversations_dir = self.conversations_dir / project_name
        self.project_conversations_dir.mkdir(exist_ok=True)
        
        # 当前对话ID
        self.current_conversation_id = None
        self.current_conversation = None
    
    def start_conversation(self, 
                          conversation_type: str,
                          target_class: str = None,
                          target_method: str = None,
                          test_style: str = None) -> str:
        """
        开始新的对话
        
        Args:
            conversation_type: 对话类型 (test_generation, compile_fix, runtime_fix)
            target_class: 目标类名
            target_method: 目标方法名
            test_style: 测试风格
            
        Returns:
            对话ID
        """
        # 生成唯一对话ID
        self.current_conversation_id = str(uuid.uuid4())[:8]
        
        # 创建对话记录
        self.current_conversation = {
            "conversation_id": self.current_conversation_id,
            "conversation_type": conversation_type,
            "project_name": self.project_name,
            "target_class": target_class,
            "target_method": target_method,
            "test_style": test_style,
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "metadata": {
                "total_tokens": 0,
                "total_duration": 0.0,
                "success": False,
                "error": None
            }
        }
        
        logger.info(f"开始对话 {self.current_conversation_id} - 类型: {conversation_type}")
        return self.current_conversation_id
    
    def add_message(self, 
                   role: str, 
                   content: str, 
                   model: str = None,
                   duration: float = None,
                   tokens: int = None,
                   metadata: Dict[str, Any] = None):
        """
        添加对话消息
        
        Args:
            role: 消息角色 (user, assistant, system)
            content: 消息内容
            model: 使用的模型名称
            duration: 响应时间
            tokens: 使用的token数量
            metadata: 其他元数据
        """
        if not self.current_conversation:
            logger.warning("没有活跃的对话，无法添加消息")
            return
        
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "model": model,
            "duration": duration,
            "tokens": tokens,
            "metadata": metadata or {}
        }
        
        self.current_conversation["messages"].append(message)
        
        # 更新统计信息
        if duration:
            self.current_conversation["metadata"]["total_duration"] += duration
        if tokens:
            self.current_conversation["metadata"]["total_tokens"] += tokens
        
        logger.debug(f"添加消息 - 角色: {role}, 长度: {len(content)}")
    
    def end_conversation(self, success: bool = True, error: str = None):
        """
        结束当前对话
        
        Args:
            success: 是否成功
            error: 错误信息
        """
        if not self.current_conversation:
            logger.warning("没有活跃的对话，无法结束")
            return
        
        # 更新对话状态
        self.current_conversation["end_time"] = datetime.now().isoformat()
        self.current_conversation["metadata"]["success"] = success
        self.current_conversation["metadata"]["error"] = error
        
        # 计算总持续时间
        start_time = datetime.fromisoformat(self.current_conversation["start_time"])
        end_time = datetime.fromisoformat(self.current_conversation["end_time"])
        total_duration = (end_time - start_time).total_seconds()
        self.current_conversation["metadata"]["total_duration"] = total_duration
        
        # 保存对话记录
        self._save_conversation()
        
        logger.info(f"结束对话 {self.current_conversation_id} - 成功: {success}")
        
        # 清理当前对话
        self.current_conversation = None
        self.current_conversation_id = None
    
    def _save_conversation(self):
        """保存对话记录到文件"""
        if not self.current_conversation:
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conversation_type = self.current_conversation["conversation_type"]
            target_info = ""
            if self.current_conversation["target_class"]:
                target_info = f"_{self.current_conversation['target_class']}"
            if self.current_conversation["target_method"]:
                target_info += f"_{self.current_conversation['target_method']}"
            
            filename = f"{timestamp}_{conversation_type}{target_info}_{self.current_conversation_id}.json"
            filepath = self.project_conversations_dir / filename
            
            # 保存为JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_conversation, f, indent=2, ensure_ascii=False)
            
            logger.info(f"对话记录已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"保存对话记录失败: {e}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取当前对话摘要"""
        if not self.current_conversation:
            return {}
        
        return {
            "conversation_id": self.current_conversation["conversation_id"],
            "type": self.current_conversation["conversation_type"],
            "target": f"{self.current_conversation['target_class']}.{self.current_conversation['target_method']}",
            "messages_count": len(self.current_conversation["messages"]),
            "total_duration": self.current_conversation["metadata"]["total_duration"],
            "total_tokens": self.current_conversation["metadata"]["total_tokens"],
            "success": self.current_conversation["metadata"]["success"]
        }
    
    def list_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        列出最近的对话记录
        
        Args:
            limit: 返回的记录数量限制
            
        Returns:
            对话记录列表
        """
        conversations = []
        
        try:
            # 查找所有对话文件
            conversation_files = list(self.project_conversations_dir.glob("*.json"))
            conversation_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for filepath in conversation_files[:limit]:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        conversation = json.load(f)
                    
                    # 提取摘要信息
                    summary = {
                        "file": filepath.name,
                        "conversation_id": conversation.get("conversation_id"),
                        "type": conversation.get("conversation_type"),
                        "target": f"{conversation.get('target_class', 'N/A')}.{conversation.get('target_method', 'N/A')}",
                        "start_time": conversation.get("start_time"),
                        "duration": conversation.get("metadata", {}).get("total_duration", 0),
                        "success": conversation.get("metadata", {}).get("success", False),
                        "messages_count": len(conversation.get("messages", []))
                    }
                    conversations.append(summary)
                    
                except Exception as e:
                    logger.warning(f"读取对话文件失败 {filepath}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"列出对话记录失败: {e}")
        
        return conversations
    
    def get_conversation_details(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定对话的详细信息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话详情或None
        """
        try:
            # 查找包含该ID的对话文件
            for filepath in self.project_conversations_dir.glob("*.json"):
                if conversation_id in filepath.name:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            logger.error(f"获取对话详情失败: {e}")
        
        return None
    
    def export_conversations(self, output_file: Path, format: str = "json"):
        """
        导出所有对话记录
        
        Args:
            output_file: 输出文件路径
            format: 导出格式 (json, csv)
        """
        try:
            conversations = []
            
            # 读取所有对话文件
            for filepath in self.project_conversations_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        conversation = json.load(f)
                    conversations.append(conversation)
                except Exception as e:
                    logger.warning(f"读取对话文件失败 {filepath}: {e}")
                    continue
            
            if format.lower() == "json":
                # 导出为JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(conversations, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == "csv":
                # 导出为CSV
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # 写入表头
                    writer.writerow([
                        "conversation_id", "type", "target_class", "target_method",
                        "start_time", "end_time", "duration", "success", "messages_count"
                    ])
                    # 写入数据
                    for conv in conversations:
                        writer.writerow([
                            conv.get("conversation_id"),
                            conv.get("conversation_type"),
                            conv.get("target_class"),
                            conv.get("target_method"),
                            conv.get("start_time"),
                            conv.get("end_time"),
                            conv.get("metadata", {}).get("total_duration"),
                            conv.get("metadata", {}).get("success"),
                            len(conv.get("messages", []))
                        ])
            
            logger.info(f"对话记录已导出: {output_file}")
            
        except Exception as e:
            logger.error(f"导出对话记录失败: {e}")
    
    def cleanup_old_conversations(self, days: int = 30):
        """
        清理旧的对话记录
        
        Args:
            days: 保留天数
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_count = 0
            for filepath in self.project_conversations_dir.glob("*.json"):
                if filepath.stat().st_mtime < cutoff_date.timestamp():
                    filepath.unlink()
                    deleted_count += 1
            
            logger.info(f"清理了 {deleted_count} 个旧对话记录")
            
        except Exception as e:
            logger.error(f"清理旧对话记录失败: {e}")
