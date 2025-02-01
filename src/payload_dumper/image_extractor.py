import os
from . import http_file
from . import zipfile
import enlighten

class ImageExtractor:
    def __init__(self, url, out_dir, target_images=None):
        self.url = url
        self.out_dir = out_dir
        self.target_images = target_images.split(',') if target_images else None
        self.manager = enlighten.get_manager()
        self.download_progress = None

    def update_download_progress(self, prog, total):
        if self.download_progress is None and prog != total:
            self.download_progress = self.manager.counter(
                total=total, desc="下载进度", unit="字节", leave=False
            )
        if self.download_progress is not None:
            self.download_progress.update(prog - self.download_progress.count)
            if prog == total:
                self.download_progress.close()
                self.download_progress = None

    def _is_image_file(self, filename):
        """检查文件是否为镜像文件"""
        image_extensions = ['.img', '.bin', '.raw']
        return any(filename.lower().endswith(ext) for ext in image_extensions)

    def _should_extract_file(self, filename):
        """判断是否应该提取该文件"""
        if not self._is_image_file(filename):
            return False
        
        if self.target_images is None:
            return True
            
        return any(target in filename.lower() for target in self.target_images)

    def extract_images(self):
        """从URL中提取镜像文件"""
        try:
            with http_file.HttpFile(self.url, self.update_download_progress) as f:
                with zipfile.ZipFile(f) as zip_file:
                    # 获取所有文件列表
                    all_files = zip_file.namelist()
                    
                    # 过滤出镜像文件
                    image_files = [f for f in all_files if self._should_extract_file(f)]
                    
                    if not image_files:
                        print("[!] 未找到任何镜像文件")
                        return
                    
                    # 创建输出目录
                    os.makedirs(self.out_dir, exist_ok=True)
                    
                    # 提取文件
                    for image_file in image_files:
                        try:
                            # 处理嵌套的zip文件
                            if image_file.endswith('.zip'):
                                with zip_file.open(image_file) as nested_zip_data:
                                    with zipfile.ZipFile(nested_zip_data) as nested_zip:
                                        nested_images = [f for f in nested_zip.namelist() 
                                                       if self._should_extract_file(f)]
                                        for nested_image in nested_images:
                                            out_path = os.path.join(self.out_dir, 
                                                                  os.path.basename(nested_image))
                                            with open(out_path, 'wb') as out_file:
                                                out_file.write(nested_zip.read(nested_image))
                                            print(f"[+] 已提取：{nested_image} -> {out_path}")
                            else:
                                # 直接提取镜像文件
                                out_path = os.path.join(self.out_dir, 
                                                      os.path.basename(image_file))
                                with open(out_path, 'wb') as out_file:
                                    out_file.write(zip_file.read(image_file))
                                print(f"[+] 已提取：{image_file} -> {out_path}")
                            
                        except Exception as e:
                            print(f"[!] 提取 {image_file} 时出错：{str(e)}")
                    
        except Exception as e:
            print(f"[!] 提取过程出错：{str(e)}")
        finally:
            self.manager.stop() 