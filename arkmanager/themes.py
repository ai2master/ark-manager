"""
主题/样式表模块 | Theme/Stylesheet Module
为 ArkManager 提供 Material Design 风格的浅色和暗色主题
Provides Material Design light and dark themes for ArkManager
"""

from PyQt6.QtCore import QSettings

# 主题字典 | Theme dictionary
_THEMES = {
    'light': """
        /* Material Design 浅色主题 | Material Design Light Theme */
        QMainWindow {
            background: #fafafa;
        }

        QToolBar {
            spacing: 4px;
            padding: 2px;
            background: #fafafa;
            border: none;
        }

        QToolBar QPushButton {
            padding: 6px 14px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fff;
            font-size: 13px;
            color: #212121;
        }

        QToolBar QPushButton:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }

        QToolBar QPushButton:pressed {
            background: #bbdefb;
        }

        QTreeWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
            background: #fff;
            color: #212121;
            alternate-background-color: #f5f5f5;
        }

        QTreeWidget::item {
            padding: 2px 0;
        }

        QTreeWidget::item:selected {
            background: #e3f2fd;
            color: #000;
        }

        QTreeWidget::item:hover {
            background: #f5f5f5;
        }

        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 16px;
            background: #fff;
            color: #212121;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }

        QComboBox, QLineEdit, QSpinBox {
            padding: 4px 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fff;
            color: #212121;
        }

        QComboBox:hover, QLineEdit:hover, QSpinBox:hover {
            border-color: #2196f3;
        }

        QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
            border-color: #2196f3;
            border-width: 2px;
        }

        QPushButton {
            padding: 6px 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fff;
            color: #212121;
        }

        QPushButton:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }

        QPushButton:pressed {
            background: #bbdefb;
        }

        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 4px;
            text-align: center;
            background: #fff;
            color: #212121;
        }

        QProgressBar::chunk {
            background: #2196f3;
            border-radius: 3px;
        }

        QPlainTextEdit, QTextEdit {
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #fff;
            color: #212121;
            font-size: 13px;
        }

        QMenuBar {
            background: #fafafa;
            color: #212121;
            border-bottom: 1px solid #ddd;
        }

        QMenuBar::item {
            padding: 4px 12px;
            background: transparent;
        }

        QMenuBar::item:selected {
            background: #e3f2fd;
        }

        QMenuBar::item:pressed {
            background: #bbdefb;
        }

        QMenu {
            background: #fff;
            color: #212121;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        QMenu::item {
            padding: 6px 24px 6px 12px;
        }

        QMenu::item:selected {
            background: #e3f2fd;
        }

        QMenu::separator {
            height: 1px;
            background: #ddd;
            margin: 4px 0;
        }

        QStatusBar {
            background: #fafafa;
            color: #212121;
            border-top: 1px solid #ddd;
        }

        QScrollBar:vertical {
            border: none;
            background: #f5f5f5;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background: #ccc;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #aaa;
        }

        QScrollBar:horizontal {
            border: none;
            background: #f5f5f5;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background: #ccc;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #aaa;
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }

        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #fff;
        }

        QTabBar::tab {
            padding: 6px 16px;
            border: 1px solid #ddd;
            border-bottom: none;
            background: #f5f5f5;
            color: #212121;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected {
            background: #fff;
            border-bottom: 2px solid #2196f3;
        }

        QTabBar::tab:hover {
            background: #e3f2fd;
        }

        QSplitter::handle {
            background: #ddd;
        }

        QSplitter::handle:horizontal {
            width: 2px;
        }

        QSplitter::handle:vertical {
            height: 2px;
        }

        QHeaderView::section {
            background: #f5f5f5;
            color: #212121;
            padding: 4px 8px;
            border: none;
            border-right: 1px solid #ddd;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }

        QHeaderView::section:hover {
            background: #e3f2fd;
        }
    """,

    'dark': """
        /* Material Design 暗色主题 | Material Design Dark Theme */
        QMainWindow {
            background: #1e1e1e;
        }

        QToolBar {
            spacing: 4px;
            padding: 2px;
            background: #1e1e1e;
            border: none;
        }

        QToolBar QPushButton {
            padding: 6px 14px;
            border: 1px solid #555555;
            border-radius: 4px;
            background: #2d2d2d;
            font-size: 13px;
            color: #e0e0e0;
        }

        QToolBar QPushButton:hover {
            background: #3d3d3d;
            border-color: #64b5f6;
        }

        QToolBar QPushButton:pressed {
            background: #4d4d4d;
        }

        QTreeWidget {
            border: 1px solid #555555;
            border-radius: 4px;
            font-size: 13px;
            background: #2d2d2d;
            color: #e0e0e0;
            alternate-background-color: #353535;
        }

        QTreeWidget::item {
            padding: 2px 0;
        }

        QTreeWidget::item:selected {
            background: #1565c0;
            color: #ffffff;
        }

        QTreeWidget::item:hover {
            background: #383838;
        }

        QGroupBox {
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 16px;
            background: #2d2d2d;
            color: #e0e0e0;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }

        QComboBox, QLineEdit, QSpinBox {
            padding: 4px 8px;
            border: 1px solid #555555;
            border-radius: 4px;
            background: #383838;
            color: #e0e0e0;
        }

        QComboBox:hover, QLineEdit:hover, QSpinBox:hover {
            border-color: #64b5f6;
        }

        QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
            border-color: #64b5f6;
            border-width: 2px;
        }

        QComboBox::drop-down {
            border: none;
            background: #383838;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #e0e0e0;
        }

        QComboBox QAbstractItemView {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #555555;
            selection-background-color: #1565c0;
            selection-color: #ffffff;
        }

        QSpinBox::up-button, QSpinBox::down-button {
            background: #383838;
            border: none;
        }

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #4d4d4d;
        }

        QPushButton {
            padding: 6px 16px;
            border: 1px solid #555555;
            border-radius: 4px;
            background: #2d2d2d;
            color: #e0e0e0;
        }

        QPushButton:hover {
            background: #3d3d3d;
            border-color: #64b5f6;
        }

        QPushButton:pressed {
            background: #4d4d4d;
        }

        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background: #2d2d2d;
            color: #e0e0e0;
        }

        QProgressBar::chunk {
            background: #64b5f6;
            border-radius: 3px;
        }

        QPlainTextEdit, QTextEdit {
            border: 1px solid #555555;
            border-radius: 4px;
            background: #2d2d2d;
            color: #e0e0e0;
            font-size: 13px;
        }

        QMenuBar {
            background: #1e1e1e;
            color: #e0e0e0;
            border-bottom: 1px solid #555555;
        }

        QMenuBar::item {
            padding: 4px 12px;
            background: transparent;
        }

        QMenuBar::item:selected {
            background: #3d3d3d;
        }

        QMenuBar::item:pressed {
            background: #4d4d4d;
        }

        QMenu {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #555555;
            border-radius: 4px;
        }

        QMenu::item {
            padding: 6px 24px 6px 12px;
        }

        QMenu::item:selected {
            background: #1565c0;
            color: #ffffff;
        }

        QMenu::separator {
            height: 1px;
            background: #555555;
            margin: 4px 0;
        }

        QStatusBar {
            background: #1e1e1e;
            color: #e0e0e0;
            border-top: 1px solid #555555;
        }

        QScrollBar:vertical {
            border: none;
            background: #2d2d2d;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background: #555555;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #666666;
        }

        QScrollBar:horizontal {
            border: none;
            background: #2d2d2d;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background: #555555;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #666666;
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }

        QTabWidget::pane {
            border: 1px solid #555555;
            border-radius: 4px;
            background: #2d2d2d;
        }

        QTabBar::tab {
            padding: 6px 16px;
            border: 1px solid #555555;
            border-bottom: none;
            background: #383838;
            color: #e0e0e0;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected {
            background: #2d2d2d;
            border-bottom: 2px solid #64b5f6;
        }

        QTabBar::tab:hover {
            background: #3d3d3d;
        }

        QSplitter::handle {
            background: #555555;
        }

        QSplitter::handle:horizontal {
            width: 2px;
        }

        QSplitter::handle:vertical {
            height: 2px;
        }

        QHeaderView::section {
            background: #383838;
            color: #e0e0e0;
            padding: 4px 8px;
            border: none;
            border-right: 1px solid #555555;
            border-bottom: 1px solid #555555;
            font-weight: bold;
        }

        QHeaderView::section:hover {
            background: #3d3d3d;
        }

        QCheckBox, QRadioButton {
            color: #e0e0e0;
        }

        QCheckBox::indicator, QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #555555;
            border-radius: 3px;
            background: #383838;
        }

        QCheckBox::indicator:hover, QRadioButton::indicator:hover {
            border-color: #64b5f6;
        }

        QCheckBox::indicator:checked {
            background: #64b5f6;
            border-color: #64b5f6;
        }

        QRadioButton::indicator {
            border-radius: 8px;
        }

        QRadioButton::indicator:checked {
            background: #64b5f6;
            border-color: #64b5f6;
        }

        QLabel {
            color: #e0e0e0;
        }
    """
}


def get_theme(name: str) -> str:
    """
    获取指定名称的主题样式表 | Get theme stylesheet by name

    Args:
        name: 主题名称 ('light' 或 'dark') | Theme name ('light' or 'dark')

    Returns:
        QSS 样式表字符串 | QSS stylesheet string
    """
    return _THEMES.get(name, _THEMES['light'])


def get_available_themes() -> dict:
    """
    获取所有可用主题的名称和显示文本 | Get all available themes with display names

    Returns:
        字典，键为主题名称，值为显示文本 | Dict with theme names as keys and display text as values
    """
    return {
        'light': '浅色 Light',
        'dark': '暗色 Dark'
    }


def get_saved_theme() -> str:
    """
    从配置文件读取保存的主题名称 | Load saved theme name from settings

    Returns:
        主题名称，默认为 'light' | Theme name, defaults to 'light'
    """
    settings = QSettings('ArkManager', 'ArkManager')
    return settings.value('theme', 'light', str)


def save_theme(name: str):
    """
    保存主题名称到配置文件 | Save theme name to settings

    Args:
        name: 主题名称 ('light' 或 'dark') | Theme name ('light' or 'dark')
    """
    if name not in _THEMES:
        name = 'light'  # 默认回退到浅色主题 | Default fallback to light theme

    settings = QSettings('ArkManager', 'ArkManager')
    settings.setValue('theme', name)
    settings.sync()
