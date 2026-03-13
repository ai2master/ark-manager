# ArkManager 产品介绍 | Product Overview

## 一句话介绍 | Tagline

**ArkManager** -- Linux 上首个专注中文编码处理的 7-Zip GUI 压缩包管理器，集成伪加密检测和密码恢复功能。

## 痛点 | Problems We Solve

### 1. 中文文件名乱码

在 Windows 上用 WinRAR / 7-Zip 创建的 ZIP 压缩包，文件名使用 GBK 编码。在 Linux 上解压时，由于系统默认 UTF-8，文件名会变成乱码。**中国约 30% 的 ZIP 压缩包受此问题影响**（7-Zip Bug #2198）。

ArkManager 方案：
- **自动检测**编码：使用 chardet 智能识别 GBK/GB18030/Big5/Shift-JIS
- **强制指定**编码：一键切换为 GBK、GB18030 等
- **预览和解压均支持**：不仅是预览时修复，解压后的文件名也同步修正

### 2. Linux 缺少好用的压缩包 GUI

- File Roller (GNOME) 功能有限，不支持加密选项
- Ark (KDE) 需要大量 Qt/KDE 依赖
- PeaZip 界面老旧，中文编码支持不完善

ArkManager：轻量 PyQt6 应用，无桌面环境依赖，界面参考 7-Zip Windows 版。

### 3. 压缩包伪加密

部分 CTF 题目和恶意软件使用 ZIP 伪加密（修改加密标志位但不实际加密），常规工具无法识别。

ArkManager 直接分析二进制头部标志位，一键检测并去除伪加密。

### 4. 中文密码

许多工具对中文密码支持不佳。ArkManager 通过正确的 UTF-8 传递确保中文密码完美工作。

## 核心功能 | Key Features

| 功能 | 说明 |
|------|------|
| 压缩/解压 | 支持 20+ 种格式：7z, ZIP, RAR, TAR, GZ, BZ2, XZ, ZST, CAB, ISO 等 |
| 中文编码 | 自动检测 + 强制 GBK/GB18030/Big5/Shift-JIS，预览和解压均可用 |
| 压缩包备注 | 右侧面板黄色高亮显示，支持中文备注 |
| 伪加密检测 | 分析 LFH/CDH 标志位不一致，可一键去除 |
| 中文密码 | 加密/解密均完美支持中文字符 |
| 密码恢复 | 集成 John the Ripper，支持字典/暴力/掩码攻击 |
| 自动创建父目录 | 解压时可选自动创建同名文件夹 |
| 拖拽打开 | 直接拖拽压缩包到窗口 |

## 竞品对比 | Comparison

| 功能 | ArkManager | PeaZip | File Roller | Ark (KDE) | 7-Zip (Wine) |
|------|:---:|:---:|:---:|:---:|:---:|
| 中文编码自动检测 | v | - | - | - | - |
| 强制 GBK 编码 | v | - | - | - | - |
| 伪加密检测 | v | - | - | - | - |
| John the Ripper 集成 | v | - | - | - | - |
| 压缩包备注显示 | v | v | - | v | v |
| 中文密码 | v | ~ | ~ | ~ | v |
| 轻量无依赖 | v | v | GNOME | KDE | Wine |
| 原生 Linux | v | v | v | v | - |
| 多格式支持 (20+) | v | v | v | v | v |

## 使用场景 | Use Cases

- **日常办公**：解压从 Windows 同事收到的中文文件名 ZIP
- **CTF 竞赛**：伪加密检测 + John the Ripper 密码破解
- **安全审计**：检查压缩包加密方式是否为伪加密
- **跨平台协作**：确保压缩包在不同系统间文件名不乱码
- **批量处理**：命令行支持直接打开指定文件

## 安装包 | Downloads

通过 GitHub Releases 提供 4 种安装包：

- `.deb` -- Ubuntu, Debian, Linux Mint
- `.rpm` -- Fedora, CentOS, openSUSE
- `.AppImage` -- 任何 Linux（免安装，下载即用）
- `.flatpak` -- 任何 Linux（沙箱运行）

## 开源协议 | License

GPL-3.0-or-later -- 自由使用、修改和分发。
