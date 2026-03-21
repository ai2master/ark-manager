#!/bin/bash
# ==============================================================================
# ArkManager AppImage 构建脚本 | ArkManager AppImage Build Script
# ==============================================================================
#
# 功能说明 | Description:
#   将 ArkManager Python 应用打包为独立的 AppImage 可执行文件。
#   AppImage 是一种 Linux 通用的便携式应用格式，无需安装即可运行。
#
#   Packages the ArkManager Python application into a self-contained AppImage
#   executable. AppImage is a universal portable app format for Linux that
#   runs without installation.
#
# 构建流程 | Build Process:
#   1. 创建 AppDir 目录结构（FHS 标准布局）
#      Create AppDir directory structure (FHS standard layout)
#   2. 用 pip 安装 PyQt6 + chardet 到 AppDir 内
#      Install PyQt6 + chardet into AppDir via pip
#   3. 复制应用代码、启动器、桌面文件和图标
#      Copy application code, launchers, desktop file, and icon
#   4. 下载 type2-runtime（AppImage 自挂载运行时）
#      Download type2-runtime (AppImage self-mounting runtime)
#   5. 用系统 mksquashfs 创建 gzip 压缩的 squashfs 镜像
#      Create gzip-compressed squashfs image using system mksquashfs
#   6. 拼接 runtime + squashfs = 最终 AppImage 文件
#      Concatenate runtime + squashfs = final AppImage file
#
# 为什么不用 appimagetool | Why not use appimagetool:
#   appimagetool (continuous) 自带的 mksquashfs 只支持 zstd 压缩，
#   而许多 Linux 发行版的 squashfuse 不支持 zstd，导致 AppImage 无法运行。
#   手动构建可以强制使用 gzip 压缩，确保最大兼容性。
#
#   appimagetool (continuous) bundles a mksquashfs that only supports zstd,
#   but many Linux distros' squashfuse doesn't support zstd, causing AppImage
#   launch failures. Manual build forces gzip compression for max compatibility.
#
# 依赖 | Dependencies:
#   - python3, pip          （Python 环境 | Python environment）
#   - squashfs-tools         （提供 mksquashfs 命令 | Provides mksquashfs）
#   - wget                   （下载 runtime | Download runtime）
#   - libfuse2               （运行时需要 | Required at runtime for FUSE mount）
#
# 用法 | Usage:
#   bash build-appimage.sh [VERSION]
#   例如 | Example: bash build-appimage.sh 1.0.1
# ==============================================================================

set -e  # 任何命令失败立即退出 | Exit immediately on any command failure

# -------------------- 配置参数 | Configuration --------------------
VERSION="${1:-1.0.0}"        # 版本号，默认 1.0.0 | Version number, defaults to 1.0.0
PACKAGE_NAME="ArkManager"   # 应用名称 | Application name

echo "Building AppImage v${VERSION}..."

# ==================== 第1步：创建 AppDir 目录结构 ====================
# ==================== Step 1: Create AppDir Directory Structure ====================
# AppDir 遵循 FHS（文件系统层次标准）布局：
#   usr/bin/             - 可执行启动脚本 | Executable launcher scripts
#   usr/lib/python3/     - Python 包和依赖 | Python packages and dependencies
#   usr/share/           - 桌面文件和图标 | Desktop files and icons
# AppDir follows FHS (Filesystem Hierarchy Standard) layout
APP_DIR="$(pwd)/${PACKAGE_NAME}.AppDir"
rm -rf "${APP_DIR}"  # 清除旧的构建目录 | Clean old build directory
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/lib/python3/dist-packages"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/scalable/apps"

# ==================== 第2步：安装 Python 依赖 ====================
# ==================== Step 2: Install Python Dependencies ====================
# 将 PyQt6 和 chardet 安装到 AppDir 内部，使 AppImage 自包含所有依赖。
# 2>/dev/null 抑制 pip 的警告输出，|| true 防止非关键错误中断构建。
# Install PyQt6 and chardet into AppDir so the AppImage is self-contained.
# 2>/dev/null suppresses pip warnings, || true prevents non-critical errors from aborting.
python3 -m pip install --target="${APP_DIR}/usr/lib/python3/dist-packages" \
    PyQt6 chardet 2>/dev/null || true

# ==================== 第3步：复制应用代码 ====================
# ==================== Step 3: Copy Application Code ====================
# 将 arkmanager Python 包复制到 AppDir 的 Python 路径中
# Copy the arkmanager Python package into AppDir's Python path
cp -r arkmanager "${APP_DIR}/usr/lib/python3/dist-packages/"

# ==================== 第4步：创建启动脚本 ====================
# ==================== Step 4: Create Launcher Scripts ====================
# 启动器脚本设置 PYTHONPATH 指向 AppDir 内的依赖，然后运行应用
# Launcher script sets PYTHONPATH to point to dependencies inside AppDir, then runs the app

# --- usr/bin/arkmanager: 主启动器 | Main launcher ---
cat > "${APP_DIR}/usr/bin/arkmanager" << 'LAUNCHER'
#!/bin/bash
# 获取脚本自身的绝对路径 | Get the absolute path of this script
HERE="$(dirname "$(readlink -f "$0")")"
# 设置 PYTHONPATH 指向 AppDir 内的 Python 包 | Set PYTHONPATH to AppDir's Python packages
export PYTHONPATH="${HERE}/../lib/python3/dist-packages:${PYTHONPATH}"
# 启动 arkmanager 主模块 | Launch arkmanager main module
exec python3 -m arkmanager "$@"
LAUNCHER
chmod +x "${APP_DIR}/usr/bin/arkmanager"

# --- AppRun: AppImage 入口点（type2-runtime 调用此脚本） ---
# --- AppRun: AppImage entry point (invoked by type2-runtime) ---
# AppRun 是 AppImage 标准要求的顶层入口脚本，
# type2-runtime 挂载 squashfs 后会执行此脚本。
# AppRun is the top-level entry script required by AppImage standard.
# The type2-runtime executes this after mounting the squashfs.
cat > "${APP_DIR}/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/dist-packages:${PYTHONPATH}"
exec python3 -m arkmanager "$@"
APPRUN
chmod +x "${APP_DIR}/AppRun"

# ==================== 第5步：安装桌面集成文件 ====================
# ==================== Step 5: Install Desktop Integration Files ====================
# .desktop 文件：Linux 桌面环境用于显示应用图标和启动信息
# .desktop file: used by Linux desktop environments for app icon and launch info
# 需要同时放在 AppDir 根目录（AppImage 标准）和 usr/share/ 下（FHS 标准）
# Must be placed both at AppDir root (AppImage standard) and usr/share/ (FHS standard)
cp resources/arkmanager.desktop "${APP_DIR}/"
cp resources/arkmanager.desktop "${APP_DIR}/usr/share/applications/"

# SVG 图标：矢量格式，适配任何分辨率 | SVG icon: vector format, scales to any resolution
cp resources/arkmanager.svg "${APP_DIR}/arkmanager.svg"
cp resources/arkmanager.svg "${APP_DIR}/usr/share/icons/hicolor/scalable/apps/"

# ==================== 第6步：手动组装 AppImage ====================
# ==================== Step 6: Manually Assemble AppImage ====================
# AppImage 文件格式 = type2-runtime（ELF 可执行头）+ squashfs（压缩文件系统）
# 运行时，runtime 通过 FUSE 挂载 squashfs 到临时目录，然后执行 AppRun。
# AppImage file format = type2-runtime (ELF executable header) + squashfs (compressed filesystem)
# At runtime, the runtime mounts squashfs via FUSE to a temp dir, then executes AppRun.
APPIMAGE_FILE="${PACKAGE_NAME}-${VERSION}-x86_64.AppImage"
RUNTIME_URL="https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64"

# --- 6a. 下载 type2-runtime ---
# --- 6a. Download type2-runtime ---
# type2-runtime 需要 libfuse2。如果目标系统无 libfuse2，
# 用户可以使用 --appimage-extract-and-run 参数自动解压运行。
# type2-runtime requires libfuse2. If target system lacks libfuse2,
# users can use --appimage-extract-and-run to auto-extract and run.
echo "Downloading AppImage runtime..."
wget -q "${RUNTIME_URL}" -O runtime-x86_64
chmod +x runtime-x86_64

# --- 6b. 创建 gzip 压缩的 squashfs 镜像 ---
# --- 6b. Create gzip-compressed squashfs image ---
# 使用系统 mksquashfs 而非 appimagetool 自带版本（自带版本只支持 zstd 压缩）。
# gzip 压缩兼容所有主流 Linux 发行版的 squashfuse 实现。
# Using system mksquashfs instead of appimagetool's bundled one (only supports zstd).
# gzip compression is compatible with squashfuse on all major Linux distributions.
# 参数说明 | Parameter explanation:
#   -root-owned   : 所有文件归 root 所有 | All files owned by root
#   -noappend     : 创建新镜像而非追加 | Create new image, don't append
#   -comp gzip    : 使用 gzip 压缩算法 | Use gzip compression algorithm
#   -b 131072     : 128KB 块大小（平衡压缩率和随机访问性能）| 128KB block size
#   -no-xattrs    : 不保存扩展属性（减小体积）| Skip extended attributes (smaller size)
echo "Creating squashfs with gzip compression..."
mksquashfs "${APP_DIR}" squashfs.img \
    -root-owned -noappend \
    -comp gzip \
    -b 131072 \
    -no-xattrs

# --- 6c. 拼接 runtime + squashfs = AppImage ---
# --- 6c. Concatenate runtime + squashfs = AppImage ---
# cat 命令将两个二进制文件拼接：
#   [runtime ELF header (自挂载代码)] + [squashfs filesystem (应用数据)]
# 执行时，内核加载 ELF 头部的 runtime 代码，runtime 在自身文件中找到
# squashfs 偏移量并通过 FUSE 挂载它。
# cat concatenates two binary files:
#   [runtime ELF header (self-mounting code)] + [squashfs filesystem (app data)]
# On execution, the kernel loads the ELF runtime code, which finds the squashfs
# offset within its own file and mounts it via FUSE.
echo "Assembling AppImage..."
cat runtime-x86_64 squashfs.img > "${APPIMAGE_FILE}"
chmod +x "${APPIMAGE_FILE}"

# ==================== 第7步：清理临时文件 ====================
# ==================== Step 7: Clean Up Temporary Files ====================
rm -f runtime-x86_64 squashfs.img  # 删除中间产物 | Remove intermediate artifacts

echo "AppImage built: ${APPIMAGE_FILE}"
rm -rf "${APP_DIR}"  # 删除 AppDir 构建目录 | Remove AppDir build directory
