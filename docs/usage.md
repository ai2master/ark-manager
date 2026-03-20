# ArkManager 使用说明 | Usage Guide

## 目录 | Table of Contents

- [系统要求 | Requirements](#系统要求--requirements)
- [安装方式 | Installation](#安装方式--installation)
- [启动应用 | Launching](#启动应用--launching)
- [主界面介绍 | Main Interface](#主界面介绍--main-interface)
- [浏览压缩包 | Browse Archive](#浏览压缩包--browse-archive)
- [解压操作 | Extraction](#解压操作--extraction)
- [创建压缩包 | Create Archive](#创建压缩包--create-archive)
- [编码处理 | Encoding Handling](#编码处理--encoding-handling)
- [伪加密检测 | Fake Encryption Detection](#伪加密检测--fake-encryption-detection)
- [密码恢复 | Password Recovery](#密码恢复--password-recovery)
- [添加文件到压缩包 | Add Files to Archive](#添加文件到压缩包--add-files-to-archive)
- [测试完整性 | Integrity Test](#测试完整性--integrity-test)
- [快捷键 | Keyboard Shortcuts](#快捷键--keyboard-shortcuts)
- [命令行用法 | Command-Line Usage](#命令行用法--command-line-usage)
- [常见问题 | FAQ](#常见问题--faq)

---

## 系统要求 | Requirements

### 必需依赖 | Required Dependencies

| 依赖 | 用途 | 安装命令 |
|------|------|---------|
| Python 3.9+ | 运行环境 | 系统自带 / Pre-installed |
| PyQt6 | GUI 框架 | `pip install PyQt6` |
| p7zip-full | 7z 压缩引擎 | `sudo apt install p7zip-full` (Debian) |
| chardet | 编码自动检测 | `pip install chardet` |

### 可选依赖 | Optional Dependencies

| 依赖 | 用途 | 安装命令 |
|------|------|---------|
| John the Ripper | 密码恢复 | `sudo apt install john` (Debian) |

### 各发行版安装依赖 | Install Dependencies by Distribution

**Debian / Ubuntu / Linux Mint:**
```bash
sudo apt install p7zip-full python3-pyqt6 python3-chardet
# 可选 | Optional:
sudo apt install john
```

**Fedora / CentOS / RHEL:**
```bash
sudo dnf install p7zip p7zip-plugins python3-qt6 python3-chardet
# 可选 | Optional:
sudo dnf install john
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S p7zip python-pyqt6 python-chardet
# 可选 | Optional:
sudo pacman -S john
```

---

## 安装方式 | Installation

### 方式一：从源码安装 | From Source

```bash
# 克隆仓库 | Clone repository
git clone https://github.com/ai2master/ark-manager.git
cd ark-manager

# 安装（可编辑模式，推荐开发者使用）| Install (editable mode, recommended for developers)
pip install -e .

# 或标准安装 | Or standard install
pip install .
```

### 方式二：DEB 包安装（Debian / Ubuntu）| DEB Package

从 [GitHub Releases](https://github.com/ai2master/ark-manager/releases) 下载最新的 `.deb` 文件。

```bash
# 安装 DEB 包 | Install DEB package
sudo dpkg -i arkmanager_1.0.0_amd64.deb

# 自动修复依赖 | Auto-fix dependencies
sudo apt-get install -f
```

卸载 | Uninstall:
```bash
sudo apt remove arkmanager
```

### 方式三：RPM 包安装（Fedora / CentOS）| RPM Package

```bash
# Fedora
sudo dnf install arkmanager-1.0.0-1.noarch.rpm

# CentOS / RHEL
sudo yum install arkmanager-1.0.0-1.noarch.rpm
```

卸载 | Uninstall:
```bash
sudo dnf remove arkmanager
```

### 方式四：AppImage（免安装便携版）| AppImage (Portable)

AppImage 是单文件可执行程序，无需安装，下载即用。适用于任何 Linux 发行版。

```bash
# 下载后添加执行权限 | Add execute permission after download
chmod +x ArkManager-1.0.0-x86_64.AppImage

# 直接运行 | Run directly
./ArkManager-1.0.0-x86_64.AppImage

# 或打开指定文件 | Or open specific file
./ArkManager-1.0.0-x86_64.AppImage /path/to/archive.zip
```

> **注意 | Note:** AppImage 需要系统安装 FUSE。大多数发行版已预装，若提示缺少 FUSE:
> ```bash
> sudo apt install libfuse2    # Debian/Ubuntu
> sudo dnf install fuse-libs   # Fedora
> ```

### 方式五：Flatpak（沙箱化安装）| Flatpak (Sandboxed)

```bash
# 安装 Flatpak 包 | Install Flatpak package
flatpak install ArkManager-1.0.0.flatpak

# 运行 | Run
flatpak run io.github.arkmanager.ArkManager
```

---

## 启动应用 | Launching

```bash
# 方式一：命令行启动 | Method 1: Command-line launch
arkmanager

# 方式二：直接打开压缩包 | Method 2: Open specific archive
arkmanager /path/to/file.zip

# 方式三：通过 Python 模块启动 | Method 3: Run as Python module
python3 -m arkmanager

# 方式四：通过 Python 模块启动并打开文件 | Method 4: Run with file
python3 -m arkmanager /path/to/file.7z
```

安装 DEB/RPM 包后，ArkManager 也会出现在系统应用菜单中，可以直接点击图标启动。

After installing the DEB/RPM package, ArkManager will also appear in the system application menu for click-to-launch.

---

## 主界面介绍 | Main Interface

ArkManager 的主窗口分为以下几个区域：

The main window is divided into the following areas:

```
+-------------------------------------------------------------+
|  [Open] [Create] [Extract] [Test] [Add] [Delete]   Toolbar  |
+-------------------------------------------------------------+
|  Archive: [/path/to/file.zip    ]  Encoding: [Auto Detect v] |
+-------------------------------------+------------------------+
|                                     |  Archive Comment       |
|  File List (Tree View)              |  +------------------+  |
|                                     |  | This is a comment|  |
|  Name | Size | Compressed | ...     |  | ...              |  |
|  -----------------------------------+  +------------------+  |
|  [D] folder/                        |                        |
|    [F] file1.txt  1.2KB  0.8KB     |  Archive Info          |
|    [F] file2.jpg  3.4MB  3.1MB     |  +------------------+  |
|  [F] readme.md    0.5KB  0.3KB     |  | Type: zip        |  |
|                                     |  | Size: 4.5 MB     |  |
|                                     |  | Method: Deflate  |  |
|                                     |  +------------------+  |
+-------------------------------------+------------------------+
|  3 files, 1 folder, Total: 5.1 KB               Status Bar  |
+-------------------------------------------------------------+
```

### 各区域说明 | Area Descriptions

1. **工具栏 | Toolbar** - 常用操作按钮：打开、创建、解压、测试、添加文件、删除文件
2. **地址栏 | Address Bar** - 显示当前打开的压缩包路径和编码选择器
3. **文件列表 | File List** - 左侧树形视图，展示压缩包中所有文件和目录结构
4. **注释面板 | Comment Panel** - 右侧显示压缩包注释（ZIP 格式支持），中文注释也能正确显示
5. **压缩包信息 | Archive Info** - 右侧下方显示压缩包元数据（类型、大小、压缩方法等）
6. **状态栏 | Status Bar** - 底部显示文件统计信息

### 文件列表列说明 | File List Columns

| 列名 | 说明 |
|------|------|
| Name | 文件名（已修复编码）| Filename (encoding fixed) |
| Size | 原始文件大小 | Original file size |
| Compressed | 压缩后大小 | Compressed size |
| Modified | 最后修改时间 | Last modification time |
| CRC | CRC32 校验值 | CRC32 checksum |
| Encrypted | 是否加密（显示 Yes/No）| Encryption status |
| Method | 压缩方法（如 Deflate, LZMA2）| Compression method |

---

## 浏览压缩包 | Browse Archive

### 打开文件 | Open File

有三种方式打开压缩包：

Three ways to open an archive:

1. **菜单/工具栏** | Menu/Toolbar: `File > Open` 或点击 `Open` 按钮 (快捷键 `Ctrl+O`)
2. **命令行** | Command line: `arkmanager /path/to/file.zip`
3. **拖拽** | Drag & Drop: 将压缩包文件直接拖拽到窗口中

### 支持的格式 | Supported Formats

ArkManager 通过 7z 后端支持以下 20+ 种压缩格式（只读标记的格式只能解压不能创建）：

| 格式 | 扩展名 | 读取 | 创建 |
|------|--------|:----:|:----:|
| 7-Zip | .7z | Y | Y |
| ZIP | .zip | Y | Y |
| TAR | .tar | Y | Y |
| GZip | .gz, .tar.gz, .tgz | Y | Y |
| BZip2 | .bz2, .tar.bz2, .tbz2 | Y | Y |
| XZ | .xz, .tar.xz, .txz | Y | Y |
| Zstandard | .zst, .tar.zst | Y | Y |
| WIM | .wim | Y | Y |
| RAR | .rar | Y | Read-only |
| CAB | .cab | Y | Read-only |
| ISO | .iso | Y | Read-only |
| ARJ | .arj | Y | Read-only |
| CPIO | .cpio | Y | Read-only |
| RPM | .rpm | Y | Read-only |
| DEB | .deb | Y | Read-only |
| LZH | .lzh | Y | Read-only |
| LZMA | .lzma | Y | Read-only |
| Z | .z | Y | Read-only |

### 查看加密压缩包 | View Encrypted Archives

如果压缩包有密码保护，ArkManager 会提示输入密码。输入正确密码后即可查看文件列表。

If the archive is password-protected, ArkManager will prompt for the password. Enter the correct password to view the file list.

> **支持中文密码** | **Chinese passwords supported**: ArkManager 通过正确的 UTF-8 编码传递密码给 7z，确保中文、日文等多语言密码完美工作。

---

## 解压操作 | Extraction

### 基本解压 | Basic Extraction

1. 打开压缩包
2. 点击工具栏 **Extract** 按钮或按 `Ctrl+E`
3. 在解压对话框中配置选项
4. 点击 **OK** 开始解压

### 解压对话框选项 | Extract Dialog Options

| 选项 | 说明 | 默认值 |
|------|------|--------|
| **Destination** | 解压目标目录 | 压缩包所在目录 |
| **Auto-create parent folder** | 自动创建与压缩包同名的文件夹，避免文件散落 | 开启 |
| **Overwrite existing files** | 覆盖目标目录中的同名文件 | 开启 |
| **Encoding Mode** | 文件名编码处理方式（见下文）| Auto Detect |
| **Forced Encoding** | 当 Encoding Mode 为 Force 时选择的编码 | GBK |
| **Password** | 解压密码（支持中文）| 空 |

### 自动创建父文件夹 | Auto-Create Parent Folder

推荐保持开启。此选项会在目标目录中创建一个与压缩包同名的子文件夹：

Recommended to keep enabled. This creates a subfolder named after the archive:

```
# 开启时 | When enabled:
解压 photos.zip -> photos/
                    |- img001.jpg
                    +- img002.jpg

# 关闭时 | When disabled:
解压 photos.zip -> img001.jpg
                   img002.jpg    # 文件直接散落在目标目录 | Files spread in destination
```

### 解压后编码修复 | Post-Extraction Encoding Fix

解压时，ArkManager 会：
1. 调用 7z 解压文件（保留原始文件名）
2. 根据编码模式检测并修复乱码文件名
3. 重命名文件到正确编码的文件名

After extraction, ArkManager will:
1. Call 7z to extract files (preserving original filenames)
2. Detect and fix garbled filenames based on encoding mode
3. Rename files to correctly encoded filenames

---

## 创建压缩包 | Create Archive

### 操作步骤 | Steps

1. 点击工具栏 **Create** 或按 `Ctrl+N`
2. 在弹出的文件选择器中选择要压缩的文件和目录
3. 在压缩对话框中配置选项
4. 点击 **OK** 开始压缩

### 压缩对话框选项 | Compress Dialog Options

| 选项 | 说明 | 可选值 |
|------|------|--------|
| **Output Path** | 输出压缩包路径 | 自动生成 |
| **Format** | 压缩格式 | 7z, ZIP, TAR, GZ, BZ2, XZ, WIM |
| **Compression Level** | 压缩级别 0-9 | 0=仅存储, 5=正常, 9=极限 |
| **Compression Method** | 压缩方法 | LZMA2, LZMA, PPMd, BZip2, Deflate, Copy |
| **Solid compression** | 固实压缩（仅 7z） | 开/关 |
| **Volume size** | 分卷大小 | 如 100m, 1g, 4480m |
| **Password** | 加密密码（支持中文） | 空 |
| **Encrypt filenames** | 加密文件名（仅 7z） | 开/关 |
| **Encoding Mode** | 文件名编码（仅 ZIP） | Auto (UTF-8) / Force GBK |

### 各格式推荐设置 | Recommended Settings per Format

**7z 格式（最佳压缩率）| 7z Format (Best compression):**
- Method: LZMA2
- Level: 5-7
- Solid: 开启 | On

**ZIP 格式（兼容性最佳）| ZIP Format (Best compatibility):**
- Method: Deflate
- Level: 5
- Encoding: Auto (UTF-8) -- 推荐，现代解压工具都支持
- Encoding: Force GBK -- 仅当接收方使用旧版中文 Windows

**分卷压缩 | Volume splitting:**
- 适合大文件传输或刻录光盘
- 输入格式：`100m`（100MB 每卷）、`4480m`（DVD 大小）、`700m`（CD 大小）

---

## 编码处理 | Encoding Handling

### 问题背景 | Background

在 Windows 上创建的 ZIP 压缩包通常使用 GBK 编码存储中文文件名。Linux 系统默认使用 UTF-8，直接解压会导致文件名显示为乱码（如 `ÊÀ½çÄúºÃ.txt`）。这是一个影响约 30% 中文 ZIP 文件的已知问题（7-Zip Bug #2198）。

ZIP archives created on Windows typically use GBK encoding for Chinese filenames. Linux defaults to UTF-8, causing garbled filenames when extracted directly (e.g., `ÊÀ½çÄúºÃ.txt`). This is a known issue affecting ~30% of Chinese ZIP files (7-Zip Bug #2198).

### 预览编码选择 | Preview Encoding Selection

在主界面顶部的 **Encoding** 下拉框中选择编码模式，立即刷新文件列表显示：

Select encoding mode in the **Encoding** dropdown at the top of the main interface to instantly refresh the file list:

| 模式 | 说明 | 使用场景 |
|------|------|---------|
| **Auto Detect** | 使用 chardet 库自动检测编码 | 大多数情况 |
| **Force GBK** | 强制以 GBK 解码文件名 | 中国大陆 Windows 创建的压缩包 |
| **Force GB18030** | 强制以 GB18030 解码 | 包含生僻字的中文文件名 |
| **Force Big5** | 强制以 Big5 解码 | 繁体中文（台湾、香港）压缩包 |
| **Force Shift-JIS** | 强制以 Shift-JIS 解码 | 日文 Windows 创建的压缩包 |
| **No Conversion** | 不做任何编码转换 | 查看原始文件名 |

### 编码工作原理 | How Encoding Works

```
原始ZIP文件 -> 7z 读取（输出 CP437/UTF-8 字节）-> ArkManager 编码处理
                                                          |
                                         +----------------+----------------+
                                         |                |                |
                                       auto            force            none
                                         |                |                |
                                   chardet 检测      CP437->GBK 转换    原样输出
                                   尝试 CJK 编码列表
                                         |
                                       修复后的文件名
```

**Auto Detect 流程 | Auto Detect Process:**
1. 将文件名字符串按 CP437 编码为字节序列
2. 使用 chardet 分析字节序列的编码
3. 如果 chardet 识别出 GBK/GB18030/Big5 等，按识别结果解码
4. 如果 chardet 不确定，按优先级尝试 GBK -> GB18030 -> Big5 -> Shift-JIS
5. 所有编码都失败则返回原始文件名

---

## 伪加密检测 | Fake Encryption Detection

### 什么是伪加密 | What is Fake Encryption

ZIP 文件使用标志位表示文件是否加密。伪加密是指：修改了加密标志位使压缩包看起来已加密，但实际数据并未经过加密处理。常见于 CTF 竞赛题目和部分恶意软件。

ZIP files use flag bits to indicate encryption. Fake/pseudo encryption means: the encryption flag is set to make the archive appear encrypted, but data is not actually encrypted. Common in CTF challenges and some malware.

### 检测方法 | Detection Method

ArkManager 分析 ZIP 二进制结构中的两种异常：

1. **LFH/CDH 标志不一致** | LFH/CDH flag mismatch:
   - 本地文件头 (Local File Header, offset +6) 的加密标志
   - 中央目录头 (Central Directory Header, offset +8) 的加密标志
   - 两者不一致说明被人为篡改

2. **加密标志 + 无加密数据** | Encryption flag + unencrypted data:
   - 设置了加密标志但数据以已知文件头开头（PNG 签名、JPEG SOI、PDF 头等）

### 使用步骤 | Steps

1. 打开一个 ZIP 压缩包
2. 菜单 `Actions > Detect Fake Encryption` 或使用快捷键
3. 查看检测结果对话框：
   - **GENUINE** -- 正常加密，数据确实已加密
   - **SUSPICIOUS (LFH/CDH mismatch)** -- 疑似伪加密，标志位不一致
   - **SUSPICIOUS (no encryption data)** -- 疑似伪加密，数据未加密
4. 如果检测到伪加密，点击 **Remove Fake Encryption** 按钮
5. 选择保存位置，ArkManager 生成一个修复后的副本（原文件不变）

### 修复原理 | How Patching Works

修复伪加密的原理是清除 ZIP 文件中所有相关的加密标志位：
- Local File Header: offset +6, 清除 bit 0
- Central Directory Header: offset +8, 清除 bit 0

修复使用 `mmap` 内存映射直接在文件副本上进行字节级修改，安全且高效。

---

## 密码恢复 | Password Recovery

### 前提条件 | Prerequisites

密码恢复功能需要系统安装 John the Ripper：

```bash
# Debian/Ubuntu
sudo apt install john

# Fedora
sudo dnf install john

# Arch
sudo pacman -S john
```

### 使用步骤 | Steps

1. 打开加密的压缩包
2. 菜单 `Tools > Password Recovery` 或按 `Ctrl+J`
3. 在密码恢复对话框中：

   **a) 提取哈希 | Extract Hash:**
   - 点击 **Extract Hash** 按钮
   - ArkManager 自动选择对应的 *2john 工具（zip2john / rar2john / 7z2john）
   - 提取成功后显示哈希内容

   **b) 选择攻击模式 | Choose Attack Mode:**

   | 模式 | 说明 | 适用场景 |
   |------|------|---------|
   | **Wordlist** | 字典攻击，使用预定义密码列表 | 最常用，有字典文件时首选 |
   | **Incremental** | 暴力破解，尝试所有可能组合 | 密码较短时（1-6位） |
   | **Single** | 基于用户名等信息生成密码变体 | 密码可能与用户名相关 |
   | **Mask** | 按规则生成密码 | 知道密码部分特征时 |

   **c) 配置参数 | Configure Parameters:**
   - **Wordlist file** (Wordlist 模式): 选择字典文件路径
   - **Mask pattern** (Mask 模式): 输入掩码（如 `?a?a?a?a?a?a` 表示 6 位任意字符）
   - **Min/Max length**: 密码长度范围
   - **Hash format**: 通常自动检测，也可手动指定

   **d) 开始破解 | Start Cracking:**
   - 点击 **Start Cracking** 按钮
   - 进度区域显示 John 的实时输出
   - 破解成功后在结果区域显示密码
   - 可随时点击 **Stop** 中止

### 掩码规则 | Mask Rules

| 符号 | 含义 |
|------|------|
| `?l` | 小写字母 a-z |
| `?u` | 大写字母 A-Z |
| `?d` | 数字 0-9 |
| `?s` | 特殊字符 |
| `?a` | 所有可打印字符 |
| `?b` | 所有 8-bit 字符（0x00-0xff） |

示例 | Examples:
- `?d?d?d?d?d?d` -- 6 位纯数字密码
- `?u?l?l?l?l?d?d` -- 1大写+4小写+2数字
- `password?d?d` -- password 后跟 2 位数字

---

## 添加文件到压缩包 | Add Files to Archive

1. 打开一个压缩包
2. 点击工具栏 **Add** 按钮
3. 在文件选择器中选择要添加的文件
4. 文件会被添加到压缩包中

> **注意 | Note:** 此操作会修改原始压缩包文件。RAR 格式不支持此操作。

---

## 测试完整性 | Integrity Test

测试压缩包是否损坏：

1. 打开压缩包
2. 点击工具栏 **Test** 按钮或按 `Ctrl+T`
3. ArkManager 调用 `7z t` 命令对所有文件进行 CRC 校验
4. 弹出结果对话框：
   - **OK** -- 压缩包完整，所有文件 CRC 校验通过
   - **Error** -- 压缩包损坏，显示具体错误信息

---

## 快捷键 | Keyboard Shortcuts

| 快捷键 | 功能 | Description |
|--------|------|-------------|
| `Ctrl+O` | 打开压缩包 | Open archive |
| `Ctrl+N` | 创建压缩包 | Create archive |
| `Ctrl+E` | 解压 | Extract |
| `Ctrl+T` | 测试完整性 | Test integrity |
| `Ctrl+J` | 密码恢复 | Password recovery |
| `Ctrl+Q` | 退出 | Quit |

---

## 命令行用法 | Command-Line Usage

```bash
# 启动 GUI | Launch GUI
arkmanager

# 打开指定压缩包 | Open specific archive
arkmanager /path/to/archive.zip

# 也可以作为 Python 模块运行 | Run as Python module
python3 -m arkmanager /path/to/archive.7z
```

ArkManager 目前仅提供 GUI 界面，不支持纯命令行批量操作。如需命令行操作，请直接使用 `7z` 命令。

ArkManager currently only provides a GUI interface. For command-line batch operations, use the `7z` command directly.

---

## 常见问题 | FAQ

### Q: 打开压缩包后文件名仍然是乱码？
**A:** 尝试在顶部编码选择器中切换到 **Force GBK** 或 **Force GB18030**。如果是繁体中文文件名，选择 **Force Big5**。

### Q: 解压后文件名正常但文件内容乱码？
**A:** 文件内容编码不属于 ArkManager 的处理范围。文件内容的编码需要用文本编辑器（如 VS Code）打开时选择正确编码。

### Q: 提示 "7z command not found"？
**A:** 需要安装 p7zip-full 包：
```bash
sudo apt install p7zip-full    # Debian/Ubuntu
sudo dnf install p7zip p7zip-plugins  # Fedora
```

### Q: 密码恢复功能不可用？
**A:** 需要安装 John the Ripper：
```bash
sudo apt install john    # Debian/Ubuntu
```

### Q: AppImage 运行报错 "squashfs compression" 相关错误？
**A:** ArkManager 的 AppImage 使用 gzip 压缩以确保兼容性。如仍报错，请确保系统安装了 FUSE：
```bash
sudo apt install libfuse2
```

### Q: 如何处理分卷压缩包（.001, .002, ...）？
**A:** 打开第一个分卷文件（.001 或不带编号的文件），7z 会自动识别并处理其余分卷。

### Q: Flatpak 版本无法访问某些目录？
**A:** Flatpak 运行在沙箱中，默认只能访问 `$HOME`、`/tmp`、`/media`、`/mnt`。如需访问其他目录，使用 `flatpak override` 命令添加权限。
