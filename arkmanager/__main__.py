"""Entry point for ArkManager."""

import sys
import os


def main():
    # Ensure proper encoding for Chinese characters
    if sys.platform == "linux":
        os.environ.setdefault("LANG", "en_US.UTF-8")
        os.environ.setdefault("LC_ALL", "en_US.UTF-8")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName("ArkManager")
    app.setOrganizationName("ArkManager")
    app.setApplicationVersion("1.0.0")

    # Enable drag and drop
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Apply style
    app.setStyleSheet("""
        QMainWindow {
            background: #fafafa;
        }
        QToolBar {
            spacing: 4px;
            padding: 2px;
        }
        QToolBar QPushButton {
            padding: 6px 14px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fff;
            font-size: 13px;
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
        }
        QTreeWidget::item {
            padding: 2px 0;
        }
        QTreeWidget::item:selected {
            background: #e3f2fd;
            color: #000;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 16px;
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
        }
        QPushButton {
            padding: 6px 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: #fff;
        }
        QPushButton:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background: #2196f3;
            border-radius: 3px;
        }
    """)

    from .main_window import MainWindow

    window = MainWindow()
    window.show()

    # Handle command-line file argument
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.isfile(filepath):
            window._load_archive(filepath)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
