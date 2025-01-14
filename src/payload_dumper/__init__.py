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

def is_url(path):
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--partitions", help="分区列表，用逗号分隔")
    parser.add_argument("--out", default="output")
    parser.add_argument("--diff", action="store_true")
    parser.add_argument("--old", default="old")
    parser.add_argument("path")
    args = parser.parse_args()

    if not os.path.exists(args.out):
        os.makedirs(args.out)

    manager = enlighten.get_manager()
    pbar = None

    def progress_callback(current, total):
        nonlocal pbar
        try:
            if pbar is None:
                pbar = manager.counter(total=total, desc='Downloading', unit='bytes', leave=False)
            pbar.count = current
            if current == total:
                pbar.close()
                pbar = None
        except:
            pass

    path = args.path
    file = None
    extractor = None
    
    try:
        if is_url(path):
            file = http_file.HttpFile(path, progress_callback)
            zip_file = ZipFile(file)
            
            payload_path = None
            for name in zip_file.namelist():
                if name.endswith('payload.bin'):
                    payload_path = name
                    break
            
            if payload_path:
                with zip_file.open(payload_path) as payload:
                    dumper = Dumper(
                        payloadfile=payload,
                        out=args.out,
                        diff=args.diff,
                        old=args.old,
                        images=args.partitions if args.partitions else "",
                        workers=cpu_count()
                    )
                    dumper.run()
            else:
                file.close()
                file = None
                extractor = LegacyBootExtractor(path, progress_callback)
                extractor.extract_boot(args.out)
        else:
            with open(path, 'rb') as f:
                dumper = Dumper(
                    payloadfile=f,
                    out=args.out,
                    diff=args.diff,
                    old=args.old,
                    images=args.partitions if args.partitions else "",
                    workers=cpu_count()
                )
                dumper.run()

    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)
    finally:
        if file:
            try:
                file.close()
            except:
                pass
        if extractor:
            try:
                extractor.close()
            except:
                pass

if __name__ == '__main__':
    main()
