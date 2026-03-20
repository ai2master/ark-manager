# ArkManager 技术架构 | Technical Architecture

## 目录 | Table of Contents

- [技术栈总览 | Tech Stack Overview](#技术栈总览--tech-stack-overview)
- [项目目录结构 | Project Directory Structure](#项目目录结构--project-directory-structure)
- [模块架构 | Module Architecture](#模块架构--module-architecture)
- [分层设计 | Layered Design](#分层设计--layered-design)
- [核心模块详解 | Core Module Details](#核心模块详解--core-module-details)
- [线程模型 | Threading Model](#线程模型--threading-model)
- [编码处理管线 | Encoding Pipeline](#编码处理管线--encoding-pipeline)
- [伪加密检测算法 | Pseudo-Encryption Detection Algorithm](#伪加密检测算法--pseudo-encryption-detection-algorithm)
- [John the Ripper 集成 | JTR Integration](#john-the-ripper-集成--jtr-integration)
- [安全设计 | Security Design](#安全设计--security-design)
- [打包与分发 | Packaging and Distribution](#打包与分发--packaging-and-distribution)
- [CI/CD 流程 | CI/CD Pipeline](#cicd-流程--cicd-pipeline)

---

## 技术栈总览 | Tech Stack Overview

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | >= 3.9 | 主开发语言 |
| GUI 框架 | PyQt6 | >= 6.0 | Qt6 的 Python 绑定，跨平台 GUI |
| 压缩后端 | 7z CLI (p7zip-full) | >= 16.02 | 通过子进程调用，支持 20+ 格式 |
| 编码检测 | chardet | >= 5.0 | Mozilla 的通用字符编码检测器 |
| 密码恢复 | John the Ripper CLI | >= 1.9 | 通过子进程调用 john/zip2john |
| 打包工具 | setuptools / pyproject.toml | - | Python 标准打包 |
| CI/CD | GitHub Actions | - | 自动构建 DEB/RPM/AppImage/Flatpak |
| 代码检查 | ruff | - | 用 Rust 编写的极速 Python linter |
| 测试框架 | pytest + pytest-qt | - | Python 标准测试 + Qt 控件测试 |

---

## 项目目录结构 | Project Directory Structure

```
ark-manager/
|-- arkmanager/                       # 主应用源码 | Main application source
|   |-- __init__.py                   # 包初始化，版本号定义 | Package init, version
|   |-- __main__.py                   # 程序入口点，Qt 应用初始化 | Entry point, Qt app init
|   |-- main_window.py                # 主窗口 GUI，所有对话框 | Main window, all dialogs
|   |-- archive_backend.py            # 7z CLI 封装层 | 7z CLI wrapper layer
|   |-- john_backend.py               # John the Ripper CLI 封装 | JTR CLI wrapper
|   +-- encoding_utils.py             # 编码检测/转换，伪加密检测 | Encoding + pseudo-encryption
|
|-- tests/                            # 测试套件 | Test suite
|   |-- __init__.py                   # 测试包初始化 | Test package init
|   |-- test_archive_backend.py       # 压缩后端测试（22 个用例）| Archive backend tests
|   |-- test_encoding_utils.py        # 编码工具测试（6 个用例）| Encoding utils tests
|   +-- test_john_backend.py          # JTR 后端测试（5 个用例）| JTR backend tests
|
|-- packaging/                        # 多格式打包脚本 | Multi-format packaging scripts
|   |-- appimage/
|   |   +-- build-appimage.sh         # AppImage 手动构建（绕过 appimagetool）
|   |-- deb/
|   |   +-- build-deb.sh              # DEB 包构建脚本
|   |-- rpm/
|   |   |-- arkmanager.spec           # RPM 规格文件
|   |   +-- build-rpm.sh              # RPM 包构建脚本
|   +-- flatpak/
|       +-- io.github.arkmanager.ArkManager.yml  # Flatpak 清单
|
|-- .github/workflows/               # GitHub Actions 工作流
|   |-- ci.yml                        # CI: lint + test (Python 3.10/3.11/3.12)
|   +-- release.yml                   # Release: 构建 4 种包 + 创建 Release
|
|-- resources/                        # 资源文件 | Resource files
|   |-- arkmanager.desktop            # Linux 桌面集成文件
|   |-- arkmanager.svg                # 应用图标 (SVG)
|   +-- generate_icon.py              # 图标生成脚本
|
|-- docs/                             # 文档 | Documentation
|   |-- usage.md                      # 使用说明
|   |-- architecture.md               # 技术架构（本文件）
|   +-- product.md                    # 产品介绍
|
|-- pyproject.toml                    # Python 项目配置（依赖、构建、工具）
|-- LICENSE                           # GPL-3.0 许可证
+-- README.md                         # 项目说明
```

---

## 模块架构 | Module Architecture

### 主要类一览 | Class Overview

| 类名 | 文件 | 职责 |
|------|------|------|
| `MainWindow` | main_window.py | 主窗口，菜单栏/工具栏/状态栏，文件树，压缩包操作 |
| `ExtractDialog` | main_window.py | 解压选项对话框（目录、编码、密码、覆盖） |
| `CompressDialog` | main_window.py | 压缩选项对话框（格式、方法、级别、加密） |
| `JohnDialog` | main_window.py | 密码恢复对话框（哈希提取、攻击配置、进度监控） |
| `PseudoEncryptionDialog` | main_window.py | 伪加密检测与修复对话框 |
| `WorkerThread` | main_window.py | 通用 QThread 工作线程（解压/压缩/测试） |
| `JohnWorkerThread` | main_window.py | JTR 专用 QThread（可能运行数小时） |
| `ArchiveBackend` | archive_backend.py | 7z CLI 封装，所有压缩包操作 |
| `ArchiveInfo` | archive_backend.py | 压缩包元数据数据类 |
| `ArchiveEntry` | archive_backend.py | 压缩包条目数据类 |
| `JohnBackend` | john_backend.py | JTR CLI 封装，哈希提取+破解 |
| `JohnResult` | john_backend.py | JTR 破解结果数据类 |
| `AttackMode` | john_backend.py | 攻击模式枚举 |

---

## 分层设计 | Layered Design

```
+------------------------------------------+
|           GUI Layer (PyQt6)              |
|  MainWindow / ExtractDialog /            |
|  CompressDialog / JohnDialog /           |
|  PseudoEncryptionDialog                  |
|  WorkerThread / JohnWorkerThread         |
+------------------------------------------+
          |                |
          | pyqtSignal     | method calls
          |                |
+------------------------------------------+
|         Backend Layer                    |
|  ArchiveBackend    JohnBackend           |
|  (subprocess->7z)  (subprocess->john)    |
+------------------------------------------+
          |                |
          | subprocess     | subprocess
          |                |
+------------------------------------------+
|       External CLI Tools                 |
|  7z (p7zip-full)  john (JTR)            |
+------------------------------------------+
          |
+------------------------------------------+
|         Utility Layer                    |
|  encoding_utils                          |
|  (chardet + struct + mmap)               |
+------------------------------------------+
```

### 设计原则 | Design Principles

1. **GUI 与逻辑分离** | GUI/Logic Separation: GUI 层不直接调用外部命令，所有操作通过 Backend 层
2. **子进程隔离** | Subprocess Isolation: 所有外部工具（7z、john）通过 `subprocess.run()` 调用，崩溃不影响主进程
3. **异步非阻塞** | Async Non-Blocking: 长时操作（解压/压缩/破解）在 QThread 中执行，不阻塞 GUI 事件循环
4. **信号通信** | Signal Communication: 工作线程通过 `pyqtSignal` 与 GUI 通信（进度更新、完成通知）

---

## 核心模块详解 | Core Module Details

### ArchiveBackend (archive_backend.py)

所有压缩包操作的统一接口，封装 7z CLI 命令。

**关键方法 | Key Methods:**

| 方法 | 7z 命令 | 功能 |
|------|---------|------|
| `list_archive()` | `7z l -slt <archive>` | 列出文件，解析为 ArchiveInfo |
| `extract()` | `7z x <archive> -o<dir>` | 解压文件，后处理修复编码 |
| `compress()` | `7z a <output> <files>` | 创建压缩包 |
| `test_archive()` | `7z t <archive>` | CRC 完整性验证 |

**命令构建流程 | Command Building Flow:**
```
用户操作 -> ArchiveBackend.method()
         -> _run_7z(args, password, timeout)
         -> subprocess.run([7z] + args + [-p<pwd>], env={LANG=UTF-8}, timeout=N)
         -> 解析 stdout/stderr
         -> 返回结果
```

**编码处理** | Encoding handling: 解码 7z 输出时按优先级尝试 UTF-8 > GBK > UTF-8(replace)。列表操作后根据 encoding_mode 调用 `_fix_filename()` 修复文件名。

**密码传递** | Password passing: 通过 `-p<password>` 命令行参数传递。已知安全限制：运行期间密码在 `/proc/PID/cmdline` 可见。7z CLI 不支持 stdin 或环境变量方式。

### encoding_utils.py

编码检测/转换和 ZIP 伪加密检测的核心工具模块。

**编码函数 | Encoding Functions:**

| 函数 | 功能 |
|------|------|
| `fix_zip_filename(name, from_enc, to_enc)` | 将文件名从 from_enc 重编码为 to_enc |
| `auto_detect_zip_filename(name)` | 自动检测并修复文件名编码 |

**伪加密函数 | Pseudo-Encryption Functions:**

| 函数 | 功能 |
|------|------|
| `detect_zip_pseudo_encryption(filepath)` | 分析 ZIP 二进制结构检测伪加密 |
| `patch_pseudo_encryption(src, dst)` | 清除加密标志位生成修复副本 |

### john_backend.py

John the Ripper 集成后端，管理哈希提取和密码破解进程。

**核心流程 | Core Flow:**
```
压缩包 -> extract_hash()
       -> 选择 *2john 工具 (zip2john / rar2john / 7z2john)
       -> subprocess.run() 提取哈希
       -> 保存为临时哈希文件

哈希文件 -> crack()
        -> 构建 john 命令 (--wordlist / --incremental / --mask)
        -> subprocess.Popen() 启动破解进程
        -> 监控进程输出

破解完成 -> show_cracked()
         -> john --show <hash_file>
         -> 解析输出提取密码
```

**支持的 *2john 工具映射 | Supported *2john Tool Mapping:**

| 压缩格式 | 哈希提取工具 |
|----------|-------------|
| .zip | zip2john |
| .rar | rar2john |
| .7z | 7z2john (Perl 脚本) |

---

## 线程模型 | Threading Model

```
主线程 (Main Thread)
|-- Qt 事件循环
|-- GUI 渲染和用户交互
|-- 信号槽连接
|
+-- WorkerThread (QThread)
|   |-- 解压操作 | Extract operation
|   |-- 压缩操作 | Compress operation
|   |-- 测试操作 | Test operation
|   |-- 添加文件 | Add files
|   +-- pyqtSignal: finished(bool, str), progress(str, int)
|
+-- JohnWorkerThread (QThread)
    |-- 密码破解（可运行数小时）| Password cracking (may run for hours)
    +-- pyqtSignal: finished(JohnResult), status_update(str)
```

### 线程安全措施 | Thread Safety Measures

1. **数据隔离** | Data Isolation: 工作线程只通过信号返回结果，不直接操作 GUI 控件
2. **互斥保护** | Mutual Exclusion: `_is_worker_busy()` 检查防止同时启动多个操作
3. **优雅终止** | Graceful Termination: JTR 进程通过 `SIGTERM` 信号停止，窗口关闭时检查并终止活跃线程

---

## 编码处理管线 | Encoding Pipeline

### 问题根源 | Root Cause

ZIP 格式规范（PKWARE APPNOTE）规定文件名使用 CP437 编码，但中国 Windows 软件（如 WinRAR）实际使用 GBK 编码。7z 在 Linux 上读取时按 CP437 解码，导致中文变成乱码。

ZIP format spec (PKWARE APPNOTE) mandates CP437 for filenames, but Chinese Windows software (e.g., WinRAR) uses GBK. 7z on Linux decodes as CP437, causing garbled Chinese.

### 修复流程 | Fix Flow

```
原始字节: [B4 F3 BA C3]  (GBK 编码的 "大好")
      |
      v
7z 输出: "xxxxx"  (7z 按 CP437 解码的结果)
      |
      v
CP437 编码: [B4 F3 BA C3]  (编码回字节)
      |
      v
chardet 检测: "gb2312" (confidence: 0.99)
      |
      v
GBK 解码: "大好"  (正确的中文)
```

### 编码检测优先级 | Encoding Detection Priority

chardet 检测不确定时，按以下顺序尝试解码：
1. GBK (中国大陆最常用)
2. GB18030 (GBK 超集)
3. Big5 (繁体中文)
4. Shift-JIS (日文)
5. EUC-JP (日文 Unix)
6. EUC-KR (韩文)

---

## 伪加密检测算法 | Pseudo-Encryption Detection Algorithm

### ZIP 文件结构 | ZIP File Structure

```
ZIP 文件布局 | ZIP File Layout:

[Local File Header 1] [File Data 1]
[Local File Header 2] [File Data 2]
...
[Central Directory Header 1]
[Central Directory Header 2]
...
[End of Central Directory Record]
```

### 关键二进制偏移 | Key Binary Offsets

**Local File Header (LFH):**
```
偏移 | Offset    字段 | Field              大小 | Size
0              签名 0x04034b50           4 bytes
4              版本                      2 bytes
6              通用标志位(bit 0=加密)    2 bytes    <-- 检查点
8              压缩方法                  2 bytes
...
```

**Central Directory Header (CDH):**
```
偏移 | Offset    字段 | Field              大小 | Size
0              签名 0x02014b50           4 bytes
...
8              通用标志位(bit 0=加密)    2 bytes    <-- 检查点
...
```

### 检测逻辑 | Detection Logic

```python
# 伪代码 | Pseudocode:
for each file entry:
    lfh_flag = read LFH general_purpose_bit at offset+6
    cdh_flag = read CDH general_purpose_bit at offset+8

    lfh_encrypted = lfh_flag & 0x0001
    cdh_encrypted = cdh_flag & 0x0001

    if lfh_encrypted != cdh_encrypted:
        -> SUSPICIOUS: LFH/CDH flag mismatch

    if lfh_encrypted and cdh_encrypted:
        data_start = read file data start
        if data starts with known signature (PNG/JPEG/PDF/PK):
            -> SUSPICIOUS: flag set but data not encrypted
```

### 内存效率 | Memory Efficiency

使用 `mmap` 内存映射代替 `f.read()` 加载整个文件：
- **mmap**: 按需加载页面，由操作系统管理物理内存，支持任意大小文件
- **f.read()**: 将整个文件加载到 Python 堆内存，大文件可能导致 OOM

---

## John the Ripper 集成 | JTR Integration

### 架构 | Architecture

```
+-------------------+       +-----------------+       +------------------+
| JohnDialog (GUI)  | ----> | JohnBackend     | ----> | john CLI         |
| - 哈希显示        |       | - extract_hash()|       | - zip2john       |
| - 模式选择        |       | - crack()       |       | - rar2john       |
| - 进度监控        |       | - stop()        |       | - john --wordlist|
| - 结果展示        |       | - show_cracked()|       | - john --show    |
+-------------------+       +-----------------+       +------------------+
         |                          |
         | pyqtSignal               | subprocess
         v                          v
+-------------------+       +-----------------+
| JohnWorkerThread  |       | 临时文件         |
| - QThread 异步    |       | - hash.txt      |
| - 进度更新        |       | - john.pot      |
+-------------------+       +-----------------+
```

### 四种攻击模式 | Four Attack Modes

| 模式 | john 参数 | 原理 | 速度 |
|------|-----------|------|------|
| Wordlist | `--wordlist=dict.txt` | 逐个尝试字典中的密码 | 快（取决于字典大小） |
| Incremental | `--incremental` | 暴力尝试所有字符组合 | 极慢（指数级增长） |
| Single | `--single` | 基于用户信息生成变体 | 快 |
| Mask | `--mask=?a?a?a?a` | 按模式规则生成 | 中等 |

---

## 安全设计 | Security Design

### 路径遍历防护 | Path Traversal Protection

解压后重命名文件时，验证新路径不会逃出目标目录：

```python
real_dir = os.path.realpath(directory)
new_path = os.path.join(root, fixed_name)
if not os.path.realpath(new_path).startswith(real_dir + os.sep):
    continue  # 跳过危险路径 | Skip dangerous path
```

### 命令注入防护 | Command Injection Protection

- 使用列表形式的 `subprocess.run(cmd_list)` 而非字符串拼接
- 7z 路径通过 `shutil.which()` 验证，确保是真实的可执行文件

### 密码安全 | Password Security

- 已知限制：密码通过命令行参数传递，运行期间可通过 `/proc/PID/cmdline` 查看
- 这是 7z CLI 的设计限制，不支持 stdin 或环境变量方式
- 子进程执行时间短（秒级），暴露窗口有限

### mmap 安全 | mmap Safety

- 伪加密检测使用 `ACCESS_READ` 只读模式，不会意外修改原文件
- 修复操作先复制到新文件再修改，确保原文件不变
- 空文件处理：捕获 `ValueError`（mmap 不能映射空文件）

---

## 打包与分发 | Packaging and Distribution

### 四种包格式对比 | Four Package Formats Comparison

| 格式 | 构建方式 | 依赖管理 | 运行环境 |
|------|---------|---------|---------|
| **DEB** | `dpkg-deb --build` | `Depends: python3-pyqt6, p7zip-full` | Debian/Ubuntu 系统 Python |
| **RPM** | `rpmbuild -ba` (Fedora 容器) | `Requires: python3-qt6, p7zip` | Fedora/RHEL 系统 Python |
| **AppImage** | 手动构建 (runtime+squashfs) | pip install 到 AppDir | 任何 Linux (自带 Python) |
| **Flatpak** | `flatpak-builder` | KDE 6.7 runtime + pip | 沙箱环境 |

### AppImage 构建细节 | AppImage Build Details

ArkManager 的 AppImage 使用手动构建方式而非 appimagetool，原因是 appimagetool continuous 版本的内置 mksquashfs 只支持 zstd 压缩，而许多 Linux 系统（特别是旧版内核）的 squashfuse 不支持 zstd 解压。

构建流程：
1. 创建 AppDir 目录结构（AppRun + .desktop + 图标 + Python + 应用代码 + 7z）
2. 下载 type2-runtime（AppImage ELF 头部）
3. 使用系统 `mksquashfs` 以 gzip 压缩创建 squashfs 镜像
4. 拼接：`cat runtime squashfs.img > AppImage`
5. 添加执行权限

---

## CI/CD 流程 | CI/CD Pipeline

### CI 工作流 (ci.yml)

**触发条件 | Triggers:** push to main / PR to main

```
Python 3.10 --+
Python 3.11 --+--> ruff check -> pytest tests/ -v
Python 3.12 --+
```

- 矩阵策略在 3 个 Python 版本上并行测试
- `QT_QPA_PLATFORM=offscreen` 启用无头 Qt 测试
- 安装系统依赖：p7zip-full（测试需要真实 7z 命令）、OpenGL 库（PyQt6 导入需要）

### Release 工作流 (release.yml)

**触发条件 | Triggers:** push tag v* / workflow_dispatch

```
build-deb (Ubuntu) ------------+
build-rpm (Fedora container) --+
build-appimage (Ubuntu) -------+--> release (下载构件 -> 创建 GitHub Release)
build-flatpak (Ubuntu) --------+   (continue-on-error: true)
```

- 4 个构建任务并行执行
- Flatpak 构建标记为 `continue-on-error: true`（PyQt6 源码编译易失败）
- Release 任务在所有构建完成后运行，上传所有成功的构件
