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

# 手动构建 AppImage：绕过 appimagetool 自带的只支持 zstd 的 mksquashfs
# AppImage = type2-runtime + gzip-compressed squashfs
# Manual AppImage build: bypass appimagetool's bundled zstd-only mksquashfs
APPIMAGE_FILE="${PACKAGE_NAME}-${VERSION}-x86_64.AppImage"
RUNTIME_URL="https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64"

# 下载 type2 runtime | Download type2 runtime
echo "Downloading AppImage runtime..."
wget -q "${RUNTIME_URL}" -O runtime-x86_64
chmod +x runtime-x86_64

# 使用系统 mksquashfs 创建 gzip 压缩的 squashfs 镜像
# Use system mksquashfs to create gzip-compressed squashfs image
echo "Creating squashfs with gzip compression..."
mksquashfs "${APP_DIR}" squashfs.img \
    -root-owned -noappend \
    -comp gzip \
    -b 131072 \
    -no-xattrs

# 拼接 runtime + squashfs = AppImage | Concatenate runtime + squashfs = AppImage
echo "Assembling AppImage..."
cat runtime-x86_64 squashfs.img > "${APPIMAGE_FILE}"
chmod +x "${APPIMAGE_FILE}"

# 清理临时文件 | Clean up temp files
rm -f runtime-x86_64 squashfs.img

echo "AppImage built: ${APPIMAGE_FILE}"
rm -rf "${APP_DIR}"
