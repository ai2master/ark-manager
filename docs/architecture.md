# ArkManager 技术架构 | Technical Architecture

## 技术栈 | Tech Stack

| 组件 | 技术 | 说明 |
|------|------|------|
| GUI 框架 | PyQt6 | 跨平台 Qt6 Python 绑定 |
| 压缩后端 | 7z CLI (p7zip) | 通过子进程调用 `7z` 命令 |
| 编码检测 | chardet | 自动识别文件名编码 |
| 密码恢复 | John the Ripper CLI | 通过子进程调用 `john`/`zip2john` |
| 打包工具 | setuptools | Python 标准打包 |
| CI/CD | GitHub Actions | 自动构建 DEB/RPM/AppImage/Flatpak |

## 模块结构 | Module Structure

```
arkmanager/
├── __init__.py          # 版本信息 | Version info
├── __main__.py          # 入口点，Qt应用初始化，全局样式 | Entry point, Qt app, styles
├── main_window.py       # 主窗口GUI，所有对话框 | Main GUI window, all dialogs
├── archive_backend.py   # 7z CLI封装，压缩/解压/列表操作 | 7z CLI wrapper
├── john_backend.py      # John the Ripper CLI封装 | John the Ripper wrapper
└── encoding_utils.py    # 编码检测，伪加密检测与修复 | Encoding & pseudo-encryption tools
```

## 核心架构 | Core Architecture

### 分层设计 | Layered Design

```
┌──────────────────────────────────────┐
│            GUI Layer (PyQt6)         │
│  MainWindow / ExtractDialog /        │
│  CompressDialog / JohnDialog /       │
│  PseudoEncryptionDialog             │
├──────────────────────────────────────┤
│          Backend Layer               │
│  ArchiveBackend    JohnBackend       │
│  (7z subprocess)   (john subprocess) │
├──────────────────────────────────────┤
│         Utility Layer                │
│  encoding_utils (chardet + struct)   │
└──────────────────────────────────────┘
```

### ArchiveBackend

所有压缩/解压操作通过 `subprocess.run()` 调用 `7z` 命令完成：

- `list_archive()` → `7z l -slt <archive>` → 解析输出为 `ArchiveInfo`
- `extract()` → `7z x <archive> -o<dir>` → 提取后修复文件名编码
- `compress()` → `7z a <output> <files>` → 支持 `-mcu=on`(UTF-8) 和 `-mcp=936`(GBK)
- `test_archive()` → `7z t <archive>` → 验证完整性

密码通过 `-p<password>` 参数传递，7z 原生支持 UTF-8 编码的中文密码。

### 编码处理流程 | Encoding Pipeline

```
ZIP文件 → 7z输出原始文件名 → 编码模式判断
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                  auto          force          none
                    │             │             │
              chardet检测    cp437→GBK重编码    原样返回
              尝试CJK编码列表
                    │
                  修复后的文件名
```

### 伪加密检测 | Pseudo-Encryption Detection

直接读取 ZIP 二进制数据，分析：
1. **LFH/CDH 标志不一致**：本地文件头加密位 vs 中央目录头加密位
2. **加密标志 + 无加密数据**：设置了加密位但数据以已知文件头开头（PNG/JPEG/PDF等）

修复方式：清除 LFH（offset +6）和 CDH（offset +8）的 bit 0。

### John the Ripper 集成 | JTR Integration

```
压缩包 → zip2john/rar2john/7z2john → hash文件
                                         │
                                    john --wordlist
                                    john --incremental
                                    john --mask
                                         │
                                    john --show → 密码
```

所有 JTR 操作在 `QThread` 中异步执行，不阻塞 GUI。

## 线程模型 | Threading Model

- **主线程**：Qt 事件循环，GUI 渲染
- **WorkerThread**：解压/压缩等长时操作
- **JohnWorkerThread**：密码破解（可能运行数小时）

通过 `pyqtSignal` 在工作线程和 GUI 之间通信。

## 打包 | Packaging

| 格式 | 构建方式 | 依赖管理 |
|------|---------|---------|
| DEB | `dpkg-deb --build` | `Depends: python3-pyqt6, python3-chardet, p7zip-full` |
| RPM | `rpmbuild -ba` | `Requires: python3-qt6, python3-chardet, p7zip` |
| AppImage | `appimagetool` | pip install 到 AppDir |
| Flatpak | `flatpak-builder` | KDE 6.7 runtime + pip modules |

所有包在 GitHub Actions 中自动构建，tag push 触发 release workflow。
