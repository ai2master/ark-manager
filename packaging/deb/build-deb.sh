#!/bin/bash
# ==============================================================================
# ArkManager DEB 包构建脚本 | ArkManager DEB Package Build Script
# ==============================================================================
#
# 功能说明 | Description:
#   构建 Debian/Ubuntu 系列发行版使用的 .deb 安装包。
#   DEB 是 Debian 系 Linux 的标准软件包格式，被 Ubuntu、Linux Mint、
#   Deepin 等众多发行版使用。
#
#   Builds a .deb package for Debian/Ubuntu family distributions.
#   DEB is the standard package format for Debian-based Linux, used by
#   Ubuntu, Linux Mint, Deepin, and many other distributions.
#
# DEB 包结构 | DEB Package Structure:
#   DEBIAN/control             - 包元数据（名称、版本、依赖）| Package metadata
#   usr/bin/arkmanager         - 命令行启动脚本 | CLI launcher script
#   usr/lib/python3/dist-packages/arkmanager/  - Python 应用代码 | App code
#   usr/share/applications/    - .desktop 桌面集成文件 | Desktop integration
#   usr/share/icons/           - 应用图标 | Application icon
#   usr/share/doc/             - 版权和文档 | Copyright and documentation
#
# 依赖 | Dependencies:
#   - dpkg-dev（提供 dpkg-deb 命令 | Provides dpkg-deb command）
#
# 用法 | Usage:
#   bash build-deb.sh [VERSION]
#   例如 | Example: bash build-deb.sh 1.0.1
# ==============================================================================

set -e  # 任何命令失败立即退出 | Exit immediately on any command failure

# -------------------- 配置参数 | Configuration --------------------
VERSION="${1:-1.0.0}"                 # 版本号 | Version number
PACKAGE_NAME="arkmanager"             # 包名（小写，Debian 规范）| Package name (lowercase, Debian convention)
BUILD_DIR="$(mktemp -d)"              # 创建临时构建目录 | Create temporary build directory
PKG_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_amd64"  # 包根目录 | Package root directory

echo "Building DEB package v${VERSION}..."

# ==================== 第1步：创建 FHS 目录结构 ====================
# ==================== Step 1: Create FHS Directory Structure ====================
# 遵循 Debian 打包规范和 FHS（文件系统层次标准）
# Follows Debian packaging guidelines and FHS (Filesystem Hierarchy Standard)
mkdir -p "${PKG_DIR}/DEBIAN"                                          # Debian 控制文件目录 | Debian control files
mkdir -p "${PKG_DIR}/usr/bin"                                          # 可执行文件 | Executables
mkdir -p "${PKG_DIR}/usr/lib/python3/dist-packages"                    # Python 包目录 | Python packages
mkdir -p "${PKG_DIR}/usr/share/applications"                           # .desktop 文件 | Desktop entries
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps"           # SVG 图标 | SVG icons
mkdir -p "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}"                   # 文档 | Documentation

# ==================== 第2步：生成 DEBIAN/control 控制文件 ====================
# ==================== Step 2: Generate DEBIAN/control File ====================
# control 文件定义包的元数据，是 DEB 包的核心配置文件。
# dpkg/apt 依赖此文件进行包管理、依赖解析和信息展示。
# The control file defines package metadata and is the core config of a DEB package.
# dpkg/apt relies on this for package management, dependency resolution, and display.
# 字段说明 | Field descriptions:
#   Package:      包名（小写，只含字母数字和连字符）| Package name
#   Version:      语义化版本号 | Semantic version number
#   Section:      软件类别（utils=工具类）| Software category
#   Architecture: 目标架构（amd64=x86_64）| Target architecture
#   Depends:      运行时必需依赖 | Required runtime dependencies
#   Recommends:   推荐但非必需的依赖 | Recommended but optional dependencies
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.9), python3-pyqt6, python3-chardet, p7zip-full
Recommends: john
Description: 7-Zip based archive manager for Linux
 ArkManager is a GUI archive manager that uses 7z CLI backend.
 Features include Chinese filename encoding support (GBK/GB18030/Big5),
 archive comment display, fake encryption detection, Chinese password
 support, and John the Ripper integration for password recovery.
Maintainer: ArkManager Contributors <arkmanager@users.noreply.github.com>
Homepage: https://github.com/ai2master/ark-manager
EOF

# ==================== 第3步：复制应用文件 ====================
# ==================== Step 3: Copy Application Files ====================
# 将 Python 包复制到系统 Python 路径，dpkg 安装时会放到对应位置
# Copy Python package to system Python path; dpkg places it accordingly on install
cp -r arkmanager "${PKG_DIR}/usr/lib/python3/dist-packages/"

# ==================== 第4步：创建命令行启动脚本 ====================
# ==================== Step 4: Create CLI Launcher Script ====================
# 启动脚本让用户可以通过 "arkmanager" 命令直接运行应用
# Launcher script allows users to run the app via the "arkmanager" command
cat > "${PKG_DIR}/usr/bin/arkmanager" << 'LAUNCHER'
#!/bin/bash
exec python3 -m arkmanager "$@"
LAUNCHER
chmod +x "${PKG_DIR}/usr/bin/arkmanager"

# ==================== 第5步：安装桌面集成文件 ====================
# ==================== Step 5: Install Desktop Integration Files ====================
# .desktop 文件使应用出现在系统应用菜单中 | .desktop file adds app to system application menu
cp resources/arkmanager.desktop "${PKG_DIR}/usr/share/applications/"
# SVG 图标可被桌面环境自动缩放到任意尺寸 | SVG icon auto-scales to any size by desktop environments
cp resources/arkmanager.svg "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/"

# ==================== 第6步：生成版权文件 ====================
# ==================== Step 6: Generate Copyright File ====================
# Debian 规范要求每个包必须包含版权声明文件
# Debian policy requires every package to include a copyright file
cat > "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: ArkManager
License: GPL-3.0+

Files: *
Copyright: 2024 ArkManager Contributors
License: GPL-3.0+
EOF

# ==================== 第7步：构建 DEB 包 ====================
# ==================== Step 7: Build DEB Package ====================
# dpkg-deb --build 将目录打包为 .deb 文件
# 它会验证 control 文件格式、计算 md5sum、生成 ar 归档
# dpkg-deb --build packages the directory into a .deb file.
# It validates the control file, computes md5sums, and creates an ar archive.
dpkg-deb --build "${PKG_DIR}"
# 将生成的 .deb 移动到项目根目录 | Move generated .deb to project root
cp "${PKG_DIR}.deb" "./${PACKAGE_NAME}_${VERSION}_amd64.deb"

echo "DEB package built: ${PACKAGE_NAME}_${VERSION}_amd64.deb"
# 清理临时构建目录 | Clean up temporary build directory
rm -rf "${BUILD_DIR}"
