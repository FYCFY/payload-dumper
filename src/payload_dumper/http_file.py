import io
import os
import time
import httpx


class HttpFile(io.RawIOBase):
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    TIMEOUT = 30.0  # 30秒超时
    
    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def _read_with_retry(self, start_pos: int, size: int) -> bytes:
        """带重试的读取函数"""
        headers = {"Range": f"bytes={start_pos}-{start_pos + size - 1}"}
        retries = 0
        last_error = None
        
        while retries < self.MAX_RETRIES:
            try:
                with self.client.stream("GET", self.url, headers=headers, timeout=self.TIMEOUT) as r:
                    if r.status_code != 206:
                        raise io.UnsupportedOperation(f"服务器不支持范围请求，状态码: {r.status_code}")
                    
                    # 读取所有数据到内存
                    chunks = []
                    total_size = 0
                    for chunk in r.iter_bytes(8192):
                        chunks.append(chunk)
                        total_size += len(chunk)
                        if self.progress_reporter:
                            self.progress_reporter(total_size, size)
                    
                    # 验证数据大小
                    if total_size != size:
                        raise ValueError(f"读取的数据大小不匹配: 期望 {size} 字节，实际读取 {total_size} 字节")
                    
                    return b''.join(chunks)
                    
            except Exception as e:
                last_error = e
                retries += 1
                if retries < self.MAX_RETRIES:
                    print(f"读取失败，{self.RETRY_DELAY}秒后重试 ({retries}/{self.MAX_RETRIES}): {str(e)}")
                    time.sleep(self.RETRY_DELAY)
                    # 重新创建客户端以防连接问题
                    self._recreate_client()
        
        raise IOError(f"多次重试后仍然失败: {str(last_error)}")

    def _recreate_client(self):
        """重新创建HTTP客户端"""
        try:
            self.client.close()
        except:
            pass
        self.client = httpx.Client(timeout=self.TIMEOUT)

    def _read_internal(self, buf: bytes) -> int:
        size = len(buf)
        end_pos = min(self.pos + size - 1, self.size - 1)
        size = end_pos - self.pos + 1
        
        try:
            data = self._read_with_retry(self.pos, size)
            buf[:len(data)] = data
            self.total_bytes += len(data)
            self.pos += len(data)
            return len(data)
        except Exception as e:
            raise IOError(f"读取数据失败: {str(e)}")

    def readall(self) -> bytes:
        sz = self.size - self.pos
        buf = bytearray(sz)
        self._read_internal(buf)
        return buf

    def readinto(self, buffer) -> int:
        return self._read_internal(buffer)

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        if whence == os.SEEK_SET:
            new_pos = offset
        elif whence == os.SEEK_CUR:
            new_pos = self.pos + offset
        elif whence == os.SEEK_END:
            new_pos = self.size + offset
        else:
            raise io.UnsupportedOperation(f"不支持的seek方式: {whence}")
            
        if new_pos < 0 or new_pos > self.size:
            raise ValueError(f"无效的seek位置: {new_pos}，文件大小: {self.size}")
            
        self.pos = new_pos
        return new_pos

    def tell(self) -> int:
        return self.pos

    def __init__(self, url: str, progress_reporter=None):
        self.url = url
        self.client = httpx.Client(timeout=self.TIMEOUT)
        self.progress_reporter = progress_reporter
        
        # 获取文件大小
        retries = 0
        last_error = None
        
        while retries < self.MAX_RETRIES:
            try:
                h = self.client.head(url, timeout=self.TIMEOUT)
                if h.status_code != 200:
                    raise ValueError(f"无法访问URL，状态码: {h.status_code}")
                    
                if h.headers.get("Accept-Ranges", "none") != "bytes":
                    raise ValueError("服务器不支持范围请求")
                    
                size = int(h.headers.get("Content-Length", "0"))
                if size == 0:
                    raise ValueError("文件大小为0或无法获取文件大小")
                    
                self.size = size
                self.pos = 0
                self.total_bytes = 0
                return
                
            except Exception as e:
                last_error = e
                retries += 1
                if retries < self.MAX_RETRIES:
                    print(f"初始化失败，{self.RETRY_DELAY}秒后重试 ({retries}/{self.MAX_RETRIES}): {str(e)}")
                    time.sleep(self.RETRY_DELAY)
                    self._recreate_client()
        
        raise ValueError(f"初始化失败: {str(last_error)}")

    def close(self) -> None:
        if hasattr(self, 'client'):
            try:
                self.client.close()
            except:
                pass

    def closed(self) -> bool:
        return not hasattr(self, 'client') or self.client.is_closed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


if __name__ == "__main__":
    from . import zipfile

    with HttpFile(
        "https://dl.google.com/developers/android/vic/images/ota/husky_beta-ota-ap31.240322.027-3310ca50.zip"
    ) as f:
        f.seek(0, os.SEEK_END)
        print("file size:", f.tell())
        f.seek(0, os.SEEK_SET)
        z = zipfile.ZipFile(f)
        print(z.namelist())
        for name in z.namelist():
            with z.open(name) as payload:
                print(name, "compress type:", payload._compress_type)
        print("total read:", f.total_bytes)

    with HttpFile(
        "https://dl.google.com/developers/android/baklava/images/factory/comet_beta-bp21.241121.009-factory-0739d956.zip"
    ) as f:
        f.seek(0, os.SEEK_END)
        print("file size:", f.tell())
        f.seek(0, os.SEEK_SET)
        z = zipfile.ZipFile(f)
        print(z.namelist())
        for name in z.namelist():
            with z.open(name) as payload:
                print(name, "compress type:", payload._compress_type, 'size:', payload._left)
        with z.open("comet_beta-bp21.241121.009/image-comet_beta-bp21.241121.009.zip") as f2:
            z2 = zipfile.ZipFile(f2)
            print(z2.namelist())
        print("total read:", f.total_bytes)
