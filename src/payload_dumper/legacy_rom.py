import io
import os
from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from .http_file import HttpFile

class LegacyBootExtractor:
    CHUNK_SIZE = 1024 * 1024
    MAX_WORKERS = 4
    
    def __init__(self, url: str, progress_reporter=None):
        self.url = url
        self.progress_reporter = progress_reporter
        self.http_file = None
        try:
            self.http_file = HttpFile(url, progress_reporter)
            self.zip_file = ZipFile(self.http_file)
            self._find_boot_img()
        except Exception as e:
            if self.http_file:
                self.http_file.close()
            raise ValueError(str(e))
    
    def _find_boot_img(self):
        try:
            self.img_files = [name for name in self.zip_file.namelist() if name.endswith('.img')]
            if not self.img_files:
                raise ValueError("未找到.img文件")
            
            self.boot_info = None
            for name in self.img_files:
                if 'boot.img' in name.lower():
                    self.boot_info = self.zip_file.getinfo(name)
                    break
            
            if not self.boot_info:
                raise ValueError("未找到boot.img")
                
        except Exception as e:
            raise ValueError(str(e))

    def extract_boot(self, output_dir: str):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_path = os.path.join(output_dir, os.path.basename(self.boot_info.filename))
            
            with self.zip_file.open(self.boot_info.filename) as src, \
                 open(output_path, 'wb') as dst, \
                 tqdm(total=self.boot_info.file_size, unit='B', unit_scale=True) as pbar:
                
                if self.boot_info.compress_type == 0:
                    chunk_size = self.CHUNK_SIZE
                    total_size = self.boot_info.file_size
                    
                    def download_chunk(start, size):
                        chunk = src.read(size)
                        pbar.update(len(chunk))
                        return chunk
                    
                    with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                        futures = []
                        for offset in range(0, total_size, chunk_size):
                            size = min(chunk_size, total_size - offset)
                            futures.append(executor.submit(download_chunk, offset, size))
                        
                        for future in futures:
                            try:
                                chunk = future.result()
                                dst.write(chunk)
                            except Exception as e:
                                raise ValueError(str(e))
                else:
                    while True:
                        chunk = src.read(self.CHUNK_SIZE)
                        if not chunk:
                            break
                        dst.write(chunk)
                        pbar.update(len(chunk))
            
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise ValueError(str(e))
    
    def close(self):
        try:
            if hasattr(self, 'zip_file'):
                self.zip_file.close()
        except:
            pass
        try:
            if self.http_file:
                self.http_file.close()
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close() 