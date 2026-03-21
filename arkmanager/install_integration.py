#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面文件管理器集成安装器 | Desktop file manager integration installer

为 Linux 文件管理器（Nautilus、Nemo、Dolphin）安装右键菜单集成
Installs right-click context menu entries for Linux file managers (Nautilus, Nemo, Dolphin)
"""

import shutil
from pathlib import Path
from typing import Dict, List


def detect_file_managers() -> List[str]:
    """
    检测已安装的文件管理器 | Detect installed file managers.

    Returns:
        检测到的文件管理器列表 | List of detected file managers
    """
    # 支持的文件管理器列表 | List of supported file managers
    managers = ['nautilus', 'nemo', 'dolphin', 'thunar']
    detected = []

    for manager in managers:
        # 使用 which 检测是否安装 | Use which to detect if installed
        if shutil.which(manager):
            detected.append(manager)

    return detected


def install_nautilus() -> bool:
    """
    安装 Nautilus (GNOME) 脚本集成 | Install Nautilus scripts.

    在 ~/.local/share/nautilus/scripts/ 创建脚本文件
    Creates script files in ~/.local/share/nautilus/scripts/

    Returns:
        安装成功返回 True | True if installation succeeds
    """
    try:
        # 获取脚本目录路径 | Get scripts directory path
        scripts_dir = Path.home() / '.local' / 'share' / 'nautilus' / 'scripts'
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # 定义要创建的脚本 | Define scripts to create
        scripts = {
            'ArkManager - Open': '''#!/bin/bash
# 用 ArkManager 打开归档 | Open archives with ArkManager
IFS=$'\\n'
for file in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    arkmanager "$file" &
done
''',
            'ArkManager - Extract Here': '''#!/bin/bash
# 解压到当前目录 | Extract to current directory
IFS=$'\\n'
for file in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    arkmanager --extract-here "$file" &
done
''',
            'ArkManager - Extract to Folder': '''#!/bin/bash
# 解压到新文件夹 | Extract to new folder
IFS=$'\\n'
for file in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    arkmanager --extract "$file" &
done
''',
            'ArkManager - Compress': '''#!/bin/bash
# 压缩选中的文件 | Compress selected files
arkmanager --compress "$@" &
''',
            'ArkManager - Checksum': '''#!/bin/bash
# 计算文件哈希值 | Calculate file hash
arkmanager --checksum "$@" &
'''
        }

        # 创建并设置脚本 | Create and set up scripts
        for name, content in scripts.items():
            script_path = scripts_dir / name
            script_path.write_text(content)
            # 设置可执行权限 | Set executable permission
            script_path.chmod(0o755)

        return True

    except OSError as e:
        print(f"安装 Nautilus 集成失败 | Failed to install Nautilus integration: {e}")
        return False


def install_nemo() -> bool:
    """
    安装 Nemo (Cinnamon) 动作集成 | Install Nemo actions.

    在 ~/.local/share/nemo/actions/ 创建 .nemo_action 文件
    Creates .nemo_action files in ~/.local/share/nemo/actions/

    Returns:
        安装成功返回 True | True if installation succeeds
    """
    try:
        # 获取动作目录路径 | Get actions directory path
        actions_dir = Path.home() / '.local' / 'share' / 'nemo' / 'actions'
        actions_dir.mkdir(parents=True, exist_ok=True)

        # 定义要创建的动作文件 | Define action files to create
        actions = {
            'arkmanager-open.nemo_action': '''[Nemo Action]
Name=Open with ArkManager
Name[zh_CN]=用 ArkManager 打开
Comment=Open archive files with ArkManager
Comment[zh_CN]=用 ArkManager 打开归档文件
Exec=arkmanager %F
Icon-Name=package-x-generic
Selection=any
Extensions=zip;7z;rar;tar;gz;bz2;xz;tar.gz;tar.bz2;tar.xz;zst;tar.zst;lzh;cab;iso;rpm;deb;wim;
Terminal=false
Quote=double
''',
            'arkmanager-extract-here.nemo_action': '''[Nemo Action]
Name=ArkManager: Extract Here
Name[zh_CN]=ArkManager: 解压到此处
Comment=Extract archives to current directory
Comment[zh_CN]=将归档解压到当前目录
Exec=arkmanager --extract-here %F
Icon-Name=archive-extract
Selection=any
Extensions=zip;7z;rar;tar;gz;bz2;xz;tar.gz;tar.bz2;tar.xz;zst;tar.zst;lzh;cab;iso;rpm;deb;wim;
Terminal=false
Quote=double
''',
            'arkmanager-extract.nemo_action': '''[Nemo Action]
Name=ArkManager: Extract to Folder
Name[zh_CN]=ArkManager: 解压到文件夹
Comment=Extract archives to a new folder
Comment[zh_CN]=将归档解压到新文件夹
Exec=arkmanager --extract %F
Icon-Name=archive-extract
Selection=any
Extensions=zip;7z;rar;tar;gz;bz2;xz;tar.gz;tar.bz2;tar.xz;zst;tar.zst;lzh;cab;iso;rpm;deb;wim;
Terminal=false
Quote=double
''',
            'arkmanager-compress.nemo_action': '''[Nemo Action]
Name=ArkManager: Compress...
Name[zh_CN]=ArkManager: 压缩...
Comment=Compress selected files
Comment[zh_CN]=压缩选中的文件
Exec=arkmanager --compress %F
Icon-Name=archive-insert
Selection=any
Extensions=any;
Terminal=false
Quote=double
''',
            'arkmanager-checksum.nemo_action': '''[Nemo Action]
Name=ArkManager: Calculate Hash
Name[zh_CN]=ArkManager: 计算哈希
Comment=Calculate file hash checksums
Comment[zh_CN]=计算文件哈希校验值
Exec=arkmanager --checksum %F
Icon-Name=dialog-password
Selection=any
Extensions=any;
Terminal=false
Quote=double
'''
        }

        # 创建动作文件 | Create action files
        for name, content in actions.items():
            action_path = actions_dir / name
            action_path.write_text(content)

        return True

    except OSError as e:
        print(f"安装 Nemo 集成失败 | Failed to install Nemo integration: {e}")
        return False


def install_dolphin() -> bool:
    """
    安装 Dolphin (KDE) 服务菜单集成 | Install Dolphin service menu.

    在 ~/.local/share/kio/servicemenus/ 创建 .desktop 文件
    Creates .desktop file in ~/.local/share/kio/servicemenus/

    Returns:
        安装成功返回 True | True if installation succeeds
    """
    try:
        # 获取服务菜单目录路径 | Get service menus directory path
        servicemenus_dir = Path.home() / '.local' / 'share' / 'kio' / 'servicemenus'
        servicemenus_dir.mkdir(parents=True, exist_ok=True)

        # 定义服务菜单内容 | Define service menu content
        service_menu = '''[Desktop Entry]
Type=Service
MimeType=application/zip;application/x-7z-compressed;application/x-rar;application/x-tar;application/gzip;application/x-bzip2;application/x-xz;application/x-zstd;application/x-lzh;application/vnd.ms-cab-compressed;application/x-iso9660-image;application/x-rpm;application/x-deb;application/x-ms-wim;
X-KDE-Submenu=ArkManager
X-KDE-Submenu[zh_CN]=ArkManager 归档管理器
Icon=package-x-generic
Actions=open;extractHere;extract;compress;checksum;

[Desktop Action open]
Name=Open with ArkManager
Name[zh_CN]=用 ArkManager 打开
Icon=package-x-generic
Exec=arkmanager %U

[Desktop Action extractHere]
Name=Extract Here
Name[zh_CN]=解压到此处
Icon=archive-extract
Exec=arkmanager --extract-here %U

[Desktop Action extract]
Name=Extract to Folder
Name[zh_CN]=解压到文件夹
Icon=archive-extract
Exec=arkmanager --extract %U

[Desktop Action compress]
Name=Compress...
Name[zh_CN]=压缩...
Icon=archive-insert
Exec=arkmanager --compress %U

[Desktop Action checksum]
Name=Calculate Hash
Name[zh_CN]=计算哈希
Icon=dialog-password
Exec=arkmanager --checksum %U
'''

        # 创建服务菜单文件 | Create service menu file
        menu_path = servicemenus_dir / 'arkmanager.desktop'
        menu_path.write_text(service_menu)

        return True

    except OSError as e:
        print(f"安装 Dolphin 集成失败 | Failed to install Dolphin integration: {e}")
        return False


def remove_nautilus() -> bool:
    """
    移除 Nautilus 集成 | Remove Nautilus integration.

    Returns:
        移除成功返回 True | True if removal succeeds
    """
    try:
        # 获取脚本目录路径 | Get scripts directory path
        scripts_dir = Path.home() / '.local' / 'share' / 'nautilus' / 'scripts'

        # 脚本名称列表 | List of script names
        script_names = [
            'ArkManager - Open',
            'ArkManager - Extract Here',
            'ArkManager - Extract to Folder',
            'ArkManager - Compress',
            'ArkManager - Checksum'
        ]

        # 删除脚本文件 | Delete script files
        for name in script_names:
            script_path = scripts_dir / name
            if script_path.exists():
                script_path.unlink()

        return True

    except OSError as e:
        print(f"移除 Nautilus 集成失败 | Failed to remove Nautilus integration: {e}")
        return False


def remove_nemo() -> bool:
    """
    移除 Nemo 集成 | Remove Nemo integration.

    Returns:
        移除成功返回 True | True if removal succeeds
    """
    try:
        # 获取动作目录路径 | Get actions directory path
        actions_dir = Path.home() / '.local' / 'share' / 'nemo' / 'actions'

        # 动作文件名称列表 | List of action file names
        action_files = [
            'arkmanager-open.nemo_action',
            'arkmanager-extract-here.nemo_action',
            'arkmanager-extract.nemo_action',
            'arkmanager-compress.nemo_action',
            'arkmanager-checksum.nemo_action'
        ]

        # 删除动作文件 | Delete action files
        for name in action_files:
            action_path = actions_dir / name
            if action_path.exists():
                action_path.unlink()

        return True

    except OSError as e:
        print(f"移除 Nemo 集成失败 | Failed to remove Nemo integration: {e}")
        return False


def remove_dolphin() -> bool:
    """
    移除 Dolphin 集成 | Remove Dolphin integration.

    Returns:
        移除成功返回 True | True if removal succeeds
    """
    try:
        # 获取服务菜单文件路径 | Get service menu file path
        menu_path = Path.home() / '.local' / 'share' / 'kio' / 'servicemenus' / 'arkmanager.desktop'

        # 删除服务菜单文件 | Delete service menu file
        if menu_path.exists():
            menu_path.unlink()

        return True

    except OSError as e:
        print(f"移除 Dolphin 集成失败 | Failed to remove Dolphin integration: {e}")
        return False


def install_all() -> Dict[str, bool]:
    """
    安装所有检测到的文件管理器集成 | Install integration for all detected file managers.

    自动检测已安装的文件管理器并为其安装右键菜单集成
    Automatically detects installed file managers and installs context menu integration

    Returns:
        字典，键为文件管理器名称，值为安装是否成功
        Dictionary with file manager names as keys and installation success as values
    """
    results = {}

    # 检测已安装的文件管理器 | Detect installed file managers
    detected = detect_file_managers()

    # 安装函数映射 | Installation function mapping
    install_funcs = {
        'nautilus': install_nautilus,
        'nemo': install_nemo,
        'dolphin': install_dolphin,
    }

    # 为每个检测到的文件管理器安装集成 | Install integration for each detected file manager
    for manager in detected:
        if manager in install_funcs:
            print(f"正在安装 {manager} 集成... | Installing {manager} integration...")
            results[manager] = install_funcs[manager]()
            if results[manager]:
                print(f"✓ {manager} 集成安装成功 | {manager} integration installed successfully")
            else:
                print(f"✗ {manager} 集成安装失败 | {manager} integration installation failed")

    if not results:
        print("未检测到支持的文件管理器 | No supported file managers detected")

    return results


def remove_all() -> Dict[str, bool]:
    """
    移除所有已安装的集成 | Remove all installed integrations.

    移除所有支持的文件管理器的右键菜单集成
    Removes context menu integration for all supported file managers

    Returns:
        字典，键为文件管理器名称，值为移除是否成功
        Dictionary with file manager names as keys and removal success as values
    """
    results = {}

    # 移除函数映射 | Removal function mapping
    remove_funcs = {
        'nautilus': remove_nautilus,
        'nemo': remove_nemo,
        'dolphin': remove_dolphin,
    }

    # 移除所有集成 | Remove all integrations
    for manager, remove_func in remove_funcs.items():
        print(f"正在移除 {manager} 集成... | Removing {manager} integration...")
        results[manager] = remove_func()
        if results[manager]:
            print(f"✓ {manager} 集成移除成功 | {manager} integration removed successfully")
        else:
            print(f"✗ {manager} 集成移除失败 | {manager} integration removal failed")

    return results


def main():
    """
    主函数，提供命令行界面 | Main function providing command-line interface.
    """
    import sys

    if len(sys.argv) < 2:
        print("用法 | Usage: python install_integration.py [install|remove|detect]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'install':
        print("开始安装文件管理器集成... | Starting file manager integration installation...")
        results = install_all()
        success_count = sum(results.values())
        print(f"\n安装完成: {success_count}/{len(results)} 成功")
        print(f"Installation complete: {success_count}/{len(results)} succeeded")

    elif command == 'remove':
        print("开始移除文件管理器集成... | Starting file manager integration removal...")
        results = remove_all()
        success_count = sum(results.values())
        print(f"\n移除完成: {success_count}/{len(results)} 成功")
        print(f"Removal complete: {success_count}/{len(results)} succeeded")

    elif command == 'detect':
        print("检测已安装的文件管理器... | Detecting installed file managers...")
        detected = detect_file_managers()
        if detected:
            print(f"检测到: {', '.join(detected)} | Detected: {', '.join(detected)}")
        else:
            print("未检测到支持的文件管理器 | No supported file managers detected")

    else:
        print(f"未知命令: {command} | Unknown command: {command}")
        print("用法 | Usage: python install_integration.py [install|remove|detect]")
        sys.exit(1)


if __name__ == '__main__':
    main()
