# ArkManager 产品介绍 | Product Overview

## 目录 | Table of Contents

- [一句话介绍 | Tagline](#一句话介绍--tagline)
- [核心痛点 | Problems We Solve](#核心痛点--problems-we-solve)
- [核心功能 | Key Features](#核心功能--key-features)
- [功能详解 | Feature Details](#功能详解--feature-details)
- [竞品对比 | Comparison](#竞品对比--comparison)
- [使用场景 | Use Cases](#使用场景--use-cases)
- [技术亮点 | Technical Highlights](#技术亮点--technical-highlights)
- [支持的格式 | Supported Formats](#支持的格式--supported-formats)
- [安装包 | Downloads](#安装包--downloads)
- [开源协议 | License](#开源协议--license)
- [未来规划 | Roadmap](#未来规划--roadmap)

---

## 一句话介绍 | Tagline

**ArkManager** -- Linux 上首个专注中文编码处理的 7-Zip GUI 压缩包管理器，集成伪加密检测和密码恢复功能。

**ArkManager** -- The first 7-Zip GUI archive manager for Linux focused on Chinese encoding handling, with fake encryption detection and password recovery integration.

---

## 核心痛点 | Problems We Solve

### 痛点一：中文文件名乱码 | Chinese Filename Garbling

**问题** | Problem:
在 Windows 上用 WinRAR / 7-Zip 创建的 ZIP 压缩包，文件名使用 GBK 编码。在 Linux 上解压时，由于系统默认 UTF-8，文件名会变成乱码（如 `ÊÀ½çÄúºÃ.txt`）。

**影响范围** | Impact:
- 中国约 30% 的 ZIP 压缩包受此问题影响（参考 7-Zip Bug #2198）
- 这是 ZIP 格式的历史设计缺陷：标准规定 CP437 编码，但 Windows 软件使用本地编码
- 所有现有 Linux 压缩工具（File Roller、Ark、PeaZip）都无法完善解决此问题

**ArkManager 方案** | ArkManager Solution:
- **自动检测**编码：使用 chardet 库智能识别 GBK/GB18030/Big5/Shift-JIS
- **强制指定**编码：一键切换为 GBK、GB18030、Big5、Shift-JIS 等
- **预览和解压均支持**：预览时修复显示，解压后自动重命名文件
- **多编码覆盖**：支持简体中文、繁体中文、日文、韩文等 12 种常见编码

### 痛点二：Linux 缺少功能完整的压缩 GUI | Lack of Full-Featured Archive GUI on Linux

**问题** | Problem:
- File Roller (GNOME): 功能有限，不支持高级加密选项，不显示压缩包注释
- Ark (KDE): 需要大量 KDE/Qt 依赖，非 KDE 环境安装臃肿
- PeaZip: 界面老旧（Lazarus/Free Pascal），中文编码支持不完善
- 7-Zip GUI: 仅 Windows 原生，Linux 需要 Wine

**ArkManager 方案** | ArkManager Solution:
- 轻量 PyQt6 应用，仅依赖 PyQt6 + p7zip-full + chardet
- 无桌面环境绑定，在 GNOME、KDE、XFCE 等任何桌面环境下都能运行
- 界面参考 7-Zip Windows 版设计，上手无门槛
- Material Design 风格的现代化 UI

### 痛点三：压缩包伪加密 | Archive Fake Encryption

**问题** | Problem:
部分 CTF 竞赛题目和恶意软件使用 ZIP 伪加密技术 -- 修改 ZIP 文件头的加密标志位但不实际加密数据内容。常规解压工具会要求输入密码，但实际上不需要密码就能解压。

现有工具无法自动识别伪加密，需要手动用十六进制编辑器分析。

**ArkManager 方案** | ArkManager Solution:
- 一键检测：分析 ZIP 二进制结构中 LFH/CDH 加密标志位的一致性
- 智能判断：对比本地文件头和中央目录头的加密标志，检测数据是否真正加密
- 一键修复：自动清除伪加密标志位，生成可正常解压的副本
- 安全操作：使用 mmap 内存映射，原文件不受影响

### 痛点四：中文密码支持不佳 | Poor Chinese Password Support

**问题** | Problem:
许多 Linux 压缩工具对中文密码处理不当，导致用中文密码加密或解密时出错。问题根源在于编码传递不一致（UTF-8 vs GBK vs locale-dependent）。

**ArkManager 方案** | ArkManager Solution:
- 通过正确的 UTF-8 编码传递密码给 7z
- 7z 原生支持 UTF-8 中文密码
- 加密和解密均完美工作

---

## 核心功能 | Key Features

| 功能 | 说明 |
|------|------|
| 压缩/解压 | 支持 20+ 种格式：7z, ZIP, RAR, TAR, GZ, BZ2, XZ, ZST, CAB, ISO 等 |
| 中文编码处理 | 自动检测 + 强制 GBK/GB18030/Big5/Shift-JIS，预览和解压均可用 |
| 压缩包注释 | 右侧面板显示 ZIP 注释，支持中文注释正确显示 |
| 伪加密检测 | 分析 LFH/CDH 标志位不一致，可一键检测并去除伪加密 |
| 中文密码 | 加密/解密均完美支持中文字符密码 |
| 密码恢复 | 集成 John the Ripper，支持字典/暴力/单字/掩码四种攻击模式 |
| 自动创建父目录 | 解压时可选自动创建与压缩包同名的文件夹 |
| 文件拖拽 | 直接拖拽压缩包到窗口打开 |
| 完整性测试 | CRC 校验验证压缩包是否损坏 |
| 高级压缩选项 | 压缩级别/方法/固实/分卷/加密文件名 |
| 多格式创建 | 可创建 7z/ZIP/TAR/GZ/BZ2/XZ/WIM 格式 |
| 文件添加 | 向已有压缩包添加文件 |

---

## 功能详解 | Feature Details

### 1. 中文文件名编码处理 | Chinese Filename Encoding

**6 种编码模式 | 6 Encoding Modes:**

| 模式 | 编码 | 适用场景 |
|------|------|---------|
| Auto Detect | chardet 自动识别 | 默认模式，适用于大多数情况 |
| Force GBK | GBK (CP936) | 中国大陆 Windows 创建的压缩包 |
| Force GB18030 | GB18030 | 包含生僻字的中文文件名 |
| Force Big5 | Big5 | 繁体中文（台湾、香港）压缩包 |
| Force Shift-JIS | Shift-JIS | 日文 Windows 创建的压缩包 |
| No Conversion | 不转换 | 查看原始字节显示的文件名 |

**工作场景 | Usage Scenarios:**
- 预览文件列表时：实时切换编码，立即刷新显示效果
- 解压时：在解压对话框中独立选择编码模式
- 压缩时：ZIP 格式可选 UTF-8（推荐）或 GBK（兼容旧版 Windows）

### 2. ZIP 伪加密检测与修复 | ZIP Pseudo-Encryption Detection & Repair

**检测原理 | Detection Principle:**
1. 读取 ZIP 文件的本地文件头 (LFH) 和中央目录头 (CDH)
2. 比较两者的加密标志位 (bit 0)
3. 标志不一致 = 疑似人为篡改
4. 标志一致但数据以已知文件头开始 = 数据未真正加密

**修复方式 | Repair Method:**
- 创建原文件的副本
- 使用 mmap 内存映射在副本上清除所有加密标志位
- 原文件完全不受影响

### 3. John the Ripper 密码恢复 | Password Recovery

**支持的攻击模式 | Supported Attack Modes:**

| 模式 | 速度 | 适用场景 |
|------|------|---------|
| Wordlist（字典） | 快 | 有密码字典文件时首选 |
| Incremental（暴力） | 极慢 | 密码较短（1-6 位）时使用 |
| Single（单字） | 快 | 密码可能与文件名/用户名相关 |
| Mask（掩码） | 中等 | 已知密码部分特征（如"6位数字"） |

**支持的格式 | Supported Formats:**
- ZIP (zip2john)
- RAR (rar2john)
- 7z (7z2john)

**操作流程 | Workflow:**
提取哈希 -> 选择攻击模式 -> 配置参数 -> 开始破解 -> 查看结果

破解在后台线程中运行，不阻塞 GUI。可随时停止。

### 4. 压缩包注释显示 | Archive Comment Display

- ZIP 格式支持在文件末尾添加注释（最多 65535 字节）
- ArkManager 在右侧面板高亮显示注释内容
- 自动尝试多种编码解码：UTF-8 -> GBK -> GB18030 -> Latin-1
- 中文注释也能正确显示

### 5. 高级压缩选项 | Advanced Compression Options

- **压缩级别** (0-9): 0=仅存储，5=正常，9=极限压缩
- **压缩方法**: LZMA2, LZMA, PPMd, BZip2, Deflate, Copy
- **固实压缩** (7z): 将所有文件视为一个数据流，压缩率更高
- **分卷压缩**: 将大压缩包分割为多个小文件（如 100m, 4g）
- **加密文件名** (7z): 连文件名也加密，需要密码才能查看列表
- **ZIP 编码选择**: UTF-8（国际兼容）或 GBK（中文 Windows 兼容）

---

## 竞品对比 | Comparison

| 功能 | ArkManager | PeaZip | File Roller | Ark (KDE) | 7-Zip (Wine) |
|------|:---:|:---:|:---:|:---:|:---:|
| 中文编码自动检测 | Y | - | - | - | - |
| 强制 GBK/Big5/SJIS 编码 | Y | - | - | - | - |
| 伪加密检测与修复 | Y | - | - | - | - |
| John the Ripper 集成 | Y | - | - | - | - |
| 压缩包注释显示 | Y | Y | - | Y | Y |
| 中文密码完整支持 | Y | ~ | ~ | ~ | Y |
| 轻量无桌面依赖 | Y | Y | GNOME | KDE | Wine |
| 原生 Linux 运行 | Y | Y | Y | Y | - |
| 20+ 格式支持 | Y | Y | Y | Y | Y |
| 固实/分卷/加密文件名 | Y | Y | - | ~ | Y |
| Material Design UI | Y | - | - | - | - |
| 4 种安装包格式 | Y | Y | - | - | - |

图例 | Legend: Y = 支持, ~ = 部分支持, - = 不支持

---

## 使用场景 | Use Cases

### 日常办公 | Daily Office Work
解压从 Windows 同事收到的中文文件名 ZIP 压缩包。切换到 "Force GBK" 编码模式即可正确显示和解压。

### CTF 竞赛 | CTF Competitions
- 使用伪加密检测功能识别和去除 ZIP 伪加密
- 使用 John the Ripper 集成破解弱密码压缩包
- 支持 ZIP、RAR、7z 三种常见 CTF 压缩格式

### 安全审计 | Security Auditing
- 检查压缩包是否使用伪加密（标志位篡改）
- 测试密码强度（字典攻击成功 = 弱密码）
- 验证压缩包完整性（CRC 校验）

### 跨平台协作 | Cross-Platform Collaboration
- 在 Linux 上处理 Windows 创建的中文压缩包
- 创建压缩包时选择 UTF-8 编码确保跨平台兼容
- 或选择 GBK 编码确保旧版 Windows 兼容

### 系统管理 | System Administration
- 查看 RPM/DEB/ISO 等系统包的内部结构
- 测试下载的压缩包完整性
- 便携的 AppImage 版本无需安装即可使用

---

## 技术亮点 | Technical Highlights

1. **mmap 内存映射** | Memory-Mapped I/O:
   伪加密检测和修复使用 mmap 而非 f.read()，由操作系统按需加载页面，支持处理任意大小的 ZIP 文件而不会 OOM。

2. **子进程安全隔离** | Subprocess Security Isolation:
   所有外部工具（7z、john）通过 subprocess 列表参数调用，防止命令注入。7z 路径通过 shutil.which() 验证。

3. **路径遍历防护** | Path Traversal Protection:
   解压后重命名文件时，使用 os.path.realpath() 验证新路径不会逃出目标目录，防止恶意压缩包的路径遍历攻击。

4. **QThread 异步架构** | QThread Async Architecture:
   所有长时操作在工作线程中执行，通过 pyqtSignal 与 GUI 通信，确保界面始终响应流畅。

5. **手动 AppImage 构建** | Manual AppImage Assembly:
   绕过 appimagetool 的 zstd 限制，手动拼接 type2-runtime + gzip squashfs，确保在所有 Linux 系统上兼容运行。

6. **多编码容错解码** | Multi-Encoding Fallback Decoding:
   7z 输出和 ZIP 注释均使用优先级链解码（UTF-8 -> GBK -> GB18030 -> Latin-1），最大限度减少乱码。

---

## 支持的格式 | Supported Formats

### 完全支持（读写）| Full Support (Read/Write)

7z, ZIP, TAR, GZ (tar.gz/tgz), BZ2 (tar.bz2/tbz2), XZ (tar.xz/txz), Zstandard (zst/tar.zst), WIM

### 只读支持 | Read-Only Support

RAR, CAB, ISO, ARJ, CPIO, RPM, DEB, LZH, LZMA, Z

> 只读格式受限于 7z 的能力，7z 可以解压但不能创建这些格式。
> Read-only formats are limited by 7z capabilities; 7z can extract but not create these formats.

---

## 安装包 | Downloads

通过 [GitHub Releases](https://github.com/ai2master/ark-manager/releases) 提供 4 种安装包：

| 格式 | 适用平台 | 特点 |
|------|---------|------|
| `.deb` | Ubuntu, Debian, Linux Mint, Deepin | 系统包管理器安装，自动处理依赖 |
| `.rpm` | Fedora, CentOS, openSUSE, RHEL | 系统包管理器安装，自动处理依赖 |
| `.AppImage` | 任何 Linux 发行版 | 免安装，下载即用，单文件便携 |
| `.flatpak` | 任何 Linux 发行版 | 沙箱化运行，安全隔离 |

---

## 开源协议 | License

**GPL-3.0-or-later** -- 自由使用、修改和分发。

GNU General Public License v3.0 or later -- Free to use, modify, and distribute.

完整协议文本见项目根目录 [LICENSE](../LICENSE) 文件。

---

## 未来规划 | Roadmap

- [ ] 多语言界面支持（i18n: zh-CN / en-US）
- [ ] 压缩包内文件预览（文本、图片）
- [ ] 批量解压模式
- [ ] 自定义主题/暗色模式
- [ ] 压缩包内搜索功能
- [ ] 右键菜单集成（Nautilus/Dolphin）
- [ ] 更多 *2john 格式支持
