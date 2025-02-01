#!/usr/bin/env python3
import argparse
import os
import sys
from multiprocessing import cpu_count
from urllib.parse import urlparse
from zipfile import ZipFile
import enlighten
import traceback

from . import http_file
from .dumper import Dumper
from .legacy_rom import LegacyBootExtractor
from . import image_extractor

def clear_screen():
    """清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')

def is_url(path):
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def try_extract_payload(input_file, args):
    """尝试使用payload.bin方式提取"""
    try:
        d = Dumper(
            payloadfile=input_file,
            out=args.output,
            diff=args.diff,
            old=args.old,
            images=args.partitions if args.partitions else "",
            workers=args.workers,
            list_partitions=args.list,
            extract_metadata=args.metadata
        )
        d.run()
        return True
    except Exception as e:
        print(f"[!] payload.bin提取失败：{str(e)}")
        return False

def try_extract_direct(url, args):
    """尝试直接提取镜像文件"""
    try:
        extractor = image_extractor.ImageExtractor(
            url=url,
            out_dir=args.output,
            target_images=args.partitions
        )
        extractor.extract_images()
        return True
    except Exception as e:
        print(f"[!] 直接提取失败：{str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Android ROM分区提取工具')
    
    # 位置参数：输入文件/URL和分区（可选）
    parser.add_argument("input", help="输入文件路径或URL")
    parser.add_argument("partitions", nargs='?', help="要提取的分区名称")
    
    # 可选参数
    parser.add_argument("--partitions", "-p", dest="partitions_opt", help="要提取的分区列表（用逗号分隔）")
    parser.add_argument("--output", "-o", help="输出目录", default="output")
    parser.add_argument("--diff", "-d", action="store_true", help="差分更新模式")
    parser.add_argument("--old", help="旧版本分区目录")
    parser.add_argument("--workers", "-w", type=int, help="工作线程数", default=os.cpu_count())
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用分区")
    parser.add_argument("--metadata", "-m", action="store_true", help="提取元数据")
    
    args = parser.parse_args()
    
    # 处理分区参数：优先使用位置参数，如果没有则使用选项参数
    if args.partitions:
        args.partitions = args.partitions
    elif args.partitions_opt:
        args.partitions = args.partitions_opt
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 判断输入是否为URL
    is_url_input = args.input.startswith(("http://", "https://"))
    success = False
    
    try:
        if is_url_input:
            # 对于URL，先尝试payload.bin方式，失败则尝试直接提取
            print("[*] 正在尝试 payload.bin 方式提取...")
            input_file = http_file.HttpFile(args.input)
            if try_extract_payload(input_file, args):
                success = True
            else:
                # 清屏并显示新的提取方式
                clear_screen()
                print("[*] 正在尝试直接提取镜像文件...")
                if try_extract_direct(args.input, args):
                    success = True
        else:
            # 对于本地文件，只尝试payload.bin方式
            print("[*] 正在尝试从本地文件提取...")
            with open(args.input, "rb") as input_file:
                if try_extract_payload(input_file, args):
                    success = True
                    
        if not success:
            print("\n[!] 提取失败：所有提取方式均未成功")
            return 1
            
    except KeyboardInterrupt:
        print("\n[!] 操作已被用户中断")
        return 1
    except Exception as e:
        print(f"[!] 发生错误：{str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
