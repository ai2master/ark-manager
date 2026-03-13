# ArkManager 使用说明 | Usage Guide

## 安装 | Installation

### 系统要求 | Requirements

- Python 3.9+
- PyQt6
- p7zip-full（提供 `7z` 命令）
- chardet（Python 包）
- john（可选，用于密码恢复）

### 从源码安装 | From Source

```bash
git clone https://github.com/ai2master/ark-manager.git
cd ark-manager
pip install -e .
arkmanager
```

### Debian/Ubuntu (.deb)

```bash
sudo dpkg -i arkmanager_1.0.0_amd64.deb
sudo apt-get install -f
```

### Fedora/RHEL (.rpm)

```bash
sudo dnf install arkmanager-1.0.0-1.noarch.rpm
```

### AppImage（免安装）

```bash
chmod +x ArkManager-1.0.0-x86_64.AppImage
./ArkManager-1.0.0-x86_64.AppImage
```

### Flatpak

```bash
flatpak install ArkManager-1.0.0.flatpak
flatpak run io.github.arkmanager.ArkManager
```

## 基本使用 | Basic Usage

### 启动 | Launch

```bash
arkmanager                      # 打开GUI | Open GUI
arkmanager /path/to/file.zip    # 直接打开压缩包 | Open specific archive
```

也可以将压缩包文件直接拖拽到窗口中打开。

### 浏览压缩包 | Browse Archive

打开压缩包后，左侧树形视图显示文件列表，包含文件名、大小、压缩大小、修改日期、CRC、加密状态和压缩方法。右侧面板显示压缩包备注和元数据。

### 解压 | Extract

1. 打开压缩包
2. 点击工具栏 **Extract** 或使用 `Ctrl+E`
3. 在对话框中选择：
   - **目标目录** | Destination directory
   - **自动创建父文件夹**（默认开启）| Auto-create parent folder
   - **覆盖已有文件** | Overwrite existing files
   - **文件名编码** | Filename encoding mode
   - **密码**（支持中文密码）| Password (Chinese supported)
4. 点击 OK 开始解压

### 创建压缩包 | Create Archive

1. 点击工具栏 **Create** 或使用 `Ctrl+N`
2. 选择要压缩的文件
3. 在对话框中设置：
   - **输出路径** | Output path
   - **格式**（7z/ZIP/TAR/GZ/BZ2/XZ/WIM）| Format
   - **压缩等级**（0-9）| Compression level
   - **压缩方法**（LZMA2/LZMA/PPMd/BZip2/Deflate/Copy）| Method
   - **文件名编码**（UTF-8 或 GBK）| Filename encoding
   - **密码和加密文件名**（支持中文）| Password and encrypt filenames
4. 点击 OK 创建

## 编码功能 | Encoding Features

### 预览编码选择 | Preview Encoding

在主界面顶部工具栏选择编码模式：
- **Auto Detect** - 自动检测并修复中文乱码
- **Force GBK** - 强制 GBK 编码（中文 Windows 创建的压缩包）
- **Force GB18030** - 中文万用编码
- **Force Big5** - 繁体中文
- **Force Shift-JIS** - 日文
- **No Conversion** - 显示原始文件名

### 解压/压缩时的编码 | Encoding in Extract/Compress

解压和压缩对话框中均提供独立的编码选项，可以：
- 自动检测编码
- 强制指定为 GBK 编码
- 不做任何转换

## 密码恢复 | Password Recovery

集成了 John the Ripper，使用方法：

1. 打开加密的压缩包
2. 选择 **Tools > Password Recovery (Ctrl+J)**
3. 点击 **Extract Hash** 提取密码哈希
4. 选择攻击模式：
   - **Wordlist** - 字典攻击（需要指定字典文件）
   - **Incremental** - 暴力破解
   - **Single** - 单次破解模式
   - **Mask** - 掩码攻击（如 `?a?a?a?a?a?a`）
5. 设置密码长度范围和哈希格式
6. 点击 **Start Cracking**

## 伪加密检测 | Fake Encryption Detection

1. 打开 ZIP 压缩包
2. 选择 **Actions > Detect Fake Encryption**
3. 查看分析结果
4. 如检测到伪加密，点击 **Remove Fake Encryption** 生成修复后的副本

## 快捷键 | Keyboard Shortcuts

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开压缩包 |
| `Ctrl+N` | 创建压缩包 |
| `Ctrl+E` | 解压 |
| `Ctrl+T` | 测试压缩包完整性 |
| `Ctrl+J` | 密码恢复（John the Ripper）|
| `Ctrl+Q` | 退出 |
