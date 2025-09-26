#!/usr/bin/env python3
"""
Context-Aware Code Generation 模块
"""

from .project_index import (
    ClassIndex, MethodSignature, ConstructorSignature, FieldSignature,
    ProjectIndexDatabase
)
from .static_analyzer import JavaStaticAnalyzer
from .context_generator import (
    ContextAwareGenerator, CoreCodeContext, DependencyContext, 
    ContextAwareTestContext
)
from .package_validator import PackageValidator
from .test_generator import ContextAwareTestGenerator

__all__ = [
    'ClassIndex', 'MethodSignature', 'ConstructorSignature', 'FieldSignature',
    'ProjectIndexDatabase', 'JavaStaticAnalyzer', 'ContextAwareGenerator',
    'CoreCodeContext', 'DependencyContext', 'ContextAwareTestContext',
    'PackageValidator', 'ContextAwareTestGenerator'
]

__version__ = '1.0.0'
