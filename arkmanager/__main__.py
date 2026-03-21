"""ArkManager 程序入口点 | Entry point for ArkManager application.

该模块负责初始化PyQt6应用程序、设置全局样式、配置编码环境，
并创建主窗口。支持通过命令行参数传入压缩包文件路径来直接打开。

This module initializes the PyQt6 application, sets up global styles,
configures encoding environment, and creates the main window. Supports
opening archive files via command-line arguments.
"""

import os
import sys

# ==================== 应用程序入口函数 | Application Entry Point ====================

def main():
    """应用程序主入口函数 | Main application entry point.

    功能 | Functionality:
    1. 配置Linux系统的UTF-8区域设置
    2. 创建Qt应用程序实例
    3. 设置应用元数据
    4. 启用高DPI支持
    5. 应用全局UI样式表
    6. 创建并显示主窗口
    7. 处理命令行文件参数
    8. 启动事件循环
    """
    # 确保中文字符正确编码 | Ensure proper encoding for Chinese characters
    # Linux系统需要明确设置UTF-8区域，避免文件名和输出乱码
    # Linux systems need explicit UTF-8 locale to avoid garbled filenames and output
    if sys.platform == "linux":
        os.environ.setdefault("LANG", "en_US.UTF-8")
        os.environ.setdefault("LC_ALL", "en_US.UTF-8")

    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    # 创建Qt应用程序实例 | Create Qt application instance
    app = QApplication(sys.argv)

    # 设置应用程序元数据，用于配置文件存储等功能
    # Set application metadata for settings storage etc.
    app.setApplicationName("ArkManager")
    app.setOrganizationName("ArkManager")
    app.setApplicationVersion("1.0.0")

    # 启用高DPI图像支持，改善高分辨率显示器上的显示效果
    # Enable high DPI pixmap support for better rendering on high-resolution displays
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # ==================== 应用全局样式表 | Apply Global Stylesheet ====================
    # 使用Material Design风格的配色方案，提供现代化的用户界面
    # Uses Material Design color scheme for a modern user interface
    app.setStyleSheet("""
        /* 主窗口背景 | Main window background */
        QMainWindow {
            background: #fafafa;
        }
        /* 工具栏样式 | Toolbar styles */
        QToolBar {
            spacing: 4px;
            padding: 2px;
        }
        /* 工具栏按钮样式 | Toolbar button styles */
        QToolBar QPushButton {
            padding: 6px 14px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fff;
            font-size: 13px;
        }
        /* 工具栏按钮悬停效果 | Toolbar button hover effect */
        QToolBar QPushButton:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        /* 工具栏按钮按下效果 | Toolbar button pressed effect */
        QToolBar QPushButton:pressed {
            background: #bbdefb;
        }
        /* 树形控件样式（文件列表） | Tree widget styles (file list) */
        QTreeWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
        }
        /* 树形控件项目样式 | Tree widget item styles */
        QTreeWidget::item {
            padding: 2px 0;
        }
        /* 树形控件选中项样式 | Tree widget selected item styles */
        QTreeWidget::item:selected {
            background: #e3f2fd;
            color: #000;
        }
        /* 分组框样式 | Group box styles */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 16px;
        }
        /* 分组框标题样式 | Group box title styles */
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }
        /* 输入控件统一样式 | Uniform input control styles */
        QComboBox, QLineEdit, QSpinBox {
            padding: 4px 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        /* 通用按钮样式 | General button styles */
        QPushButton {
            padding: 6px 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fff;
        }
        /* 通用按钮悬停效果 | General button hover effect */
        QPushButton:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        /* 进度条样式 | Progress bar styles */
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 4px;
            text-align: center;
        }
        /* 进度条填充部分 | Progress bar filled chunk */
        QProgressBar::chunk {
            background: #2196f3;
            border-radius: 3px;
        }
    """)

    # ==================== 创建并显示主窗口 | Create and Show Main Window ====================

    from .main_window import MainWindow

    # 创建主窗口实例 | Create main window instance
    window = MainWindow()
    window.show()

    # 处理命令行文件参数 | Handle command-line file argument
    # 如果用户通过命令行传入文件路径，自动打开该压缩包
    # If user provides file path via command line, automatically open that archive
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.isfile(filepath):
            window._load_archive(filepath)

    # 启动Qt事件循环，进入主程序 | Start Qt event loop and enter main program
    sys.exit(app.exec())


# ==================== 直接执行入口 | Direct Execution Entry ====================

if __name__ == "__main__":
    main()
