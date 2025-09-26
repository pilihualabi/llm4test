import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from typing import Dict, Any, Optional, List
import logging
import time
import json
import re

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for communicating with Ollama API with robust error handling and retries."""
    
    def __init__(
        self,
        base_url: str,
        code_model: str,
        non_code_model: str,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        timeout: int = 60,
        json_logger=None,
        conversation_logger=None
    ):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: The base URL for the Ollama API
            code_model: The model to use for code-related tasks
            non_code_model: The model to use for non-code tasks (e.g. scenarios)
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            timeout: Request timeout in seconds
            json_logger: Optional TestGenerationLogger instance for tracking metrics
            conversation_logger: Optional ConversationLogger instance for tracking conversations
        """
        self.base_url = base_url
        self.code_model = code_model
        self.non_code_model = non_code_model
        self.max_retries = max_retries
        self.timeout = timeout
        # 增加重试间隔，给模型更多时间响应
        self.retry_delay = max(retry_delay, 10.0)  # 至少10秒重试间隔
        self.json_logger = json_logger
        self.conversation_logger = conversation_logger
        self.request_count = 0
        self.total_response_time = 0.0

    def _is_reasoning_model(self, model: str) -> bool:
        """
        Check if the given model is a reasoning model that supports the 'think' parameter.
        
        Args:
            model: Model name to check
            
        Returns:
            True if the model is a reasoning model (currently deepseek-r1 variants)
        """
        return model.startswith("deepseek-r1")
    
    def _clean_code_content(self, content: str) -> str:
        """
        Clean code content by removing Markdown formatting and other artifacts.
        
        Args:
            content: Raw content from LLM
            
        Returns:
            Cleaned code content
        """
        # 移除Markdown代码块标记
        content = content.replace('```java', '').replace('```', '')
        
        # 移除think标签
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        
        # 移除参数化测试相关的导入（避免编译错误）
        content = re.sub(r'import org\.junit\.jupiter\.params\.[^;]+;', '', content)
        content = re.sub(r'@ParameterizedTest[^}]*}', '', content, flags=re.DOTALL)
        content = re.sub(r'@ValueSource[^}]*}', '', content, flags=re.DOTALL)
        
        # 移除多余的空行
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line or (cleaned_lines and cleaned_lines[-1]):  # 保留非空行和必要的空行
                cleaned_lines.append(line)
        
        # 重新组合
        cleaned_content = '\n'.join(cleaned_lines)
        
        # 确保以package或import开头
        if not cleaned_content.startswith('package') and not cleaned_content.startswith('import'):
            # 查找第一个有效的Java代码行
            for line in lines:
                line = line.strip()
                if line.startswith('package') or line.startswith('import') or line.startswith('public class'):
                    start_idx = content.find(line)
                    if start_idx != -1:
                        cleaned_content = content[start_idx:]
                        break
        
        return cleaned_content.strip()

    def _make_request(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        is_code_task: bool = True,
        attempt: int = 1
    ) -> str:
        """
        Make a request to Ollama with retries and error handling.
        
        Args:
            messages: List of message dictionaries
            model: Optional model override
            schema: Optional JSON schema for structured output
            is_code_task: Whether this is a code-related task (uses code_model) or not (uses non_code_model)
            attempt: Current attempt number (for retries)
            
        Returns:
            The response content as a string
            
        Raises:
            RuntimeError: If all retries fail
        """
        # Start timing this request
        request_start_time = time.time()
        
        # Choose model based on task type if not explicitly provided
        # For non-code tasks, use code_model as fallback since non_code_model might be embedding model
        chosen_model = model or (self.code_model if is_code_task else self.code_model)
        
        # Check if this is a reasoning model
        is_reasoning = self._is_reasoning_model(chosen_model)
        
        base_payload = {
            "model": chosen_model,
            "prompt": messages[-1]["content"] if messages else "",  # 使用最后一条消息的内容作为prompt
            "stream": False,
            "options": {
                "num_ctx": 32000,
            }
        }
        
        # Enable reasoning for reasoning models
        if is_reasoning:
            base_payload["think"] = True
            logger.info(f"Using reasoning model {chosen_model} with think parameter enabled")
        
        # Add schema if provided (only for structured requests)
        if schema:
            payload = {**base_payload, "format": schema}
        else:
            payload = base_payload
        
        try:
            # 记录用户消息到对话记录器
            if self.conversation_logger:
                user_content = messages[-1]["content"] if messages else ""
                self.conversation_logger.add_message(
                    role="user",
                    content=user_content,
                    model=chosen_model
                )
            
            # 使用正确的Ollama API端点
            api_url = f"{self.base_url}/api/generate"
            
            # 添加调试信息
            logger.debug(f"发送请求到: {api_url}")
            logger.debug(f"请求内容: {payload}")
            
            resp = requests.post(api_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            content = resp.json().get("response", "")
            
            # 清理代码内容，移除Markdown标记
            if is_code_task and content:
                content = self._clean_code_content(content)
            
            # 记录助手响应到对话记录器
            if self.conversation_logger:
                response_time = time.time() - request_start_time
                self.conversation_logger.add_message(
                    role="assistant",
                    content=content,
                    model=chosen_model,
                    duration=response_time
                )
            
            # Calculate response time for this request
            response_time = time.time() - request_start_time
            self.total_response_time += response_time
            
            # Count every request (including retries)
            self.request_count += 1
            
            # Check if response was truncated
            if content and content.endswith('...'):
                logger.warning("Response appears to be truncated, retrying with larger context...")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    return self._make_request(messages, model, schema, is_code_task, attempt + 1)
                else:
                    raise RuntimeError("Response was truncated and max retries exceeded")
            
            # If we got an empty response and have retries left, try again
            if not content and attempt < self.max_retries:
                logger.debug(f"Empty response received, retrying (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                return self._make_request(messages, model, schema, is_code_task, attempt + 1)
            
            return content
            
        except ConnectionError as e:
            # Calculate response time even for failed requests
            response_time = time.time() - request_start_time
            self.total_response_time += response_time
            
            # Count failed requests too
            self.request_count += 1
            
            if attempt < self.max_retries:
                logger.debug(f"Connection failed, retrying (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                return self._make_request(messages, model, schema, is_code_task, attempt + 1)
            else:
                raise RuntimeError() from e
        except (HTTPError, Timeout) as e:
            # Calculate response time even for failed requests
            response_time = time.time() - request_start_time
            self.total_response_time += response_time
            
            # Count failed requests too
            self.request_count += 1
            
            if attempt < self.max_retries:
                logger.debug(f"Request failed, retrying (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                return self._make_request(messages, model, schema, is_code_task, attempt + 1)
            else:
                raise RuntimeError() from e

    def call_structured(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        model: Optional[str] = None,
        is_code_task: bool = True
    ) -> str:
        """
        Make a structured request to Ollama with schema validation.
        
        Args:
            messages: List of message dictionaries
            schema: JSON schema for structured output
            model: Optional model override
            is_code_task: Whether this is a code-related task (uses code_model) or not (uses non_code_model)
            
        Returns:
            The response content as a string
            
        Raises:
            RuntimeError: If all retries fail
        """
        attempt = 1
        while attempt <= self.max_retries:
            try:
                content = self._make_request(messages, model, schema, is_code_task)
                
                # First try to parse as JSON
                try:
                    json_content = json.loads(content)
                    # If we get here, the JSON is valid
                    return content
                except json.JSONDecodeError as e:
                    if attempt >= self.max_retries:
                        raise RuntimeError(f"Failed to get valid JSON after {self.max_retries} attempts") from e
                    time.sleep(self.retry_delay)
                    attempt += 1
                    continue
                        
            except Exception as e:
                if attempt >= self.max_retries:
                    raise RuntimeError(f"Failed after {self.max_retries} attempts") from e
                time.sleep(self.retry_delay)
                attempt += 1
                continue

    def call_unstructured(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        is_code_task: bool = True
    ) -> str:
        """
        Make an unstructured request to Ollama.
        
        Args:
            messages: List of message dictionaries
            model: Optional model override
            is_code_task: Whether this is a code-related task (uses code_model) or not (uses non_code_model)
            
        Returns:
            The response content as a string
            
        Raises:
            RuntimeError: If all retries fail
        """
        return self._make_request(messages, model, None, is_code_task)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current LLM metrics.
        
        Returns:
            Dictionary with request count and total response time
        """
        return {
            "request_count": self.request_count,
            "total_response_time": self.total_response_time
        } 