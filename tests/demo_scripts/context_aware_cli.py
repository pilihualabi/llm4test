#!/usr/bin/env python3
"""
Context-Aware Code Generation CLI
命令行接口
"""

import argparse
import logging
import sys
import json
from pathlib import Path

from context_aware import ContextAwareTestGenerator

def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('context_aware.log')
        ]
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Context-Aware Code Generation - 智能Java单元测试生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法
  python context_aware_cli.py --project ../pdfcompare --class com.example.pdfcompare.util.ImageComparator --method compareImages

  # 强制重新索引
  python context_aware_cli.py --project ../pdfcompare --class com.example.pdfcompare.util.ImageComparator --method compareImages --force-reindex

  # 指定输出目录
  python context_aware_cli.py --project ../pdfcompare --class com.example.pdfcompare.util.ImageComparator --method compareImages --output ./my_tests

  # 详细日志
  python context_aware_cli.py --project ../pdfcompare --class com.example.pdfcompare.util.ImageComparator --method compareImages --verbose
        """
    )
    
    # 必需参数
    parser.add_argument(
        '--project',
        required=True,
        help='Java项目路径'
    )
    
    parser.add_argument(
        '--class',
        dest='target_class',
        required=True,
        help='目标类的完全限定名，例如: com.example.pdfcompare.util.ImageComparator'
    )
    
    parser.add_argument(
        '--method',
        dest='target_method',
        required=True,
        help='目标方法名，例如: compareImages'
    )
    
    # 可选参数
    parser.add_argument(
        '--output',
        default='./context_aware_output',
        help='输出目录 (默认: ./context_aware_output)'
    )
    
    parser.add_argument(
        '--force-reindex',
        action='store_true',
        help='强制重新索引项目（忽略缓存）'
    )
    
    parser.add_argument(
        '--max-fix-attempts',
        type=int,
        default=3,
        help='最大修复尝试次数 (默认: 3)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='启用详细日志输出'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='仅显示项目统计信息，不生成测试'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # 验证项目路径
        project_path = Path(args.project)
        if not project_path.exists():
            logger.error(f"项目路径不存在: {project_path}")
            sys.exit(1)
        
        if not project_path.is_dir():
            logger.error(f"项目路径不是目录: {project_path}")
            sys.exit(1)
        
        # 创建生成器
        logger.info(" 初始化Context-Aware测试生成器")
        generator = ContextAwareTestGenerator(
            project_path=str(project_path),
            output_dir=args.output
        )
        
        # 如果只显示统计信息
        if args.stats_only:
            logger.info(" 获取项目统计信息")
            stats = generator.get_project_statistics()
            print("\n" + "="*60)
            print(" 项目统计信息")
            print("="*60)
            print(f" 类数量: {stats['classes']}")
            print(f"  方法数量: {stats['methods']}")
            print(f"  构造器数量: {stats['constructors']}")
            print(f" 字段数量: {stats['fields']}")
            print("="*60)
            return
        
        # 生成测试
        logger.info(f" 开始生成测试: {args.target_class}.{args.target_method}")
        print("\n" + "="*80)
        print(" Context-Aware Code Generation - 智能测试生成")
        print("="*80)
        print(f" 项目路径: {project_path}")
        print(f" 目标类: {args.target_class}")
        print(f"  目标方法: {args.target_method}")
        print(f" 输出目录: {args.output}")
        print(f" 强制重新索引: {'是' if args.force_reindex else '否'}")
        print(f" 最大修复尝试: {args.max_fix_attempts}")
        print("="*80)
        
        result = generator.generate_test(
            target_class_fqn=args.target_class,
            target_method_name=args.target_method,
            force_reindex=args.force_reindex,
            max_fix_attempts=args.max_fix_attempts
        )
        
        # 显示结果
        print("\n" + "="*80)
        print(" 生成结果")
        print("="*80)
        
        if result['success']:
            print(" 测试生成成功!")
        else:
            print(" 测试生成失败!")
        
        # 显示统计信息
        if 'stats' in result and 'analysis' in result['stats']:
            analysis_stats = result['stats']['analysis']
            print(f"\n 项目分析统计:")
            print(f"    处理文件: {analysis_stats['files_processed']}")
            print(f"    发现类: {analysis_stats['classes_found']}")
            print(f"     发现方法: {analysis_stats['methods_found']}")
            print(f"     发现构造器: {analysis_stats['constructors_found']}")
            print(f"    发现字段: {analysis_stats['fields_found']}")
            
            if analysis_stats['errors']:
                print(f"     错误数量: {len(analysis_stats['errors'])}")
        
        # 显示修复信息
        if result['fixes_applied']:
            print(f"\n 应用的修复:")
            for fix in result['fixes_applied']:
                print(f"   • {fix}")
        
        # 显示编译错误
        if result['compilation_errors']:
            print(f"\n 编译错误:")
            for error in result['compilation_errors']:
                print(f"   • {error}")
        
        # 显示输出文件
        output_path = Path(args.output)
        if output_path.exists():
            java_files = list(output_path.glob("*.java"))
            if java_files:
                print(f"\n 生成的测试文件:")
                for java_file in java_files:
                    print(f"    {java_file}")
        
        print("="*80)
        
        # 保存详细结果
        result_file = output_path / "generation_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            # 移除不能序列化的对象
            serializable_result = {
                'success': result['success'],
                'fixes_applied': result['fixes_applied'],
                'compilation_errors': result['compilation_errors'],
                'stats': result['stats']
            }
            if 'error' in result:
                serializable_result['error'] = result['error']
            
            json.dump(serializable_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"详细结果已保存: {result_file}")
        
        # 设置退出码
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
