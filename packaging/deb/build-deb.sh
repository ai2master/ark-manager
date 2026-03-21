#!/bin/bash
# 构建 ArkManager DEB 包 | Build ArkManager DEB package
# 用法 | Usage: bash build-deb.sh VERSION [DISTRO]
#   VERSION: 版本号 (如 1.1.2) | Version number
#   DISTRO:  jammy 或 noble (默认 noble) | jammy or noble (default noble)
#
# jammy (22.04): 内嵌 PyQt6 (pip) 因官方源无此包
#                Bundles PyQt6 from pip since system repos lack it
# noble (24.04): 依赖系统 python3-pyqt6 包
#                Depends on system python3-pyqt6 package

set -e

VERSION="${1:-1.0.0}"
DISTRO="${2:-noble}"
PACKAGE_NAME="arkmanager"
BUILD_DIR="$(mktemp -d)"
PKG_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_amd64"

echo "Building DEB package v${VERSION} for ${DISTRO}..."

# 创建目录结构 | Create directory structure
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/lib/python3/dist-packages"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}"

# 根据发行版设置依赖 | Set dependencies based on distro
if [ "${DISTRO}" = "jammy" ]; then
    # Ubuntu 22.04: 内嵌 PyQt6，依赖 Qt6 系统库
    # Ubuntu 22.04: bundle PyQt6, depend on Qt6 system libs
    DEPENDS="python3 (>= 3.10), python3-chardet, p7zip-full, libqt6widgets6, libqt6gui6, libqt6core6, libegl1"
    echo "Installing PyQt6 into package (bundled for jammy)..."
    python3 -m pip install --target="${PKG_DIR}/usr/lib/python3/dist-packages" \
        PyQt6 2>/dev/null || true
else
    # Ubuntu 24.04: 使用系统 PyQt6 包
    # Ubuntu 24.04: use system PyQt6 package
    DEPENDS="python3 (>= 3.12), python3-pyqt6, python3-chardet, p7zip-full"
fi

# 生成 control 文件 | Generate control file
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}~${DISTRO}
Section: utils
Priority: optional
Architecture: amd64
Depends: ${DEPENDS}
Recommends: john
Description: 7-Zip based archive manager for Linux
 ArkManager is a GUI archive manager that uses 7z CLI backend.
 Features include Chinese filename encoding support (GBK/GB18030/Big5),
 archive comment display, fake encryption detection, Chinese password
 support, and John the Ripper integration for password recovery.
Maintainer: ArkManager Contributors <arkmanager@users.noreply.github.com>
Homepage: https://github.com/ai2master/ark-manager
EOF

# 复制应用代码 | Copy application code
cp -r arkmanager "${PKG_DIR}/usr/lib/python3/dist-packages/"

# 创建启动脚本 | Create launcher script
cat > "${PKG_DIR}/usr/bin/arkmanager" << 'LAUNCHER'
#!/bin/bash
exec python3 -m arkmanager "$@"
LAUNCHER
chmod +x "${PKG_DIR}/usr/bin/arkmanager"

# 桌面集成 | Desktop integration
cp resources/arkmanager.desktop "${PKG_DIR}/usr/share/applications/"
cp resources/arkmanager.svg "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/"

# 版权文件 | Copyright file
cat > "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: ArkManager
License: GPL-3.0+

Files: *
Copyright: 2024 ArkManager Contributors
License: GPL-3.0+
EOF

# 构建 DEB 包 | Build DEB package
dpkg-deb --build "${PKG_DIR}"
DEB_NAME="${PACKAGE_NAME}_${VERSION}~${DISTRO}_amd64.deb"
cp "${PKG_DIR}.deb" "./${DEB_NAME}"

echo "DEB package built: ${DEB_NAME}"
rm -rf "${BUILD_DIR}"
