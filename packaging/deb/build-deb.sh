#!/bin/bash
set -e

VERSION="${1:-1.0.0}"
PACKAGE_NAME="arkmanager"
BUILD_DIR="$(mktemp -d)"
PKG_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_amd64"

echo "Building DEB package v${VERSION}..."

# Create directory structure
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/lib/python3/dist-packages"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}"

# Control file
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

# Copy application files
cp -r arkmanager "${PKG_DIR}/usr/lib/python3/dist-packages/"

# Create launcher script
cat > "${PKG_DIR}/usr/bin/arkmanager" << 'LAUNCHER'
#!/bin/bash
exec python3 -m arkmanager "$@"
LAUNCHER
chmod +x "${PKG_DIR}/usr/bin/arkmanager"

# Copy desktop entry and icon
cp resources/arkmanager.desktop "${PKG_DIR}/usr/share/applications/"
cp resources/arkmanager.svg "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/"

# Copyright
cat > "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: ArkManager
License: GPL-3.0+

Files: *
Copyright: 2024 ArkManager Contributors
License: GPL-3.0+
EOF

# Build
dpkg-deb --build "${PKG_DIR}"
cp "${PKG_DIR}.deb" "./${PACKAGE_NAME}_${VERSION}_amd64.deb"

echo "DEB package built: ${PACKAGE_NAME}_${VERSION}_amd64.deb"
rm -rf "${BUILD_DIR}"
