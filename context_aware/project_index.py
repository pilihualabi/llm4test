#!/usr/bin/env python3
"""
项目级类索引系统
Context-Aware Code Generation 的核心组件
"""

import os
import re
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MethodSignature:
    """方法签名信息"""
    name: str
    access_modifier: str  # public, private, protected, package
    return_type: str
    parameters: List[str]  # ["String name", "int age"]
    exceptions: List[str]  # ["IOException", "SQLException"]
    is_static: bool = False
    is_abstract: bool = False
    is_final: bool = False

@dataclass
class ConstructorSignature:
    """构造器签名信息"""
    access_modifier: str
    parameters: List[str]
    exceptions: List[str]

@dataclass
class FieldSignature:
    """字段签名信息"""
    name: str
    access_modifier: str
    type: str
    is_static: bool = False
    is_final: bool = False

@dataclass
class ClassIndex:
    """类索引信息"""
    simple_name: str
    fully_qualified_name: str
    package: str
    file_path: str
    access_modifier: str
    class_type: str  # class, interface, enum, record, abstract_class
    extends: Optional[str] = None
    implements: List[str] = None
    annotations: List[str] = None
    constructors: List[ConstructorSignature] = None
    methods: List[MethodSignature] = None
    fields: List[FieldSignature] = None
    inner_classes: List[str] = None
    imports: List[str] = None
    last_modified: str = None

    def __post_init__(self):
        if self.implements is None:
            self.implements = []
        if self.annotations is None:
            self.annotations = []
        if self.constructors is None:
            self.constructors = []
        if self.methods is None:
            self.methods = []
        if self.fields is None:
            self.fields = []
        if self.inner_classes is None:
            self.inner_classes = []
        if self.imports is None:
            self.imports = []

class ProjectIndexDatabase:
    """项目索引数据库"""
    
    def __init__(self, db_path: str = "./project_index.db"):
        self.db_path = db_path
        self._init_database()
    
    def has_data(self) -> bool:
        """检查数据库是否有数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM class_index")
                count = cursor.fetchone()[0]
                return count > 0
        except Exception:
            return False

    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 类索引表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS class_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simple_name TEXT NOT NULL,
                    fully_qualified_name TEXT UNIQUE NOT NULL,
                    package TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    access_modifier TEXT NOT NULL,
                    class_type TEXT NOT NULL,
                    extends TEXT,
                    implements TEXT,  -- JSON array
                    annotations TEXT,  -- JSON array
                    inner_classes TEXT,  -- JSON array
                    imports TEXT,  -- JSON array
                    last_modified TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 构造器表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS constructors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_fqn TEXT NOT NULL,
                    access_modifier TEXT NOT NULL,
                    parameters TEXT,  -- JSON array
                    exceptions TEXT,  -- JSON array
                    FOREIGN KEY (class_fqn) REFERENCES class_index (fully_qualified_name)
                )
            ''')
            
            # 方法表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_fqn TEXT NOT NULL,
                    name TEXT NOT NULL,
                    access_modifier TEXT NOT NULL,
                    return_type TEXT NOT NULL,
                    parameters TEXT,  -- JSON array
                    exceptions TEXT,  -- JSON array
                    is_static BOOLEAN DEFAULT FALSE,
                    is_abstract BOOLEAN DEFAULT FALSE,
                    is_final BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (class_fqn) REFERENCES class_index (fully_qualified_name)
                )
            ''')
            
            # 字段表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_fqn TEXT NOT NULL,
                    name TEXT NOT NULL,
                    access_modifier TEXT NOT NULL,
                    type TEXT NOT NULL,
                    is_static BOOLEAN DEFAULT FALSE,
                    is_final BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (class_fqn) REFERENCES class_index (fully_qualified_name)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_class_simple_name ON class_index (simple_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_class_fqn ON class_index (fully_qualified_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_class_package ON class_index (package)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_method_name ON methods (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_field_name ON fields (name)')
            
            conn.commit()

    def insert_class(self, class_data: dict):
        """插入简单的类数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO class_index (
                    simple_name, fully_qualified_name, package, file_path,
                    access_modifier, class_type, extends, implements,
                    annotations, inner_classes, imports, last_modified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                class_data['simple_name'],
                class_data['fully_qualified_name'],
                class_data['package'],
                class_data['file_path'],
                class_data['access_modifier'],
                class_data['class_type'],
                class_data['extends'],
                json.dumps(class_data['implements']),
                json.dumps(class_data['annotations']),
                json.dumps(class_data['inner_classes']),
                json.dumps(class_data['imports']),
                class_data['last_modified']
            ))

            conn.commit()

    def insert_method(self, method_data: dict):
        """插入简单的方法数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO methods (
                    class_fqn, name, access_modifier, return_type,
                    parameters, exceptions, is_static, is_abstract, is_final
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                method_data['class_fqn'],
                method_data['name'],
                method_data['access_modifier'],
                method_data['return_type'],
                json.dumps(method_data['parameters']),
                json.dumps(method_data['exceptions']),
                method_data['is_static'],
                method_data['is_abstract'],
                method_data['is_final']
            ))

            conn.commit()

    def insert_class_index(self, class_index: ClassIndex):
        """插入或更新类索引"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入或更新类信息
            cursor.execute('''
                INSERT OR REPLACE INTO class_index 
                (simple_name, fully_qualified_name, package, file_path, access_modifier, 
                 class_type, extends, implements, annotations, inner_classes, imports, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                class_index.simple_name,
                class_index.fully_qualified_name,
                class_index.package,
                class_index.file_path,
                class_index.access_modifier,
                class_index.class_type,
                class_index.extends,
                json.dumps(class_index.implements),
                json.dumps(class_index.annotations),
                json.dumps(class_index.inner_classes),
                json.dumps(class_index.imports),
                class_index.last_modified
            ))
            
            # 删除旧的构造器、方法、字段
            cursor.execute('DELETE FROM constructors WHERE class_fqn = ?', (class_index.fully_qualified_name,))
            cursor.execute('DELETE FROM methods WHERE class_fqn = ?', (class_index.fully_qualified_name,))
            cursor.execute('DELETE FROM fields WHERE class_fqn = ?', (class_index.fully_qualified_name,))
            
            # 插入构造器
            for constructor in class_index.constructors:
                cursor.execute('''
                    INSERT INTO constructors (class_fqn, access_modifier, parameters, exceptions)
                    VALUES (?, ?, ?, ?)
                ''', (
                    class_index.fully_qualified_name,
                    constructor.access_modifier,
                    json.dumps(constructor.parameters),
                    json.dumps(constructor.exceptions)
                ))
            
            # 插入方法
            for method in class_index.methods:
                cursor.execute('''
                    INSERT INTO methods 
                    (class_fqn, name, access_modifier, return_type, parameters, exceptions, 
                     is_static, is_abstract, is_final)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    class_index.fully_qualified_name,
                    method.name,
                    method.access_modifier,
                    method.return_type,
                    json.dumps(method.parameters),
                    json.dumps(method.exceptions),
                    method.is_static,
                    method.is_abstract,
                    method.is_final
                ))
            
            # 插入字段
            for field in class_index.fields:
                cursor.execute('''
                    INSERT INTO fields (class_fqn, name, access_modifier, type, is_static, is_final)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    class_index.fully_qualified_name,
                    field.name,
                    field.access_modifier,
                    field.type,
                    field.is_static,
                    field.is_final
                ))
            
            conn.commit()
    
    def get_class_by_simple_name(self, simple_name: str) -> List[ClassIndex]:
        """根据简单类名获取类索引"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM class_index WHERE simple_name = ?
            ''', (simple_name,))
            
            results = []
            for row in cursor.fetchall():
                class_index = self._row_to_class_index(row)
                self._load_class_details(class_index)
                results.append(class_index)
            
            return results
    
    def get_class_by_fqn(self, fqn: str) -> Optional[ClassIndex]:
        """根据完全限定名获取类索引"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM class_index WHERE fully_qualified_name = ?
            ''', (fqn,))
            
            row = cursor.fetchone()
            if row:
                class_index = self._row_to_class_index(row)
                self._load_class_details(class_index)
                return class_index
            
            return None
    
    def search_classes_by_package_prefix(self, package_prefix: str) -> List[ClassIndex]:
        """根据包前缀搜索类"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM class_index WHERE package LIKE ?
            ''', (f"{package_prefix}%",))
            
            results = []
            for row in cursor.fetchall():
                class_index = self._row_to_class_index(row)
                self._load_class_details(class_index)
                results.append(class_index)
            
            return results

    def get_class_info(self, fqn: str) -> Optional[Dict]:
        """获取类的详细信息，包括源代码"""
        class_index = self.get_class_by_fqn(fqn)
        if not class_index:
            return None

        # 读取源代码文件
        source_code = ""
        if class_index.file_path and os.path.exists(class_index.file_path):
            try:
                with open(class_index.file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
            except Exception as e:
                logger.warning(f"读取源代码失败: {class_index.file_path}, {e}")

        return {
            'fully_qualified_name': class_index.fully_qualified_name,
            'simple_name': class_index.simple_name,
            'package_name': class_index.package,
            'file_path': class_index.file_path,
            'source_code': source_code,
            'methods': [asdict(method) for method in class_index.methods],
            'constructors': [asdict(constructor) for constructor in class_index.constructors],
            'fields': [asdict(field) for field in class_index.fields],
            'annotations': class_index.annotations,
            'extends': class_index.extends,
            'implements': class_index.implements
        }

    def get_all_classes(self) -> List[Dict]:
        """获取所有类的基本信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT fully_qualified_name, simple_name, package, file_path
                FROM class_index
            ''')

            results = []
            for row in cursor.fetchall():
                results.append({
                    'fully_qualified_name': row[0],
                    'simple_name': row[1],
                    'package_name': row[2],
                    'file_path': row[3]
                })

            return results

    def _row_to_class_index(self, row) -> ClassIndex:
        """将数据库行转换为ClassIndex对象"""
        return ClassIndex(
            simple_name=row[1],
            fully_qualified_name=row[2],
            package=row[3],
            file_path=row[4],
            access_modifier=row[5],
            class_type=row[6],
            extends=row[7],
            implements=json.loads(row[8]) if row[8] else [],
            annotations=json.loads(row[9]) if row[9] else [],
            inner_classes=json.loads(row[10]) if row[10] else [],
            imports=json.loads(row[11]) if row[11] else [],
            last_modified=row[12]
        )
    
    def _load_class_details(self, class_index: ClassIndex):
        """加载类的详细信息（构造器、方法、字段）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 加载构造器
            cursor.execute('''
                SELECT access_modifier, parameters, exceptions 
                FROM constructors WHERE class_fqn = ?
            ''', (class_index.fully_qualified_name,))
            
            for row in cursor.fetchall():
                constructor = ConstructorSignature(
                    access_modifier=row[0],
                    parameters=json.loads(row[1]) if row[1] else [],
                    exceptions=json.loads(row[2]) if row[2] else []
                )
                class_index.constructors.append(constructor)
            
            # 加载方法
            cursor.execute('''
                SELECT name, access_modifier, return_type, parameters, exceptions, 
                       is_static, is_abstract, is_final
                FROM methods WHERE class_fqn = ?
            ''', (class_index.fully_qualified_name,))
            
            for row in cursor.fetchall():
                method = MethodSignature(
                    name=row[0],
                    access_modifier=row[1],
                    return_type=row[2],
                    parameters=json.loads(row[3]) if row[3] else [],
                    exceptions=json.loads(row[4]) if row[4] else [],
                    is_static=bool(row[5]),
                    is_abstract=bool(row[6]),
                    is_final=bool(row[7])
                )
                class_index.methods.append(method)
            
            # 加载字段
            cursor.execute('''
                SELECT name, access_modifier, type, is_static, is_final
                FROM fields WHERE class_fqn = ?
            ''', (class_index.fully_qualified_name,))
            
            for row in cursor.fetchall():
                field = FieldSignature(
                    name=row[0],
                    access_modifier=row[1],
                    type=row[2],
                    is_static=bool(row[3]),
                    is_final=bool(row[4])
                )
                class_index.fields.append(field)
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM class_index')
            class_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM methods')
            method_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM constructors')
            constructor_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM fields')
            field_count = cursor.fetchone()[0]
            
            return {
                'classes': class_count,
                'methods': method_count,
                'constructors': constructor_count,
                'fields': field_count
            }
