"""
方法签名解析器
用于从Java方法签名中提取参数类型和其他信息
"""

import re
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class JavaSignatureParser:
    """Java方法签名解析器"""
    
    @staticmethod
    def extract_parameter_types(signature: str) -> List[str]:
        """
        从方法签名中提取参数类型
        
        Args:
            signature: Java方法签名
            
        Returns:
            参数类型列表
        """
        try:
            # 清理签名，移除多余的空格和换行
            signature = re.sub(r'\s+', ' ', signature.strip())
            
            # 查找参数部分
            param_match = re.search(r'\(([^)]*)\)', signature)
            if not param_match:
                return []
            
            param_string = param_match.group(1).strip()
            if not param_string:
                return []
            
            # 解析参数
            parameters = JavaSignatureParser._parse_parameters(param_string)
            
            # 提取类型
            types = []
            for param in parameters:
                param_type = JavaSignatureParser._extract_type_from_parameter(param)
                if param_type:
                    types.append(param_type)
            
            return types
            
        except Exception as e:
            logger.debug(f"解析方法签名失败: {signature}, 错误: {e}")
            return []
    
    @staticmethod
    def _parse_parameters(param_string: str) -> List[str]:
        """
        解析参数字符串，处理泛型和嵌套类型
        
        Args:
            param_string: 参数字符串
            
        Returns:
            参数列表
        """
        parameters = []
        current_param = ""
        bracket_count = 0
        angle_bracket_count = 0
        
        for char in param_string:
            if char == '<':
                angle_bracket_count += 1
                current_param += char
            elif char == '>':
                angle_bracket_count -= 1
                current_param += char
            elif char == '(':
                bracket_count += 1
                current_param += char
            elif char == ')':
                bracket_count -= 1
                current_param += char
            elif char == ',' and bracket_count == 0 and angle_bracket_count == 0:
                # 这是一个参数分隔符
                if current_param.strip():
                    parameters.append(current_param.strip())
                current_param = ""
            else:
                current_param += char
        
        # 添加最后一个参数
        if current_param.strip():
            parameters.append(current_param.strip())
        
        return parameters
    
    @staticmethod
    def _extract_type_from_parameter(parameter: str) -> Optional[str]:
        """
        从参数声明中提取类型
        
        Args:
            parameter: 参数声明，如 "List<String> items" 或 "int count"
            
        Returns:
            类型名称
        """
        try:
            # 移除final关键字
            parameter = re.sub(r'\bfinal\s+', '', parameter)
            
            # 分割参数声明，最后一部分是参数名
            parts = parameter.strip().split()
            if len(parts) < 2:
                return None
            
            # 类型是除了最后一个部分之外的所有部分
            type_parts = parts[:-1]
            param_type = ' '.join(type_parts)
            
            # 清理类型名称
            param_type = param_type.strip()
            
            return param_type
            
        except Exception as e:
            logger.debug(f"提取参数类型失败: {parameter}, 错误: {e}")
            return None
    
    @staticmethod
    def extract_all_types_from_signature(signature: str) -> List[str]:
        """
        从方法签名中提取所有类型（包括返回类型和参数类型）
        
        Args:
            signature: Java方法签名
            
        Returns:
            所有类型的列表
        """
        types = []
        
        # 提取返回类型
        return_type = JavaSignatureParser.extract_return_type(signature)
        if return_type and return_type != 'void':
            types.append(return_type)
        
        # 提取参数类型
        param_types = JavaSignatureParser.extract_parameter_types(signature)
        types.extend(param_types)
        
        # 提取泛型中的类型
        all_nested_types = []
        for type_name in types:
            nested_types = JavaSignatureParser._extract_nested_types(type_name)
            all_nested_types.extend(nested_types)
        
        types.extend(all_nested_types)
        
        # 去重并过滤基本类型
        unique_types = []
        seen = set()
        primitive_types = {'int', 'long', 'double', 'float', 'boolean', 'char', 'byte', 'short', 'void'}
        
        for type_name in types:
            clean_type = JavaSignatureParser._clean_type_name(type_name)
            if clean_type and clean_type not in seen and clean_type not in primitive_types:
                unique_types.append(clean_type)
                seen.add(clean_type)
        
        return unique_types
    
    @staticmethod
    def extract_return_type(signature: str) -> Optional[str]:
        """
        从方法签名中提取返回类型
        
        Args:
            signature: Java方法签名
            
        Returns:
            返回类型
        """
        try:
            # 清理签名
            signature = re.sub(r'\s+', ' ', signature.strip())
            
            # 匹配方法签名模式
            # 匹配: [修饰符] 返回类型 方法名(参数)
            pattern = r'(?:public|private|protected|static|final|abstract|synchronized|\s)*\s*(\S+(?:<[^>]*>)?(?:\[\])*)\s+\w+\s*\('
            
            match = re.search(pattern, signature)
            if match:
                return_type = match.group(1).strip()
                return return_type
            
            return None
            
        except Exception as e:
            logger.debug(f"提取返回类型失败: {signature}, 错误: {e}")
            return None
    
    @staticmethod
    def _extract_nested_types(type_name: str) -> List[str]:
        """
        从泛型类型中提取嵌套的类型
        
        Args:
            type_name: 类型名称，如 "List<String>" 或 "Map<String, Integer>"
            
        Returns:
            嵌套类型列表
        """
        nested_types = []
        
        # 查找泛型参数
        generic_match = re.search(r'<([^>]+)>', type_name)
        if generic_match:
            generic_params = generic_match.group(1)
            
            # 解析泛型参数
            params = JavaSignatureParser._parse_generic_parameters(generic_params)
            for param in params:
                clean_param = JavaSignatureParser._clean_type_name(param)
                if clean_param:
                    nested_types.append(clean_param)
                    # 递归处理嵌套的泛型
                    nested_types.extend(JavaSignatureParser._extract_nested_types(param))
        
        return nested_types
    
    @staticmethod
    def _parse_generic_parameters(generic_params: str) -> List[str]:
        """
        解析泛型参数字符串
        
        Args:
            generic_params: 泛型参数字符串，如 "String, Integer" 或 "String, List<Integer>"
            
        Returns:
            参数列表
        """
        params = []
        current_param = ""
        angle_bracket_count = 0
        
        for char in generic_params:
            if char == '<':
                angle_bracket_count += 1
                current_param += char
            elif char == '>':
                angle_bracket_count -= 1
                current_param += char
            elif char == ',' and angle_bracket_count == 0:
                if current_param.strip():
                    params.append(current_param.strip())
                current_param = ""
            else:
                current_param += char
        
        # 添加最后一个参数
        if current_param.strip():
            params.append(current_param.strip())
        
        return params
    
    @staticmethod
    def _clean_type_name(type_name: str) -> str:
        """
        清理类型名称，移除数组标记和通配符
        
        Args:
            type_name: 原始类型名称
            
        Returns:
            清理后的类型名称
        """
        if not type_name:
            return ""
        
        # 移除数组标记
        type_name = re.sub(r'\[\]', '', type_name)
        
        # 移除泛型参数
        type_name = re.sub(r'<.*>', '', type_name)
        
        # 移除通配符
        type_name = re.sub(r'\?\s*(?:extends|super)\s+', '', type_name)
        type_name = re.sub(r'\?', '', type_name)
        
        # 移除包名前缀（如果有的话）
        if '.' in type_name:
            type_name = type_name.split('.')[-1]
        
        return type_name.strip()
    
    @staticmethod
    def extract_method_name(signature: str) -> Optional[str]:
        """
        从方法签名中提取方法名
        
        Args:
            signature: Java方法签名
            
        Returns:
            方法名
        """
        try:
            # 查找方法名模式
            pattern = r'\b(\w+)\s*\('
            match = re.search(pattern, signature)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.debug(f"提取方法名失败: {signature}, 错误: {e}")
            return None
