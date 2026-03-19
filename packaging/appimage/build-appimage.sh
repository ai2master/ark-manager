#!/bin/bash
set -e

VERSION="${1:-1.0.0}"
PACKAGE_NAME="ArkManager"

echo "Building AppImage v${VERSION}..."

# Create AppDir structure
APP_DIR="$(pwd)/${PACKAGE_NAME}.AppDir"
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/lib/python3/dist-packages"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/scalable/apps"

# Install Python and dependencies into AppDir
python3 -m pip install --target="${APP_DIR}/usr/lib/python3/dist-packages" \
    PyQt6 chardet 2>/dev/null || true

# Copy application
cp -r arkmanager "${APP_DIR}/usr/lib/python3/dist-packages/"

# Create launcher
cat > "${APP_DIR}/usr/bin/arkmanager" << 'LAUNCHER'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="${HERE}/../lib/python3/dist-packages:${PYTHONPATH}"
exec python3 -m arkmanager "$@"
LAUNCHER
chmod +x "${APP_DIR}/usr/bin/arkmanager"

# AppRun
cat > "${APP_DIR}/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/dist-packages:${PYTHONPATH}"
exec python3 -m arkmanager "$@"
APPRUN
chmod +x "${APP_DIR}/AppRun"

# Desktop file
cp resources/arkmanager.desktop "${APP_DIR}/"
cp resources/arkmanager.desktop "${APP_DIR}/usr/share/applications/"

# Icon
cp resources/arkmanager.svg "${APP_DIR}/arkmanager.svg"
cp resources/arkmanager.svg "${APP_DIR}/usr/share/icons/hicolor/scalable/apps/"

# 下载并解压 appimagetool | Download and extract appimagetool
# 必须解压后运行，否则自带的 mksquashfs 只支持 zstd 压缩
# Must extract before running, otherwise bundled mksquashfs only supports zstd
if [ ! -f appimagetool ]; then
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool
    chmod +x appimagetool
fi
./appimagetool --appimage-extract > /dev/null 2>&1

# 使用系统 mksquashfs（支持 gzip/xz/zstd）+ gzip 压缩以保证最大兼容性
# Use system mksquashfs (supports gzip/xz/zstd) + gzip for max compatibility
export MKSQUASHFS=/usr/bin/mksquashfs
ARCH=x86_64 ./squashfs-root/AppRun --comp gzip "${APP_DIR}" "${PACKAGE_NAME}-${VERSION}-x86_64.AppImage"
rm -rf squashfs-root

echo "AppImage built: ${PACKAGE_NAME}-${VERSION}-x86_64.AppImage"
rm -rf "${APP_DIR}"
