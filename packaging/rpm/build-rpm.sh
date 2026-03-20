#!/bin/bash
# ==============================================================================
# ArkManager RPM 包构建脚本 | ArkManager RPM Package Build Script
# ==============================================================================
#
# 功能说明 | Description:
#   构建 Fedora/RHEL/CentOS/openSUSE 使用的 .rpm 安装包。
#   RPM 是 Red Hat 系 Linux 的标准软件包格式。
#
#   Builds an .rpm package for Fedora/RHEL/CentOS/openSUSE distributions.
#   RPM is the standard package format for Red Hat family Linux.
#
# 构建流程 | Build Process:
#   1. 创建 rpmbuild 标准目录结构（BUILD/RPMS/SOURCES/SPECS/SRPMS）
#      Create rpmbuild standard directory structure
#   2. 将源码打包为 .tar.gz 放入 SOURCES/
#      Package source code as .tar.gz into SOURCES/
#   3. 用 sed 更新 .spec 文件中的版本号并放入 SPECS/
#      Update version in .spec file with sed and place in SPECS/
#   4. 执行 rpmbuild -ba 同时构建二进制 RPM 和源码 RPM
#      Run rpmbuild -ba to build both binary and source RPMs
#
# 依赖 | Dependencies:
#   - rpm-build, rpmdevtools  （RPM 构建工具 | RPM build tools）
#   - python3-devel           （Python 开发头文件 | Python dev headers）
#   - python3-setuptools, python3-pip, python3-wheel  （Python 打包工具）
#
# 用法 | Usage:
#   bash build-rpm.sh [VERSION]
#   例如 | Example: bash build-rpm.sh 1.0.1
#
# 注意 | Note:
#   此脚本应在 Fedora 容器或系统中运行，因为 rpmbuild 依赖 Fedora/RHEL 工具链。
#   在 GitHub Actions 中通过 Fedora Docker 容器运行。
#   This script should run in a Fedora container/system as rpmbuild depends on
#   Fedora/RHEL toolchain. Runs in a Fedora Docker container in GitHub Actions.
# ==============================================================================

set -e  # 任何命令失败立即退出 | Exit immediately on any command failure

# -------------------- 配置参数 | Configuration --------------------
VERSION="${1:-1.0.0}"        # 版本号 | Version number
PACKAGE_NAME="arkmanager"    # 包名 | Package name

echo "Building RPM package v${VERSION}..."

# ==================== 第1步：创建 rpmbuild 目录结构 ====================
# ==================== Step 1: Create rpmbuild Directory Structure ====================
# rpmbuild 要求固定的目录布局 | rpmbuild requires a fixed directory layout:
#   BUILD/    - 构建中间目录（解压+编译）| Build intermediate directory
#   RPMS/     - 生成的二进制 RPM 文件 | Generated binary RPM files
#   SOURCES/  - 源码压缩包 | Source tarballs
#   SPECS/    - RPM 规格文件 | RPM spec files
#   SRPMS/    - 源码 RPM 文件 | Source RPM files
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# ==================== 第2步：创建源码压缩包 ====================
# ==================== Step 2: Create Source Tarball ====================
# rpmbuild 要求源码以 "包名-版本号/" 为顶层目录的 .tar.gz 格式提供
# rpmbuild requires source as .tar.gz with "pkgname-version/" as top-level directory
TEMP_DIR=$(mktemp -d)
mkdir -p "${TEMP_DIR}/${PACKAGE_NAME}-${VERSION}"
# 只复制构建所需的文件（不包含测试、CI 等开发文件）
# Only copy files needed for building (exclude tests, CI, and dev files)
cp -r arkmanager pyproject.toml resources LICENSE README.md "${TEMP_DIR}/${PACKAGE_NAME}-${VERSION}/"
cd "${TEMP_DIR}"
tar czf ~/rpmbuild/SOURCES/${PACKAGE_NAME}-${VERSION}.tar.gz ${PACKAGE_NAME}-${VERSION}
cd -

# ==================== 第3步：准备 .spec 文件 ====================
# ==================== Step 3: Prepare .spec File ====================
# .spec 文件定义了 RPM 的构建指令和包元数据（类似 DEB 的 control 文件）
# 用 sed 动态替换 Version 字段以匹配当前构建版本
# .spec file defines RPM build instructions and package metadata (similar to DEB's control)
# Use sed to dynamically replace the Version field to match the current build version
sed "s/^Version:.*/Version:        ${VERSION}/" packaging/rpm/arkmanager.spec > ~/rpmbuild/SPECS/arkmanager.spec

# ==================== 第4步：执行 RPM 构建 ====================
# ==================== Step 4: Execute RPM Build ====================
# rpmbuild -ba 执行完整构建流程 | rpmbuild -ba runs the full build process:
#   %prep    → 解压源码（%autosetup）| Extract source (%autosetup)
#   %build   → 编译/构建（pip wheel）| Compile/build (pip wheel)
#   %install → 安装到 buildroot | Install into buildroot
#   %files   → 收集文件列表 → 生成 RPM | Collect file list → generate RPM
# -ba 表示同时构建二进制 RPM（-bb）和源码 RPM（-bs）
# -ba means build both binary RPM (-bb) and source RPM (-bs)
rpmbuild -ba ~/rpmbuild/SPECS/arkmanager.spec

echo "RPM package built in ~/rpmbuild/RPMS/"
# 清理临时目录 | Clean up temporary directory
rm -rf "${TEMP_DIR}"
