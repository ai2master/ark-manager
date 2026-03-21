"""
对话框模块 | Dialogs module

包含 ArkManager 的所有对话框类。
Contains all dialog classes for ArkManager.
"""

import os
from typing import List

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from .archive_backend import ArchiveBackend
from .encoding_utils import CJK_ENCODINGS
from .hash_tools import SUPPORTED_ALGORITHMS, calculate_multiple
from .i18n import tr
from .john_backend import AttackMode, JohnBackend


class ExtractDialog(QDialog):
    """解压对话框 | Extract dialog."""

    def __init__(self, archive_path: str = "", parent=None, filepath: str = ""):
        super().__init__(parent)
        # 保存压缩包路径 (支持 filepath 别名) | Save archive path (support filepath alias)
        archive_path = archive_path or filepath
        self.archive_path = archive_path
        self.output_dir = ""

        # 设置窗口标题 | Set window title
        self.setWindowTitle(tr("Extract Archive"))
        self.resize(600, 350)

        # 创建布局 | Create layout
        layout = QVBoxLayout(self)

        # 来源组 | Source group
        source_group = QGroupBox(tr("Source"))
        source_layout = QFormLayout()
        self.archive_label = QLabel(archive_path)
        source_layout.addRow(tr("Archive:"), self.archive_label)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # 目标组 | Destination group
        dest_group = QGroupBox(tr("Destination"))
        dest_layout = QVBoxLayout()

        # 目标路径选择 | Destination path selection
        path_layout = QHBoxLayout()
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText(tr("Select destination folder..."))
        self.browse_btn = QPushButton(tr("Browse..."))
        self.browse_btn.clicked.connect(self._browse_destination)
        path_layout.addWidget(self.dest_edit)
        path_layout.addWidget(self.browse_btn)
        dest_layout.addLayout(path_layout)

        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)

        # 选项组 | Options group
        options_group = QGroupBox(tr("Options"))
        options_layout = QVBoxLayout()

        self.create_folder_check = QCheckBox(tr("Create parent folder (named after the archive)"))
        self.create_folder_check.setChecked(True)
        options_layout.addWidget(self.create_folder_check)

        self.overwrite_check = QCheckBox(tr("Overwrite existing files"))
        self.overwrite_check.setChecked(True)  # 默认覆盖 | Default to overwrite
        options_layout.addWidget(self.overwrite_check)

        self.smart_extract_check = QCheckBox(tr("Smart extract (auto-detect subfolder)"))
        self.smart_extract_check.setChecked(True)
        options_layout.addWidget(self.smart_extract_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 编码组 | Encoding group
        encoding_group = QGroupBox(tr("Encoding"))
        encoding_layout = QFormLayout()

        self.encoding_combo = QComboBox()
        self.encoding_combo.addItem(tr("Auto-detect"), "auto")
        self.encoding_combo.addItem(tr("Force encoding"), "force")
        self.encoding_combo.addItem(tr("No encoding fix"), "none")
        self.encoding_combo.currentIndexChanged.connect(self._on_encoding_mode_changed)
        encoding_layout.addRow(tr("Mode:"), self.encoding_combo)

        self.forced_enc_combo = QComboBox()
        # CJK_ENCODINGS 是 (code, name) 元组列表 | CJK_ENCODINGS is list of (code, name) tuples
        for code, name in CJK_ENCODINGS:
            self.forced_enc_combo.addItem(name, code)
        # 默认选择 GBK | Default to GBK
        for i in range(self.forced_enc_combo.count()):
            if self.forced_enc_combo.itemData(i) == "gbk":
                self.forced_enc_combo.setCurrentIndex(i)
                break
        encoding_layout.addRow(tr("Forced encoding:"), self.forced_enc_combo)

        encoding_group.setLayout(encoding_layout)
        layout.addWidget(encoding_group)

        # 密码组 | Password group
        password_group = QGroupBox(tr("Password"))
        password_layout = QVBoxLayout()

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText(tr("Enter password if required (supports Chinese)"))
        password_layout.addWidget(self.password_edit)

        self.show_password_check = QCheckBox(tr("Show password"))
        self.show_password_check.toggled.connect(self._toggle_password_visibility)
        password_layout.addWidget(self.show_password_check)

        password_group.setLayout(password_layout)
        layout.addWidget(password_group)

        # 按钮组 | Button group
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # 设置默认目标路径为压缩包所在目录 | Set default destination to archive directory
        default_dest = os.path.dirname(archive_path) if archive_path else ""
        self.dest_edit.setText(default_dest)

        # 初始化编码模式 | Initialize encoding mode
        self._on_encoding_mode_changed()

    def _on_encoding_mode_changed(self):
        """编码模式改变时更新UI | Update UI when encoding mode changes."""
        mode = self.encoding_combo.currentData()
        # 只有强制模式需要选择编码 | Only force mode needs encoding selection
        self.forced_enc_combo.setEnabled(mode == "force")

    def _browse_destination(self):
        """浏览选择目标目录 | Browse for destination directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("Select Destination"),
            self.dest_edit.text() or os.path.expanduser("~")
        )
        if folder:
            self.dest_edit.setText(folder)

    def _toggle_password_visibility(self, checked: bool):
        """切换密码可见性 | Toggle password visibility."""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def get_options(self) -> dict:
        """
        获取解压选项 | Get extraction options.

        Returns:
            包含所有解压选项的字典 | Dictionary containing all extraction options
        """
        # 获取密码，空字符串返回 None | Get password, return None for empty string
        password = self.password_edit.text()
        password = password if password else None

        # 获取编码模式 | Get encoding mode
        encoding_mode = self.encoding_combo.currentData()
        forced_encoding = self.forced_enc_combo.currentData() if encoding_mode == "force" else ""

        return {
            'archive_path': self.archive_path,
            'output_dir': self.dest_edit.text(),
            'password': password,
            'create_parent_dir': self.create_folder_check.isChecked(),
            'overwrite': self.overwrite_check.isChecked(),
            'smart_extract': self.smart_extract_check.isChecked(),
            'encoding_mode': encoding_mode,
            'forced_encoding': forced_encoding,
        }


class CompressDialog(QDialog):
    """压缩对话框 | Compress dialog."""

    def __init__(self, files: List[str] = None, parent=None, input_paths: List[str] = None):
        super().__init__(parent)
        # 保存待压缩文件列表 (支持 input_paths 别名)
        # Save list of files to compress (support input_paths alias)
        self.files = files or input_paths or []

        # 设置窗口标题 | Set window title
        self.setWindowTitle(tr("Create Archive"))
        self.resize(650, 500)

        # 创建布局 | Create layout
        layout = QVBoxLayout(self)

        # 来源组 | Source group
        source_group = QGroupBox(tr("Source"))
        source_layout = QVBoxLayout()

        self.files_list = QListWidget()
        if self.files:
            for file in self.files:
                self.files_list.addItem(file)
        source_layout.addWidget(self.files_list)

        # 文件操作按钮 | File operation buttons
        file_btns_layout = QHBoxLayout()
        self.add_files_btn = QPushButton(tr("Add Files..."))
        self.add_files_btn.clicked.connect(self._add_files)
        self.remove_btn = QPushButton(tr("Remove"))
        self.remove_btn.clicked.connect(self._remove_files)
        self.clear_btn = QPushButton(tr("Clear"))
        self.clear_btn.clicked.connect(self._clear_files)
        file_btns_layout.addWidget(self.add_files_btn)
        file_btns_layout.addWidget(self.remove_btn)
        file_btns_layout.addWidget(self.clear_btn)
        file_btns_layout.addStretch()
        source_layout.addLayout(file_btns_layout)

        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # 目标组 | Destination group
        dest_group = QGroupBox(tr("Destination"))
        dest_layout = QVBoxLayout()

        # 目标路径选择 | Destination path selection
        path_layout = QHBoxLayout()
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText(tr("Select output archive file..."))
        # 添加 output_edit 作为 dest_edit 的引用 | Add output_edit as alias for dest_edit
        self.output_edit = self.dest_edit
        self.browse_btn = QPushButton(tr("Browse..."))
        self.browse_btn.clicked.connect(self._browse_destination)
        path_layout.addWidget(self.dest_edit)
        path_layout.addWidget(self.browse_btn)
        dest_layout.addLayout(path_layout)

        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)

        # 格式和压缩组 | Format and compression group
        format_group = QGroupBox(tr("Format && Compression"))
        format_layout = QFormLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItems(['7z', 'zip', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz'])
        self.format_combo.setCurrentText('zip')
        format_layout.addRow(tr("Format:"), self.format_combo)

        self.level_spin = QSpinBox()
        self.level_spin.setRange(0, 9)
        self.level_spin.setValue(5)
        format_layout.addRow(tr("Compression level:"), self.level_spin)

        self.method_combo = QComboBox()
        self.method_combo.addItem(tr("Default"), "")
        self.method_combo.addItem("LZMA2", "LZMA2")
        self.method_combo.addItem("LZMA", "LZMA")
        self.method_combo.addItem("Deflate", "Deflate")
        format_layout.addRow(tr("Method:"), self.method_combo)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # 编码组 (仅ZIP) | Encoding group (ZIP only)
        encoding_group = QGroupBox(tr("Filename Encoding (ZIP only)"))
        encoding_layout = QFormLayout()

        self.encoding_combo = QComboBox()
        self.encoding_combo.addItem(tr("UTF-8 (Recommended)"), "utf-8")
        self.encoding_combo.addItem(tr("Force GBK (CP936)"), "gbk")
        # CJK_ENCODINGS 是 (code, name) 元组列表 | CJK_ENCODINGS is list of (code, name) tuples
        for code, name in CJK_ENCODINGS:
            if code not in ['utf-8', 'gbk']:
                self.encoding_combo.addItem(name, code)
        encoding_layout.addRow(tr("Encoding:"), self.encoding_combo)

        encoding_group.setLayout(encoding_layout)
        layout.addWidget(encoding_group)

        # 加密组 | Encryption group
        encryption_group = QGroupBox(tr("Encryption"))
        encryption_layout = QVBoxLayout()

        password_layout = QFormLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        placeholder_text = tr("Leave empty for no encryption (supports Chinese)")
        self.password_edit.setPlaceholderText(placeholder_text)
        password_layout.addRow(tr("Password:"), self.password_edit)

        self.password_confirm_edit = QLineEdit()
        self.password_confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_edit.setPlaceholderText(tr("Confirm password"))
        password_layout.addRow(tr("Confirm:"), self.password_confirm_edit)
        encryption_layout.addLayout(password_layout)

        self.show_password_check = QCheckBox(tr("Show password"))
        self.show_password_check.toggled.connect(self._toggle_password_visibility)
        encryption_layout.addWidget(self.show_password_check)

        self.encrypt_filenames_check = QCheckBox(tr("Encrypt filenames (7z only)"))
        encryption_layout.addWidget(self.encrypt_filenames_check)

        encryption_group.setLayout(encryption_layout)
        layout.addWidget(encryption_group)

        # 高级选项 | Advanced options
        advanced_group = QGroupBox(tr("Advanced Options"))
        advanced_layout = QFormLayout()

        self.solid_check = QCheckBox(tr("Solid archive (7z only)"))
        advanced_layout.addRow("", self.solid_check)

        self.volumes_edit = QLineEdit()
        self.volumes_edit.setPlaceholderText(tr("e.g., 100m, 4g (leave empty for no splitting)"))
        advanced_layout.addRow(tr("Split volumes:"), self.volumes_edit)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        # 按钮组 | Button group
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_files(self):
        """添加文件 | Add files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("Select Files to Compress"),
            os.path.expanduser("~")
        )
        if files:
            for file in files:
                self.files_list.addItem(file)

    def _remove_files(self):
        """移除选中文件 | Remove selected files."""
        for item in self.files_list.selectedItems():
            self.files_list.takeItem(self.files_list.row(item))

    def _clear_files(self):
        """清除所有文件 | Clear all files."""
        self.files_list.clear()

    def _browse_destination(self):
        """浏览选择目标文件 | Browse for destination file."""
        # 根据格式设置默认扩展名 | Set default extension based on format
        format_str = self.format_combo.currentText()
        filter_str = f"{format_str.upper()} Archives (*.{format_str})"

        file, _ = QFileDialog.getSaveFileName(
            self,
            tr("Save Archive As"),
            os.path.expanduser("~"),
            filter_str
        )
        if file:
            self.dest_edit.setText(file)

    def _toggle_password_visibility(self, checked: bool):
        """切换密码可见性 | Toggle password visibility."""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        self.password_confirm_edit.setEchoMode(mode)

    def _on_accept(self):
        """验证并接受 | Validate and accept."""
        # 验证输出路径 | Validate output path
        if not self.dest_edit.text():
            QMessageBox.warning(self, tr("Error"), tr("Please specify output file path."))
            return

        # 验证密码匹配 | Validate passwords match
        if self.password_edit.text() != self.password_confirm_edit.text():
            QMessageBox.warning(self, tr("Error"), tr("Passwords do not match."))
            return

        # 验证文件列表 | Validate file list
        if self.files_list.count() == 0:
            QMessageBox.warning(self, tr("Error"), tr("Please add files to compress."))
            return

        self.accept()

    def get_options(self) -> dict:
        """
        获取压缩选项 | Get compression options.

        Returns:
            包含所有压缩选项的字典 | Dictionary containing all compression options
        """
        # 收集文件列表 | Collect file list
        files = []
        for i in range(self.files_list.count()):
            files.append(self.files_list.item(i).text())

        # 获取密码，空字符串返回 None | Get password, return None for empty string
        password = self.password_edit.text()
        password = password if password else None

        # 获取编码模式 | Get encoding mode
        encoding = self.encoding_combo.currentData()
        if encoding == "utf-8":
            encoding_mode = "auto"
            forced_encoding = ""
        else:
            encoding_mode = "force"
            forced_encoding = encoding

        return {
            'files': files,
            'output_file': self.dest_edit.text(),
            'output_path': self.dest_edit.text(),
            'format': self.format_combo.currentText().lower(),
            'level': self.level_spin.value(),
            'compression_level': self.level_spin.value(),
            'method': self.method_combo.currentData(),
            'password': password,
            'encoding': encoding,
            'encoding_mode': encoding_mode,
            'forced_encoding': forced_encoding,
            'encrypt_filenames': self.encrypt_filenames_check.isChecked(),
            'solid': self.solid_check.isChecked(),
            'volumes': self.volumes_edit.text(),
        }


class JohnDialog(QDialog):
    """密码破解对话框 (John the Ripper) | Password cracking dialog (John the Ripper)."""

    def __init__(self, parent=None, john_backend: JohnBackend = None, archive_path: str = ""):
        super().__init__(parent)
        # 设置窗口标题 | Set window title
        self.setWindowTitle(tr("Password Recovery (John the Ripper)"))
        self.resize(700, 550)

        # John 后端 (支持传入或创建新实例) | John backend (support passed in or create new)
        self.john = john_backend if john_backend is not None else JohnBackend()
        self.hash_text = ""

        # 创建布局 | Create layout
        layout = QVBoxLayout(self)

        # 目标组 | Target group
        target_group = QGroupBox(tr("Target"))
        target_layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText(tr("Select archive file..."))
        # 如果传入了 archive_path，设置到编辑框 | If archive_path passed, set to edit
        if archive_path:
            self.file_edit.setText(archive_path)
        self.browse_btn = QPushButton(tr("Browse..."))
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(self.browse_btn)
        target_layout.addLayout(file_layout)

        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # 哈希提取组 | Hash extraction group
        hash_group = QGroupBox(tr("Hash Extraction"))
        hash_layout = QVBoxLayout()

        self.hash_display = QPlainTextEdit()
        self.hash_display.setReadOnly(True)
        self.hash_display.setMaximumHeight(80)
        self.hash_display.setPlaceholderText(tr("No hash extracted yet"))
        hash_layout.addWidget(self.hash_display)

        hash_btn_layout = QHBoxLayout()
        self.extract_hash_btn = QPushButton(tr("Extract Hash"))
        self.extract_hash_btn.clicked.connect(self._extract_hash)
        hash_btn_layout.addWidget(self.extract_hash_btn)
        hash_btn_layout.addStretch()
        hash_layout.addLayout(hash_btn_layout)

        hash_group.setLayout(hash_layout)
        layout.addWidget(hash_group)

        # 攻击配置组 | Attack configuration group
        attack_group = QGroupBox(tr("Attack Configuration"))
        attack_layout = QFormLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(tr("Wordlist"), AttackMode.WORDLIST)
        self.mode_combo.addItem(tr("Incremental (Brute Force)"), AttackMode.INCREMENTAL)
        self.mode_combo.addItem(tr("Single Crack"), AttackMode.SINGLE)
        self.mode_combo.addItem(tr("Mask Attack"), AttackMode.MASK)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        attack_layout.addRow(tr("Mode:"), self.mode_combo)

        self.wordlist_layout = QHBoxLayout()
        self.wordlist_edit = QLineEdit()
        self.wordlist_btn = QPushButton(tr("Browse..."))
        self.wordlist_btn.clicked.connect(self._browse_wordlist)
        self.wordlist_layout.addWidget(self.wordlist_edit)
        self.wordlist_layout.addWidget(self.wordlist_btn)
        attack_layout.addRow(tr("Wordlist:"), self.wordlist_layout)

        self.format_combo = QComboBox()
        self.format_combo.addItem(tr("Auto"), None)
        self.format_combo.addItem(tr("PKZIP"), "pkzip")
        self.format_combo.addItem(tr("ZIP (AES)"), "ZIP")
        self.format_combo.addItem(tr("RAR"), "rar")
        attack_layout.addRow(tr("Format:"), self.format_combo)

        attack_group.setLayout(attack_layout)
        layout.addWidget(attack_group)

        # 输出组 | Output group
        output_group = QGroupBox(tr("Output"))
        output_layout = QVBoxLayout()

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Monospace", 9))
        output_layout.addWidget(self.output_text)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        output_layout.addWidget(self.progress_bar)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # 按钮组 | Button group
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton(tr("Start Cracking"))
        self.start_btn.clicked.connect(self._start_cracking)
        self.stop_btn = QPushButton(tr("Stop"))
        self.stop_btn.clicked.connect(self._stop_cracking)
        self.stop_btn.setEnabled(False)
        self.close_btn = QPushButton(tr("Close"))
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)
        layout.addLayout(buttons_layout)

        # 初始化模式 | Initialize mode
        self._on_mode_changed()

    def _browse_file(self):
        """浏览选择文件 | Browse for file."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            tr("Select Archive"),
            os.path.expanduser("~"),
            "Archives (*.zip *.7z *.rar);;All Files (*)"
        )
        if file:
            self.file_edit.setText(file)

    def _browse_wordlist(self):
        """浏览选择字典文件 | Browse for wordlist file."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            tr("Select Wordlist"),
            os.path.expanduser("~"),
            "Text Files (*.txt);;All Files (*)"
        )
        if file:
            self.wordlist_edit.setText(file)

    def _on_mode_changed(self):
        """模式改变时更新UI | Update UI when mode changes."""
        mode = self.mode_combo.currentData()
        # 只有 Wordlist 模式需要字典文件 | Only Wordlist mode needs wordlist file
        enable_wordlist = (mode == AttackMode.WORDLIST)
        self.wordlist_edit.setEnabled(enable_wordlist)
        self.wordlist_btn.setEnabled(enable_wordlist)

    def _extract_hash(self):
        """提取哈希 | Extract hash."""
        file_path = self.file_edit.text()
        if not file_path:
            QMessageBox.warning(self, tr("Error"), tr("Please select a target file."))
            return

        self.output_text.appendPlainText(tr("Extracting hash..."))
        self.progress_bar.show()

        try:
            # 提取哈希 | Extract hash
            result = self.john.extract_hash(file_path)

            if result.success and result.hash:
                self.hash_text = result.hash
                self.hash_display.setPlainText(result.hash)
                msg = tr("Hash extracted: {format}").format(
                    format=result.format or "unknown"
                )
                self.output_text.appendPlainText(msg)
            else:
                error_msg = result.error or "Unknown error"
                fail_msg = tr("Hash extraction failed: {error}").format(error=error_msg)
                self.output_text.appendPlainText(fail_msg)
                QMessageBox.warning(self, tr("Error"), fail_msg)
        except Exception as e:
            self.output_text.appendPlainText(f"Exception: {str(e)}")
            QMessageBox.critical(self, tr("Error"), str(e))
        finally:
            self.progress_bar.hide()

    def _start_cracking(self):
        """开始破解 | Start cracking."""
        if not self.hash_text:
            QMessageBox.warning(self, tr("Error"), tr("Extract hash first."))
            return

        mode = self.mode_combo.currentData()
        wordlist = self.wordlist_edit.text() if mode == AttackMode.WORDLIST else None

        # 验证 wordlist 模式必须有字典文件 | Validate wordlist mode requires wordlist file
        if mode == AttackMode.WORDLIST and not wordlist:
            QMessageBox.warning(self, tr("Error"), tr("Please select a wordlist file."))
            return

        self.output_text.clear()
        self.output_text.appendPlainText(f"Starting {mode.value} attack...")
        self.progress_bar.show()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # TODO: 在后台线程运行破解 | Run cracking in background thread
        # 这里需要实现 JohnWorkerThread 并连接信号
        # Need to implement JohnWorkerThread and connect signals

    def _stop_cracking(self):
        """停止破解 | Stop cracking."""
        self.output_text.appendPlainText("Stopping...")
        self.progress_bar.hide()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


class PseudoEncryptionDialog(QDialog):
    """伪加密检测对话框 | Pseudo-encryption detection dialog."""

    def __init__(self, archive_path: str = "", parent=None, filepath: str = ""):
        super().__init__(parent)
        # 支持 filepath 别名 | Support filepath alias
        archive_path = archive_path or filepath
        self.archive_path = archive_path

        # 设置窗口标题 | Set window title
        self.setWindowTitle(tr("Fake Encryption Detection"))
        self.resize(550, 400)

        # 创建布局 | Create layout
        layout = QVBoxLayout(self)

        # 信息标签 | Info label
        basename = os.path.basename(archive_path) if archive_path else ""
        info_label = QLabel(tr("Analyzing: {path}").format(path=basename))
        layout.addWidget(info_label)

        # 结果文本 | Results text
        self.results_text = QPlainTextEdit()
        # 添加 details_text 作为 results_text 的引用 | Add details_text as alias
        self.details_text = self.results_text
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Monospace", 9))
        layout.addWidget(self.results_text)

        # 按钮组 | Button group
        buttons_layout = QHBoxLayout()
        self.analyze_btn = QPushButton(tr("Analyze"))
        self.analyze_btn.clicked.connect(self._analyze)
        self.fix_btn = QPushButton(tr("Remove Fake Encryption"))
        self.fix_btn.clicked.connect(self._fix)
        self.fix_btn.setEnabled(False)
        self.close_btn = QPushButton(tr("Close"))
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.analyze_btn)
        buttons_layout.addWidget(self.fix_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)
        layout.addLayout(buttons_layout)

        # 保存检测结果 | Save detection results
        self.fake_files = []

        # 如果提供了路径，自动分析 | Auto-analyze if path provided
        if archive_path:
            self._analyze()

    def _analyze(self):
        """分析伪加密 | Analyze fake encryption."""
        from .encoding_utils import detect_zip_pseudo_encryption

        self.results_text.clear()
        self.results_text.appendPlainText(tr("Analyzing..."))

        try:
            fake_files = detect_zip_pseudo_encryption(self.archive_path)
            self.fake_files = fake_files

            if fake_files:
                fake_msg = f"\n{tr('Fake encryption detected:')} {len(fake_files)} files\n"
                self.results_text.appendPlainText(fake_msg)
                for file in fake_files:
                    self.results_text.appendPlainText(f"  - {file}")
                self.fix_btn.setEnabled(True)
            else:
                self.results_text.appendPlainText(f"\n{tr('No fake encryption detected.')}")
                self.fix_btn.setEnabled(False)
        except Exception as e:
            self.results_text.appendPlainText(f"\n{tr('Error')}: {str(e)}")
            QMessageBox.critical(self, tr("Error"), str(e))

    def _fix(self):
        """修复伪加密 | Fix fake encryption."""
        from .encoding_utils import patch_pseudo_encryption

        # 选择输出文件 | Select output file
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            tr("Save Patched Archive"),
            os.path.splitext(self.archive_path)[0] + "_fixed.zip",
            "ZIP Archives (*.zip)"
        )

        if not output_file:
            return

        self.results_text.appendPlainText(f"\n{tr('Patching...')}")

        try:
            success = patch_pseudo_encryption(self.archive_path, output_file)
            if success:
                self.results_text.appendPlainText(f"{tr('Success')}: {output_file}")
                save_msg = f"{tr('Archive saved to:')} {output_file}"
                QMessageBox.information(self, tr("Success"), save_msg)
            else:
                self.results_text.appendPlainText(tr("Failed to patch archive."))
                QMessageBox.warning(self, tr("Error"), tr("Failed to patch archive."))
        except Exception as e:
            self.results_text.appendPlainText(f"\n{tr('Error')}: {str(e)}")
            QMessageBox.critical(self, tr("Error"), str(e))


class ChecksumDialog(QDialog):
    """哈希/校验和对话框 | Hash/Checksum dialog."""

    def __init__(self, files: List[str] = None, parent=None):
        super().__init__(parent)
        self.files = files or []

        # 设置窗口标题 | Set window title
        self.setWindowTitle(tr("Checksum / Hash"))
        self.resize(800, 600)

        # 创建布局 | Create layout
        layout = QVBoxLayout(self)

        # 文件选择组 | File selection group
        files_group = QGroupBox(tr("Files"))
        files_layout = QVBoxLayout()

        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        for file in self.files:
            self.files_list.addItem(file)
        files_layout.addWidget(self.files_list)

        # 文件操作按钮 | File operation buttons
        file_btns_layout = QHBoxLayout()
        self.add_btn = QPushButton(tr("Add Files..."))
        self.add_btn.clicked.connect(self._add_files)
        self.remove_btn = QPushButton(tr("Remove"))
        self.remove_btn.clicked.connect(self._remove_files)
        self.clear_btn = QPushButton(tr("Clear"))
        self.clear_btn.clicked.connect(self._clear_files)
        file_btns_layout.addWidget(self.add_btn)
        file_btns_layout.addWidget(self.remove_btn)
        file_btns_layout.addWidget(self.clear_btn)
        file_btns_layout.addStretch()
        files_layout.addLayout(file_btns_layout)

        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        # 算法选择组 | Algorithm selection group
        algo_group = QGroupBox(tr("Select algorithms:"))
        algo_layout = QHBoxLayout()

        self.algo_checks = {}
        for algo in SUPPORTED_ALGORITHMS:
            check = QCheckBox(algo.upper())
            check.setChecked(True)
            self.algo_checks[algo] = check
            algo_layout.addWidget(check)
        algo_layout.addStretch()

        algo_group.setLayout(algo_layout)
        layout.addWidget(algo_group)

        # 结果组 | Results group
        results_group = QGroupBox(tr("Results"))
        results_layout = QVBoxLayout()

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels([tr("File"), tr("Algorithm"), tr("Hash Value")])
        self.results_tree.setAlternatingRowColors(True)
        results_layout.addWidget(self.results_tree)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        results_layout.addWidget(self.progress_bar)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # 按钮组 | Button group
        buttons_layout = QHBoxLayout()
        self.calculate_btn = QPushButton(tr("Calculate"))
        self.calculate_btn.clicked.connect(self._calculate)
        self.copy_all_btn = QPushButton(tr("Copy All"))
        self.copy_all_btn.clicked.connect(self._copy_all)
        self.export_btn = QPushButton(tr("Export..."))
        self.export_btn.clicked.connect(self._export)
        self.close_btn = QPushButton(tr("Close"))
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.calculate_btn)
        buttons_layout.addWidget(self.copy_all_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)
        layout.addLayout(buttons_layout)

    def _add_files(self):
        """添加文件 | Add files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("Select Files"),
            os.path.expanduser("~")
        )
        if files:
            for file in files:
                self.files_list.addItem(file)

    def _remove_files(self):
        """移除选中文件 | Remove selected files."""
        for item in self.files_list.selectedItems():
            self.files_list.takeItem(self.files_list.row(item))

    def _clear_files(self):
        """清除所有文件 | Clear all files."""
        self.files_list.clear()

    def _calculate(self):
        """计算哈希 | Calculate hashes."""
        # 收集文件列表 | Collect file list
        files = []
        for i in range(self.files_list.count()):
            files.append(self.files_list.item(i).text())

        if not files:
            QMessageBox.warning(self, tr("Error"), tr("Please add files first."))
            return

        # 收集选中的算法 | Collect selected algorithms
        algorithms = [algo for algo, check in self.algo_checks.items() if check.isChecked()]

        if not algorithms:
            QMessageBox.warning(self, tr("Error"), tr("Please select at least one algorithm."))
            return

        # 清空结果 | Clear results
        self.results_tree.clear()
        self.progress_bar.setRange(0, len(files))
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        # 计算每个文件的哈希 | Calculate hash for each file
        for idx, filepath in enumerate(files):
            try:
                results = calculate_multiple(filepath, algorithms)

                # 为每个算法添加一行 | Add a row for each algorithm
                file_item = QTreeWidgetItem([os.path.basename(filepath), "", ""])
                self.results_tree.addTopLevelItem(file_item)

                for algo in algorithms:
                    if algo in results:
                        child = QTreeWidgetItem(["", algo.upper(), results[algo]])
                        file_item.addChild(child)

                file_item.setExpanded(True)

            except Exception as e:
                error_item = QTreeWidgetItem([os.path.basename(filepath), "ERROR", str(e)])
                self.results_tree.addTopLevelItem(error_item)

            self.progress_bar.setValue(idx + 1)

        self.progress_bar.hide()
        self.results_tree.resizeColumnToContents(0)
        self.results_tree.resizeColumnToContents(1)

    def _copy_all(self):
        """复制所有结果到剪贴板 | Copy all results to clipboard."""
        from PyQt6.QtWidgets import QApplication

        text_lines = []
        root = self.results_tree.invisibleRootItem()

        for i in range(root.childCount()):
            file_item = root.child(i)
            filename = file_item.text(0)
            text_lines.append(f"File: {filename}")

            for j in range(file_item.childCount()):
                child = file_item.child(j)
                algo = child.text(1)
                hash_val = child.text(2)
                text_lines.append(f"  {algo}: {hash_val}")

            text_lines.append("")

        if text_lines:
            QApplication.clipboard().setText("\n".join(text_lines))
            QMessageBox.information(self, tr("Success"), tr("Copied to clipboard."))
        else:
            QMessageBox.warning(self, tr("Warning"), tr("No results to export."))

    def _export(self):
        """导出结果到文件 | Export results to file."""
        if self.results_tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, tr("Warning"), tr("No results to export."))
            return

        file, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export Checksums"),
            os.path.expanduser("~/checksums.txt"),
            "Text Files (*.txt);;All Files (*)"
        )

        if not file:
            return

        try:
            with open(file, 'w', encoding='utf-8') as f:
                root = self.results_tree.invisibleRootItem()

                for i in range(root.childCount()):
                    file_item = root.child(i)
                    filename = file_item.text(0)
                    f.write(f"File: {filename}\n")

                    for j in range(file_item.childCount()):
                        child = file_item.child(j)
                        algo = child.text(1)
                        hash_val = child.text(2)
                        f.write(f"  {algo}: {hash_val}\n")

                    f.write("\n")

            QMessageBox.information(
                self,
                tr("Success"),
                tr("Checksums exported to {path}").format(path=file)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), str(e))


class BatchExtractDialog(QDialog):
    """批量解压对话框 | Batch extract dialog."""

    def __init__(self, files: List[str] = None, parent=None):
        super().__init__(parent)
        self.files = files or []

        # 设置窗口标题 | Set window title
        self.setWindowTitle(tr("Batch Extract"))
        self.resize(700, 500)

        # 创建布局 | Create layout
        layout = QVBoxLayout(self)

        # 文件列表组 | File list group
        files_group = QGroupBox(tr("Archives to Extract"))
        files_layout = QVBoxLayout()

        self.files_list = QListWidget()
        for file in self.files:
            self.files_list.addItem(file)
        files_layout.addWidget(self.files_list)

        # 文件操作按钮 | File operation buttons
        file_btns_layout = QHBoxLayout()
        self.add_btn = QPushButton(tr("Add Files..."))
        self.add_btn.clicked.connect(self._add_files)
        self.remove_btn = QPushButton(tr("Remove"))
        self.remove_btn.clicked.connect(self._remove_files)
        self.clear_btn = QPushButton(tr("Clear"))
        self.clear_btn.clicked.connect(self._clear_files)
        file_btns_layout.addWidget(self.add_btn)
        file_btns_layout.addWidget(self.remove_btn)
        file_btns_layout.addWidget(self.clear_btn)
        file_btns_layout.addStretch()
        files_layout.addLayout(file_btns_layout)

        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        # 目标目录组 | Destination directory group
        dest_group = QGroupBox(tr("Destination"))
        dest_layout = QVBoxLayout()

        dest_path_layout = QHBoxLayout()
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText(tr("Select destination folder..."))
        self.browse_btn = QPushButton(tr("Browse..."))
        self.browse_btn.clicked.connect(self._browse_destination)
        dest_path_layout.addWidget(self.dest_edit)
        dest_path_layout.addWidget(self.browse_btn)
        dest_layout.addLayout(dest_path_layout)

        self.create_subfolders_check = QCheckBox(tr("Extract each archive to its own subfolder"))
        self.create_subfolders_check.setChecked(True)
        dest_layout.addWidget(self.create_subfolders_check)

        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)

        # 进度组 | Progress group
        progress_group = QGroupBox(tr("Progress"))
        progress_layout = QVBoxLayout()

        self.status_label = QLabel(tr("Ready"))
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # 按钮组 | Button group
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton(tr("Start"))
        self.start_btn.clicked.connect(self._start_extraction)
        self.close_btn = QPushButton(tr("Close"))
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)
        layout.addLayout(buttons_layout)

    def _add_files(self):
        """添加文件 | Add files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("Select Archives to Extract"),
            os.path.expanduser("~"),
            "Archives (*.zip *.7z *.rar *.tar *.tar.gz *.tar.bz2 *.tar.xz);;All Files (*)"
        )
        if files:
            for file in files:
                self.files_list.addItem(file)

    def _remove_files(self):
        """移除选中文件 | Remove selected files."""
        for item in self.files_list.selectedItems():
            self.files_list.takeItem(self.files_list.row(item))

    def _clear_files(self):
        """清除所有文件 | Clear all files."""
        self.files_list.clear()

    def _browse_destination(self):
        """浏览选择目标目录 | Browse for destination directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("Select Destination"),
            self.dest_edit.text() or os.path.expanduser("~")
        )
        if folder:
            self.dest_edit.setText(folder)

    def _start_extraction(self):
        """开始批量解压 | Start batch extraction."""
        # 收集文件列表 | Collect file list
        files = []
        for i in range(self.files_list.count()):
            files.append(self.files_list.item(i).text())

        if not files:
            QMessageBox.warning(self, tr("Error"), tr("Please add archives to extract."))
            return

        dest_dir = self.dest_edit.text()
        if not dest_dir:
            QMessageBox.warning(self, tr("Error"), tr("Please select destination folder."))
            return

        # 设置进度条 | Set up progress bar
        self.progress_bar.setRange(0, len(files))
        self.progress_bar.setValue(0)

        # 禁用开始按钮 | Disable start button
        self.start_btn.setEnabled(False)

        # 逐个解压 | Extract one by one
        backend = ArchiveBackend()
        success_count = 0

        for idx, archive_path in enumerate(files):
            filename = os.path.basename(archive_path)
            self.status_label.setText(
                tr("Extracting {current}/{total}: {name}").format(
                    current=idx + 1,
                    total=len(files),
                    name=filename
                )
            )

            try:
                # 确定输出目录 | Determine output directory
                if self.create_subfolders_check.isChecked():
                    # 创建以压缩包命名的子文件夹 | Create subfolder named after archive
                    basename = os.path.splitext(filename)[0]
                    output_dir = os.path.join(dest_dir, basename)
                else:
                    output_dir = dest_dir

                # 解压 | Extract
                success, _ = backend.extract(archive_path, output_dir)
                if success:
                    success_count += 1

            except Exception as e:
                print(f"Error extracting {filename}: {e}")

            self.progress_bar.setValue(idx + 1)

        # 完成 | Complete
        self.status_label.setText(
            tr("Batch extraction complete. {success}/{total} succeeded.").format(
                success=success_count,
                total=len(files)
            )
        )
        self.start_btn.setEnabled(True)

        QMessageBox.information(
            self,
            tr("Complete"),
            tr("Batch extraction complete. {success}/{total} succeeded.").format(
                success=success_count,
                total=len(files)
            )
        )
