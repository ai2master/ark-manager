"""ArkManager 程序入口点 | Entry point for ArkManager application.

该模块负责初始化PyQt6应用程序、设置全局样式、配置编码环境，
并创建主窗口。支持通过命令行参数传入压缩包文件路径来直接打开，
以及通过CLI进行快速操作（解压、压缩、校验等）。

This module initializes the PyQt6 application, sets up global styles,
configures encoding environment, and creates the main window. Supports
opening archive files via command-line arguments and quick operations
via CLI (extract, compress, checksum, etc.).
"""

import argparse
import os
import sys

from . import __version__

# ==================== 命令行参数解析 | Command-line Argument Parsing ====================

def parse_args():
    """解析命令行参数 | Parse command-line arguments.

    Returns:
        argparse.Namespace: 解析后的参数对象 | Parsed arguments object
    """
    parser = argparse.ArgumentParser(
        prog='arkmanager',
        description='ArkManager - 基于7z的压缩包管理器 | 7z-based archive manager'
    )

    # 位置参数：压缩包文件路径 | Positional arguments: archive file paths
    parser.add_argument(
        'files',
        nargs='*',
        help='压缩包文件路径 | Archive file paths'
    )

    # 快速操作参数 | Quick operation arguments
    parser.add_argument(
        '--extract-here',
        nargs='+',
        metavar='FILE',
        help='解压到当前目录 | Extract to current directory'
    )
    parser.add_argument(
        '--extract',
        nargs='+',
        metavar='FILE',
        help='解压（弹出选项对话框） | Extract (show options dialog)'
    )
    parser.add_argument(
        '--compress',
        nargs='+',
        metavar='FILE',
        help='压缩（弹出选项对话框） | Compress (show options dialog)'
    )
    parser.add_argument(
        '--checksum',
        nargs='+',
        metavar='FILE',
        help='计算哈希 | Calculate hash'
    )

    # 系统集成参数 | System integration arguments
    parser.add_argument(
        '--install-integration',
        action='store_true',
        help='安装文件管理器右键菜单 | Install file manager integration'
    )
    parser.add_argument(
        '--remove-integration',
        action='store_true',
        help='移除文件管理器右键菜单 | Remove file manager integration'
    )

    # 语言设置 | Language setting
    parser.add_argument(
        '--language',
        choices=['en_US', 'zh_CN'],
        help='设置界面语言 | Set UI language'
    )

    return parser.parse_args()


# ==================== 应用程序入口函数 | Application Entry Point ====================

def main():
    """应用程序主入口函数 | Main application entry point.

    功能 | Functionality:
    1. 解析命令行参数
    2. 处理非 GUI 操作（install/remove integration）
    3. 配置编码环境
    4. 创建Qt应用程序实例
    5. 初始化多语言支持
    6. 加载并应用主题
    7. 启用高DPI支持
    8. 创建并显示主窗口
    9. 处理 CLI 文件参数
    10. 启动事件循环
    """
    # ==================== 1. 解析命令行参数 | Parse Command-line Arguments ====================
    args = parse_args()

    # ==================== 2. 处理非 GUI 操作 | Handle Non-GUI Operations ====================
    # 安装文件管理器右键菜单集成 | Install file manager context menu integration
    if args.install_integration:
        from .install_integration import install_all
        print("Installing desktop integration...")
        print("正在安装桌面集成...")
        results = install_all()
        for fm, success in results.items():
            status = "✓ OK" if success else "⊗ SKIP"
            print(f"  {fm}: {status}")
        return

    # 移除文件管理器右键菜单集成 | Remove file manager context menu integration
    if args.remove_integration:
        from .install_integration import remove_all
        print("Removing desktop integration...")
        print("正在移除桌面集成...")
        results = remove_all()
        for fm, success in results.items():
            status = "✓ OK" if success else "⊗ SKIP"
            print(f"  {fm}: {status}")
        return

    # ==================== 3. 配置环境 | Configure Environment ====================
    # 确保中文字符正确编码 | Ensure proper encoding for Chinese characters
    # Linux系统需要明确设置UTF-8区域，避免文件名和输出乱码
    # Linux systems need explicit UTF-8 locale to avoid garbled filenames and output
    if sys.platform == "linux":
        os.environ.setdefault("LANG", "en_US.UTF-8")
        os.environ.setdefault("LC_ALL", "en_US.UTF-8")

    # ============ 4. 创建Qt应用程序实例 | Create Qt Application Instance ============
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 设置应用程序元数据，用于配置文件存储等功能
    # Set application metadata for settings storage etc.
    app.setApplicationName("ArkManager")
    app.setOrganizationName("ArkManager")
    app.setApplicationVersion(__version__)

    # ==================== 5. 初始化多语言支持 | Initialize i18n ====================
    from .i18n import init_language, set_language

    # 如果命令行指定了语言，使用命令行参数；否则从配置加载或自动检测
    # If language specified via CLI, use it; otherwise load from settings or auto-detect
    if args.language:
        set_language(args.language)
    else:
        init_language()

    # ==================== 6. 加载并应用主题 | Load and Apply Theme ====================
    from .themes import get_saved_theme, get_theme

    # 从配置文件读取用户保存的主题偏好 | Load user's saved theme preference
    theme_name = get_saved_theme()
    app.setStyleSheet(get_theme(theme_name))

    # ==================== 7. 启用高DPI支持 | Enable High-DPI Support ====================
    from PyQt6.QtCore import Qt

    # 启用高DPI图像支持（Qt6.5+已默认启用，仅旧版本需要）
    # Enable high DPI pixmap support (default in Qt6.5+, only needed for older)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # ==================== 8. 创建并显示主窗口 | Create and Show Main Window ====================
    from .main_window import MainWindow

    # 创建主窗口实例 | Create main window instance
    window = MainWindow()
    window.show()

    # ==================== 9. 处理 CLI 文件参数 | Handle CLI File Parameters ====================
    # 根据不同的命令行参数执行相应操作
    # Execute corresponding operations based on different CLI arguments

    files_to_open = args.files or []

    if args.extract_here:
        # 直接解压到当前目录（无需弹出对话框）
        # Extract directly to current directory (no dialog)
        for f in args.extract_here:
            if os.path.isfile(f):
                window._quick_extract_here(f)

    elif args.extract:
        # 打开解压对话框（用户可配置选项）
        # Open extract dialog (user can configure options)
        for f in args.extract:
            if os.path.isfile(f):
                window._load_archive(f)
                window._extract_archive()

    elif args.compress:
        # 打开压缩对话框（用户可配置选项）
        # Open compress dialog (user can configure options)
        window._quick_compress(args.compress)

    elif args.checksum:
        # 打开校验和对话框
        # Open checksum dialog
        window._quick_checksum(args.checksum)

    elif files_to_open:
        # 打开第一个文件到主窗口
        # Open first file in main window
        filepath = files_to_open[0]
        if os.path.isfile(filepath):
            window._load_archive(filepath)

    # ==================== 10. 启动事件循环 | Start Event Loop ====================
    # 启动Qt事件循环，进入主程序 | Start Qt event loop and enter main program
    sys.exit(app.exec())


# ==================== 直接执行入口 | Direct Execution Entry ====================

if __name__ == "__main__":
    main()
