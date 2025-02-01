# Android ROM 分区提取工具

这是一个用于从 Android ROM 包中提取分区镜像的工具。它支持两种提取方式：
1. 从 payload.bin 格式的 ROM 包中提取分区
2. 从普通 ZIP 格式的 ROM 包中直接提取镜像文件

## 特点

- 支持从 URL 直接提取，无需下载完整 ROM 包
- 支持从本地文件提取
- 自动识别 ROM 包格式并选择合适的提取方式
- 支持提取嵌套 ZIP 包中的镜像文件
- 多线程处理，提升提取速度
- 支持断点续传
- 实时显示下载进度

## 安装要求

- Python >= 3.8
- pip 包管理器

## 安装方法

```bash
# 从 GitHub 安装最新版本
pip install git+https://github.com/5ec1cff/payload-dumper
```

## 使用方法

### 基本用法

```bash
# 从 URL 提取单个分区
payload_dumper <ROM包URL> <分区名>

# 从本地文件提取单个分区
payload_dumper <ROM包路径> <分区名>

# 提取多个分区（使用逗号分隔）
payload_dumper <ROM包URL或路径> -p boot,system,vendor
```

### 常用示例

```bash
# 提取 boot 分区
payload_dumper https://example.com/rom.zip boot

# 提取 boot 和 system 分区
payload_dumper https://example.com/rom.zip -p boot,system

# 指定输出目录
payload_dumper https://example.com/rom.zip boot -o my_output

# 使用64线程提取
payload_dumper https://example.com/rom.zip boot -w 64
```

### 所有可用参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `<URL/文件>` | - | ROM包的URL或本地文件路径 | `https://example.com/rom.zip` |
| `<分区名>` | - | 要提取的分区名称 | `boot` |
| `--partitions` | `-p` | 要提取的分区列表（用逗号分隔） | `-p boot,system,vendor` |
| `--output` | `-o` | 指定输出目录 | `-o my_output` |
| `--workers` | `-w` | 指定工作线程数 | `-w 64` |
| `--diff` | `-d` | 差分更新模式 | `-d` |
| `--old` | - | 旧版本分区目录（差分更新用） | `--old old_rom` |
| `--list` | `-l` | 列出所有可用分区 | `-l` |
| `--metadata` | `-m` | 提取元数据 | `-m` |

### 支持的分区类型

工具可以提取以下格式的镜像文件：
- `.img` 格式镜像
- `.bin` 格式镜像
- `.raw` 格式镜像

### 注意事项

1. 对于 URL 提取，工具会自动：
   - 先尝试 payload.bin 方式提取
   - 如果失败，会自动切换到直接提取方式
2. 对于本地文件，仅支持 payload.bin 方式提取
3. 默认输出目录为 `output`
4. 默认使用系统 CPU 核心数作为线程数
5. 支持断点续传，下载中断后重新运行会继续下载

## 开发相关

```bash
# 克隆仓库
git clone https://github.com/5ec1cff/payload-dumper

# 运行
cd src
python -m payload_dumper

# 安装
cd ..
pip install .
```

## 问题反馈

如果您在使用过程中遇到任何问题，请在 GitHub 上提交 Issue。

