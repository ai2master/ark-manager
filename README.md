# ArkManager

A 7-Zip based GUI archive manager for Linux with Chinese encoding support, fake encryption detection, and John the Ripper integration.

![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Qt](https://img.shields.io/badge/GUI-PyQt6-green)

## Features

- **7z CLI Backend** - Uses the native `7z` command for all archive operations. Supports 7z, ZIP, RAR, TAR, GZ, BZ2, XZ, ZST, CAB, ISO, WIM, and more.
- **Chinese Filename Encoding** - Auto-detect or force GBK/GB18030/Big5/Shift-JIS encoding for archive filenames. Fixes garbled Chinese filenames in ZIP files created on Windows.
- **Archive Comment Display** - Shows archive comments prominently in the right panel of the preview interface.
- **Fake Encryption Detection** - Detects ZIP pseudo-encryption by analyzing Local File Header and Central Directory Header flags. Can remove fake encryption.
- **Chinese Password Support** - Full support for Chinese characters in passwords for both encryption and decryption.
- **John the Ripper Integration** - Built-in GUI for password recovery using John the Ripper. Supports hash extraction (zip2john, rar2john, etc.), wordlist attacks, incremental brute-force, mask attacks, and more.
- **Auto-Create Parent Folder** - Option to automatically create a parent directory when extracting archives.
- **Drag & Drop** - Drop archive files directly onto the window to open them.

## Screenshots

The interface is inspired by 7-Zip for Windows and PeaZip for Linux, with a tree view for archive contents and a side panel for archive comments and metadata.

## Installation

### Requirements

- Python 3.9+
- PyQt6
- p7zip-full (`7z` command)
- chardet (Python package)
- john (optional, for password recovery)

### From Source

```bash
git clone https://github.com/aidev666888/ark-manager.git
cd ark-manager
pip install -e .
arkmanager
```

### Debian/Ubuntu (.deb)

```bash
sudo dpkg -i arkmanager_1.0.0_amd64.deb
sudo apt-get install -f  # Install dependencies
```

### Fedora/RHEL (.rpm)

```bash
sudo dnf install arkmanager-1.0.0-1.noarch.rpm
```

### AppImage (Portable)

```bash
chmod +x ArkManager-1.0.0-x86_64.AppImage
./ArkManager-1.0.0-x86_64.AppImage
```

### Flatpak

```bash
flatpak install ArkManager-1.0.0.flatpak
flatpak run io.github.arkmanager.ArkManager
```

## Usage

### Open an Archive

```bash
arkmanager                  # Launch GUI
arkmanager /path/to/file.zip  # Open specific archive
```

### Encoding Options

In the main toolbar, select the encoding mode:
- **Auto Detect** - Automatically detect and fix garbled Chinese filenames
- **Force GBK** - Force GBK encoding (for archives created on Chinese Windows)
- **Force GB18030** - Chinese universal encoding
- **Force Big5** - Traditional Chinese
- **Force Shift-JIS** - Japanese
- **No Conversion** - Show raw filenames

The same encoding options are available in the Extract and Compress dialogs.

### Password Recovery

1. Open an encrypted archive
2. Go to **Tools > Password Recovery (John the Ripper)**
3. Click **Extract Hash** to generate a hash file
4. Choose attack mode (Wordlist, Incremental, Single, Mask)
5. Click **Start Cracking**

### Fake Encryption Detection

1. Open a ZIP archive
2. Go to **Actions > Detect Fake Encryption**
3. If pseudo-encryption is detected, click **Remove Fake Encryption** to create a patched copy

## Building Packages

All packages are built via GitHub Actions on tag push:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers the build workflow which produces `.deb`, `.rpm`, `.AppImage`, and `.flatpak` packages.

### Manual Build

```bash
# DEB
bash packaging/deb/build-deb.sh 1.0.0

# RPM (on Fedora)
bash packaging/rpm/build-rpm.sh 1.0.0

# AppImage
bash packaging/appimage/build-appimage.sh 1.0.0
```

## Architecture

```
arkmanager/
├── __init__.py          # Version info
├── __main__.py          # Entry point, Qt app setup, styling
├── main_window.py       # Main GUI window, dialogs
├── archive_backend.py   # 7z CLI wrapper for archive operations
├── john_backend.py      # John the Ripper CLI wrapper
└── encoding_utils.py    # Encoding detection, pseudo-encryption tools
```

## Acknowledgments

- [7-Zip](https://www.7-zip.org/) by Igor Pavlov
- [PeaZip](https://peazip.github.io/) for UI inspiration
- [John the Ripper](https://www.openwall.com/john/) by Openwall
- [chardet](https://github.com/chardet/chardet) for encoding detection

## License

GPL-3.0-or-later
