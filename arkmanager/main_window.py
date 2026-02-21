"""Main window for ArkManager archive manager."""

import os
import sys
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QComboBox, QCheckBox,
    QLineEdit, QPushButton, QDialog, QFormLayout, QSpinBox,
    QGroupBox, QRadioButton, QButtonGroup, QProgressBar,
    QTabWidget, QPlainTextEdit, QHeaderView, QMenuBar, QMenu,
    QApplication, QDialogButtonBox, QGridLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont, QColor

from . import __version__, __app_name__
from .archive_backend import ArchiveBackend, ArchiveInfo, ArchiveEntry
from .john_backend import JohnBackend, AttackMode, JohnResult
from .encoding_utils import (
    CJK_ENCODINGS, detect_zip_pseudo_encryption, patch_pseudo_encryption,
)


class WorkerThread(QThread):
    """Generic worker thread for long-running operations."""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str, int)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            if isinstance(result, tuple):
                self.finished.emit(result[0], result[1])
            else:
                self.finished.emit(True, str(result))
        except Exception as e:
            self.finished.emit(False, str(e))


class JohnWorkerThread(QThread):
    """Worker thread for John the Ripper operations."""
    finished = pyqtSignal(object)  # JohnResult
    status_update = pyqtSignal(str)

    def __init__(self, john_backend: JohnBackend, hash_file: str,
                 attack_mode: AttackMode, **kwargs):
        super().__init__()
        self.john = john_backend
        self.hash_file = hash_file
        self.attack_mode = attack_mode
        self.kwargs = kwargs

    def run(self):
        result = self.john.crack(
            self.hash_file,
            attack_mode=self.attack_mode,
            **self.kwargs,
        )
        self.finished.emit(result)


class ExtractDialog(QDialog):
    """Dialog for extraction options."""

    def __init__(self, parent=None, filepath: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Extract Archive")
        self.setMinimumWidth(500)
        self._setup_ui(filepath)

    def _setup_ui(self, filepath):
        layout = QVBoxLayout(self)

        # Source
        src_group = QGroupBox("Source")
        src_layout = QFormLayout()
        self.source_label = QLabel(filepath)
        self.source_label.setWordWrap(True)
        src_layout.addRow("Archive:", self.source_label)
        src_group.setLayout(src_layout)
        layout.addWidget(src_group)

        # Destination
        dest_group = QGroupBox("Destination")
        dest_layout = QHBoxLayout()
        self.dest_edit = QLineEdit()
        self.dest_edit.setText(os.path.dirname(filepath) if filepath else os.path.expanduser("~"))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_dest)
        dest_layout.addWidget(self.dest_edit)
        dest_layout.addWidget(browse_btn)
        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)

        # Options
        opt_group = QGroupBox("Options")
        opt_layout = QVBoxLayout()

        self.create_parent_cb = QCheckBox("Create parent folder (named after the archive)")
        self.create_parent_cb.setChecked(True)
        opt_layout.addWidget(self.create_parent_cb)

        self.overwrite_cb = QCheckBox("Overwrite existing files")
        self.overwrite_cb.setChecked(True)
        opt_layout.addWidget(self.overwrite_cb)

        # Encoding options
        enc_layout = QHBoxLayout()
        enc_layout.addWidget(QLabel("Filename Encoding:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItem("Auto Detect", "auto")
        self.encoding_combo.addItem("Force GBK (Simplified Chinese)", "force")
        self.encoding_combo.addItem("No conversion", "none")
        self.encoding_combo.currentIndexChanged.connect(self._on_encoding_changed)
        enc_layout.addWidget(self.encoding_combo)
        opt_layout.addLayout(enc_layout)

        # Forced encoding selector
        self.forced_enc_layout = QHBoxLayout()
        self.forced_enc_layout.addWidget(QLabel("Forced Encoding:"))
        self.forced_enc_combo = QComboBox()
        for code, name in CJK_ENCODINGS:
            self.forced_enc_combo.addItem(f"{name} ({code})", code)
        self.forced_enc_layout.addWidget(self.forced_enc_combo)
        opt_layout.addLayout(self.forced_enc_layout)
        # Hide by default
        self._set_forced_enc_visible(False)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # Password
        pwd_group = QGroupBox("Password")
        pwd_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter password if required (supports Chinese)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_pwd_cb = QCheckBox("Show")
        self.show_pwd_cb.toggled.connect(
            lambda checked: self.password_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        pwd_layout.addWidget(self.password_edit)
        pwd_layout.addWidget(self.show_pwd_cb)
        pwd_group.setLayout(pwd_layout)
        layout.addWidget(pwd_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_dest(self):
        path = QFileDialog.getExistingDirectory(self, "Select Destination")
        if path:
            self.dest_edit.setText(path)

    def _on_encoding_changed(self, index):
        mode = self.encoding_combo.currentData()
        self._set_forced_enc_visible(mode == "force")

    def _set_forced_enc_visible(self, visible):
        for i in range(self.forced_enc_layout.count()):
            w = self.forced_enc_layout.itemAt(i).widget()
            if w:
                w.setVisible(visible)

    def get_options(self) -> dict:
        mode = self.encoding_combo.currentData()
        return {
            "output_dir": self.dest_edit.text(),
            "create_parent_dir": self.create_parent_cb.isChecked(),
            "overwrite": self.overwrite_cb.isChecked(),
            "encoding_mode": mode,
            "forced_encoding": self.forced_enc_combo.currentData() if mode == "force" else "gbk",
            "password": self.password_edit.text() or None,
        }


class CompressDialog(QDialog):
    """Dialog for compression options."""

    def __init__(self, parent=None, input_paths: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Create Archive")
        self.setMinimumWidth(550)
        self.input_paths = input_paths or []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Output file
        out_group = QGroupBox("Output")
        out_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(self.output_edit)
        out_layout.addWidget(browse_btn)
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)

        # Format and compression
        fmt_group = QGroupBox("Format && Compression")
        fmt_layout = QFormLayout()

        self.format_combo = QComboBox()
        for fmt in ["7z", "zip", "tar", "gz", "bz2", "xz", "wim"]:
            self.format_combo.addItem(fmt.upper(), fmt)
        fmt_layout.addRow("Format:", self.format_combo)

        self.level_spin = QSpinBox()
        self.level_spin.setRange(0, 9)
        self.level_spin.setValue(5)
        self.level_spin.setToolTip("0=Store, 1=Fastest, 5=Normal, 7=Maximum, 9=Ultra")
        fmt_layout.addRow("Compression Level:", self.level_spin)

        self.method_combo = QComboBox()
        self.method_combo.addItem("Default", "")
        self.method_combo.addItem("LZMA2", "LZMA2")
        self.method_combo.addItem("LZMA", "LZMA")
        self.method_combo.addItem("PPMd", "PPMd")
        self.method_combo.addItem("BZip2", "BZip2")
        self.method_combo.addItem("Deflate", "Deflate")
        self.method_combo.addItem("Copy (Store)", "Copy")
        fmt_layout.addRow("Method:", self.method_combo)

        self.solid_cb = QCheckBox("Solid archive (7z only)")
        self.solid_cb.setChecked(True)
        fmt_layout.addRow(self.solid_cb)

        self.volumes_edit = QLineEdit()
        self.volumes_edit.setPlaceholderText("e.g., 100m, 1g (leave empty for single file)")
        fmt_layout.addRow("Split Volumes:", self.volumes_edit)

        fmt_group.setLayout(fmt_layout)
        layout.addWidget(fmt_group)

        # Encoding options
        enc_group = QGroupBox("Filename Encoding (ZIP only)")
        enc_layout = QFormLayout()
        self.enc_mode_combo = QComboBox()
        self.enc_mode_combo.addItem("UTF-8 (Recommended)", "auto")
        self.enc_mode_combo.addItem("Force GBK (CP936)", "force")
        enc_layout.addRow("Encoding:", self.enc_mode_combo)
        enc_group.setLayout(enc_layout)
        layout.addWidget(enc_group)

        # Password
        pwd_group = QGroupBox("Encryption")
        pwd_layout = QFormLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Leave empty for no encryption (supports Chinese)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_layout.addRow("Password:", self.password_edit)

        self.password_confirm = QLineEdit()
        self.password_confirm.setPlaceholderText("Confirm password")
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_layout.addRow("Confirm:", self.password_confirm)

        self.show_pwd_cb = QCheckBox("Show password")
        self.show_pwd_cb.toggled.connect(self._toggle_pwd_visibility)
        pwd_layout.addRow(self.show_pwd_cb)

        self.encrypt_names_cb = QCheckBox("Encrypt filenames (7z only)")
        pwd_layout.addRow(self.encrypt_names_cb)

        pwd_group.setLayout(pwd_layout)
        layout.addWidget(pwd_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_output(self):
        formats = "7z Files (*.7z);;ZIP Files (*.zip);;TAR Files (*.tar);;All Files (*)"
        path, _ = QFileDialog.getSaveFileName(self, "Save Archive As", "", formats)
        if path:
            self.output_edit.setText(path)

    def _toggle_pwd_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        self.password_confirm.setEchoMode(mode)

    def _validate_and_accept(self):
        if not self.output_edit.text():
            QMessageBox.warning(self, "Error", "Please specify output file path.")
            return
        pwd = self.password_edit.text()
        if pwd and pwd != self.password_confirm.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        self.accept()

    def get_options(self) -> dict:
        enc_mode = self.enc_mode_combo.currentData()
        return {
            "output_path": self.output_edit.text(),
            "format": self.format_combo.currentData(),
            "compression_level": self.level_spin.value(),
            "method": self.method_combo.currentData(),
            "solid": self.solid_cb.isChecked(),
            "volumes": self.volumes_edit.text(),
            "encoding_mode": enc_mode,
            "forced_encoding": "gbk" if enc_mode == "force" else "",
            "password": self.password_edit.text() or None,
            "encrypt_filenames": self.encrypt_names_cb.isChecked(),
        }


class JohnDialog(QDialog):
    """Dialog for John the Ripper integration."""

    def __init__(self, parent=None, john_backend: Optional[JohnBackend] = None,
                 archive_path: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Password Recovery - John the Ripper")
        self.setMinimumSize(700, 550)
        self.john = john_backend or JohnBackend()
        self.archive_path = archive_path
        self.hash_file = ""
        self._worker: Optional[JohnWorkerThread] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Status
        if not self.john.is_available():
            warn = QLabel(
                "WARNING: John the Ripper not found!\n"
                "Install: sudo apt install john  (or)  sudo snap install john-the-ripper"
            )
            warn.setStyleSheet("color: red; font-weight: bold; padding: 8px;")
            layout.addWidget(warn)

        # Target file
        target_group = QGroupBox("Target")
        target_layout = QHBoxLayout()
        self.target_edit = QLineEdit(self.archive_path)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_target)
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(browse_btn)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # Hash extraction
        hash_group = QGroupBox("Hash Extraction")
        hash_layout = QHBoxLayout()
        self.extract_btn = QPushButton("Extract Hash")
        self.extract_btn.clicked.connect(self._extract_hash)
        self.hash_status = QLabel("No hash extracted yet")
        hash_layout.addWidget(self.extract_btn)
        hash_layout.addWidget(self.hash_status)
        hash_group.setLayout(hash_layout)
        layout.addWidget(hash_group)

        # Attack mode
        attack_group = QGroupBox("Attack Configuration")
        attack_layout = QFormLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Wordlist", "wordlist")
        self.mode_combo.addItem("Incremental (Brute Force)", "incremental")
        self.mode_combo.addItem("Single Crack", "single")
        self.mode_combo.addItem("Mask Attack", "mask")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        attack_layout.addRow("Attack Mode:", self.mode_combo)

        self.wordlist_layout = QHBoxLayout()
        self.wordlist_edit = QLineEdit()
        self.wordlist_edit.setPlaceholderText("/usr/share/wordlists/rockyou.txt")
        wordlist_browse = QPushButton("Browse...")
        wordlist_browse.clicked.connect(self._browse_wordlist)
        self.wordlist_layout.addWidget(self.wordlist_edit)
        self.wordlist_layout.addWidget(wordlist_browse)
        attack_layout.addRow("Wordlist:", self.wordlist_layout)

        self.mask_edit = QLineEdit()
        self.mask_edit.setPlaceholderText("e.g., ?a?a?a?a?a?a (6 char all)")
        self.mask_edit.setVisible(False)
        attack_layout.addRow("Mask:", self.mask_edit)

        self.charset_combo = QComboBox()
        self.charset_combo.addItem("Default", "")
        self.charset_combo.addItem("Digits", "Digits")
        self.charset_combo.addItem("Alpha", "Alpha")
        self.charset_combo.addItem("Alnum", "Alnum")
        self.charset_combo.addItem("ASCII", "ASCII")
        self.charset_combo.setVisible(False)
        attack_layout.addRow("Charset:", self.charset_combo)

        len_layout = QHBoxLayout()
        self.min_len = QSpinBox()
        self.min_len.setRange(0, 64)
        self.min_len.setValue(0)
        self.min_len.setSpecialValueText("Auto")
        len_layout.addWidget(QLabel("Min:"))
        len_layout.addWidget(self.min_len)
        self.max_len = QSpinBox()
        self.max_len.setRange(0, 64)
        self.max_len.setValue(0)
        self.max_len.setSpecialValueText("Auto")
        len_layout.addWidget(QLabel("Max:"))
        len_layout.addWidget(self.max_len)
        attack_layout.addRow("Password Length:", len_layout)

        self.format_combo = QComboBox()
        self.format_combo.addItem("Auto Detect", "")
        self.format_combo.addItem("PKZIP", "PKZIP")
        self.format_combo.addItem("ZIP (AES)", "ZIP")
        self.format_combo.addItem("RAR5", "rar5")
        self.format_combo.addItem("RAR", "rar")
        self.format_combo.addItem("7z", "7z")
        attack_layout.addRow("Hash Format:", self.format_combo)

        self.extra_args_edit = QLineEdit()
        self.extra_args_edit.setPlaceholderText("Additional john arguments")
        attack_layout.addRow("Extra Args:", self.extra_args_edit)

        attack_group.setLayout(attack_layout)
        layout.addWidget(attack_group)

        # Control buttons
        ctrl_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Cracking")
        self.start_btn.clicked.connect(self._start_crack)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_crack)
        self.stop_btn.setEnabled(False)
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addWidget(self.stop_btn)
        layout.addLayout(ctrl_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Output
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Monospace", 10))
        output_layout.addWidget(self.output_text)

        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        output_layout.addWidget(self.result_label)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _browse_target(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Archive",
            filter="Archives (*.zip *.rar *.7z *.pdf);;All Files (*)"
        )
        if path:
            self.target_edit.setText(path)

    def _browse_wordlist(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist",
            filter="Text Files (*.txt *.lst);;All Files (*)"
        )
        if path:
            self.wordlist_edit.setText(path)

    def _on_mode_changed(self, index):
        mode = self.mode_combo.currentData()
        # Show/hide relevant fields
        for i in range(self.wordlist_layout.count()):
            w = self.wordlist_layout.itemAt(i).widget()
            if w:
                w.setVisible(mode == "wordlist")
        self.mask_edit.setVisible(mode == "mask")
        self.charset_combo.setVisible(mode == "incremental")

    def _extract_hash(self):
        target = self.target_edit.text()
        if not target:
            QMessageBox.warning(self, "Error", "Please select a target file.")
            return

        self.hash_status.setText("Extracting hash...")
        success, hash_file, error = self.john.extract_hash(target)

        if success:
            self.hash_file = hash_file
            self.hash_status.setText(f"Hash extracted: {hash_file}")
            self.hash_status.setStyleSheet("color: green;")
            # Show hash content
            try:
                with open(hash_file) as f:
                    self.output_text.setPlainText(f"Hash content:\n{f.read()}")
            except Exception:
                pass
        else:
            self.hash_status.setText(f"Failed: {error}")
            self.hash_status.setStyleSheet("color: red;")

    def _start_crack(self):
        if not self.hash_file:
            QMessageBox.warning(self, "Error", "Extract hash first.")
            return

        mode_str = self.mode_combo.currentData()
        mode_map = {
            "wordlist": AttackMode.WORDLIST,
            "incremental": AttackMode.INCREMENTAL,
            "single": AttackMode.SINGLE,
            "mask": AttackMode.MASK,
        }
        attack_mode = mode_map.get(mode_str, AttackMode.WORDLIST)

        kwargs = {
            "wordlist": self.wordlist_edit.text(),
            "mask": self.mask_edit.text(),
            "charset": self.charset_combo.currentData(),
            "min_length": self.min_len.value(),
            "max_length": self.max_len.value(),
            "format_hint": self.format_combo.currentData(),
        }

        extra = self.extra_args_edit.text().strip()
        if extra:
            kwargs["extra_args"] = extra.split()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.result_label.setText("")
        self.output_text.appendPlainText("\n--- Starting crack session ---\n")

        self._worker = JohnWorkerThread(
            self.john, self.hash_file, attack_mode, **kwargs
        )
        self._worker.finished.connect(self._on_crack_finished)
        self._worker.start()

    def _stop_crack(self):
        self.john.stop()
        self.stop_btn.setEnabled(False)
        self.output_text.appendPlainText("\n--- Stopped by user ---\n")

    def _on_crack_finished(self, result: JohnResult):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.output_text.appendPlainText(result.status)

        if result.found:
            self.result_label.setText(f"PASSWORD FOUND: {result.password}")
            self.result_label.setStyleSheet(
                "color: green; font-size: 16px; font-weight: bold; "
                "background: #e8f5e9; padding: 8px; border-radius: 4px;"
            )
        elif result.error:
            self.result_label.setText(f"Error: {result.error}")
            self.result_label.setStyleSheet("color: red; font-weight: bold;")
            self.output_text.appendPlainText(f"Error: {result.error}")
        else:
            self.result_label.setText("Password not found with current settings.")
            self.result_label.setStyleSheet("color: orange; font-weight: bold;")

        self._worker = None

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self.john.stop()
            self._worker.wait(5000)
        super().closeEvent(event)


class PseudoEncryptionDialog(QDialog):
    """Dialog showing pseudo-encryption detection results."""

    def __init__(self, parent=None, filepath: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Fake Encryption Detection")
        self.setMinimumSize(600, 400)
        self.filepath = filepath
        self._setup_ui()
        self._run_detection()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.status_label = QLabel("Analyzing...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(self.status_label)

        self.details_text = QPlainTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Monospace", 10))
        layout.addWidget(self.details_text)

        # Patch button
        btn_layout = QHBoxLayout()
        self.patch_btn = QPushButton("Remove Fake Encryption")
        self.patch_btn.clicked.connect(self._patch)
        self.patch_btn.setEnabled(False)
        btn_layout.addWidget(self.patch_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _run_detection(self):
        if not self.filepath.lower().endswith(".zip"):
            self.status_label.setText("Fake encryption detection only works with ZIP files.")
            self.status_label.setStyleSheet("color: orange; font-size: 14px; font-weight: bold;")
            return

        result = detect_zip_pseudo_encryption(self.filepath)

        if result["is_pseudo_encrypted"]:
            self.status_label.setText("FAKE ENCRYPTION DETECTED!")
            self.status_label.setStyleSheet(
                "color: red; font-size: 16px; font-weight: bold; "
                "background: #ffebee; padding: 8px; border-radius: 4px;"
            )
            self.patch_btn.setEnabled(True)
        else:
            self.status_label.setText("No fake encryption detected.")
            self.status_label.setStyleSheet(
                "color: green; font-size: 14px; font-weight: bold; "
                "background: #e8f5e9; padding: 8px; border-radius: 4px;"
            )

        details = "\n".join(result["details"])
        if result["entries"]:
            details += "\n\nEntry Details:\n"
            for e in result["entries"]:
                details += (
                    f"  {e['filename']}: LFH encrypted={e['lfh_encrypted']}, "
                    f"CDH encrypted={e['cdh_encrypted']}, "
                    f"pseudo={e['is_pseudo']}\n"
                )

        self.details_text.setPlainText(details)

    def _patch(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Patched Archive",
            self.filepath.replace(".zip", "_patched.zip"),
            "ZIP Files (*.zip)"
        )
        if not output_path:
            return

        if patch_pseudo_encryption(self.filepath, output_path):
            QMessageBox.information(
                self, "Success",
                f"Fake encryption removed.\nSaved to: {output_path}"
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to patch archive.")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setMinimumSize(1000, 650)

        self.settings = QSettings("ArkManager", "ArkManager")
        self.current_archive: Optional[ArchiveInfo] = None
        self.current_path = ""
        self._worker: Optional[WorkerThread] = None

        try:
            self.backend = ArchiveBackend()
        except RuntimeError as e:
            QMessageBox.critical(None, "Error", str(e))
            sys.exit(1)

        self.john = JohnBackend()

        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._restore_state()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Address bar
        addr_layout = QHBoxLayout()
        addr_layout.addWidget(QLabel("Archive:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Open an archive file...")
        addr_layout.addWidget(self.path_edit)

        # Encoding selector in toolbar area
        addr_layout.addWidget(QLabel("Encoding:"))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItem("Auto Detect", "auto")
        self.encoding_combo.addItem("Force GBK", "force_gbk")
        self.encoding_combo.addItem("Force GB18030", "force_gb18030")
        self.encoding_combo.addItem("Force Big5", "force_big5")
        self.encoding_combo.addItem("Force Shift-JIS", "force_shift_jis")
        self.encoding_combo.addItem("No Conversion", "none")
        self.encoding_combo.setToolTip("Filename encoding for preview")
        self.encoding_combo.currentIndexChanged.connect(self._on_preview_encoding_changed)
        addr_layout.addWidget(self.encoding_combo)

        main_layout.addLayout(addr_layout)

        # Main splitter: tree | comment panel
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: file tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Name", "Size", "Compressed", "Modified", "CRC",
            "Encrypted", "Method"
        ])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.setRootIsDecorated(True)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        left_layout.addWidget(self.tree)

        # Info bar below tree
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("padding: 4px; background: #f5f5f5;")
        left_layout.addWidget(self.info_label)

        self.main_splitter.addWidget(left_widget)

        # Right: comment panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        comment_header = QLabel("Archive Comment")
        comment_header.setStyleSheet(
            "font-weight: bold; font-size: 13px; padding: 6px; "
            "background: #e3f2fd; border-radius: 4px;"
        )
        right_layout.addWidget(comment_header)

        self.comment_text = QTextEdit()
        self.comment_text.setReadOnly(True)
        self.comment_text.setPlaceholderText("No comment in this archive.")
        self.comment_text.setFont(QFont("Sans Serif", 11))
        right_layout.addWidget(self.comment_text)

        # Archive info
        info_header = QLabel("Archive Info")
        info_header.setStyleSheet(
            "font-weight: bold; font-size: 13px; padding: 6px; "
            "background: #e3f2fd; border-radius: 4px;"
        )
        right_layout.addWidget(info_header)

        self.archive_info_text = QTextEdit()
        self.archive_info_text.setReadOnly(True)
        self.archive_info_text.setMaximumHeight(200)
        right_layout.addWidget(self.archive_info_text)

        self.main_splitter.addWidget(right_widget)
        self.main_splitter.setSizes([700, 300])

        main_layout.addWidget(self.main_splitter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def _setup_menubar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Archive...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_archive)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        new_action = QAction("&Create Archive...", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._create_archive)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Actions menu
        actions_menu = menubar.addMenu("&Actions")

        extract_action = QAction("&Extract...", self)
        extract_action.setShortcut(QKeySequence("Ctrl+E"))
        extract_action.triggered.connect(self._extract_archive)
        actions_menu.addAction(extract_action)

        test_action = QAction("&Test Archive", self)
        test_action.setShortcut(QKeySequence("Ctrl+T"))
        test_action.triggered.connect(self._test_archive)
        actions_menu.addAction(test_action)

        actions_menu.addSeparator()

        pseudo_action = QAction("Detect &Fake Encryption...", self)
        pseudo_action.triggered.connect(self._detect_pseudo_encryption)
        actions_menu.addAction(pseudo_action)

        actions_menu.addSeparator()

        add_files_action = QAction("&Add Files to Archive...", self)
        add_files_action.triggered.connect(self._add_files)
        actions_menu.addAction(add_files_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        john_action = QAction("&Password Recovery (John the Ripper)...", self)
        john_action.setShortcut(QKeySequence("Ctrl+J"))
        john_action.triggered.connect(self._open_john)
        tools_menu.addAction(john_action)

        tools_menu.addSeparator()

        bench_action = QAction("&Benchmark...", self)
        bench_action.triggered.connect(self._benchmark)
        tools_menu.addAction(bench_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About ArkManager", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        open_btn = QPushButton("Open")
        open_btn.setToolTip("Open Archive (Ctrl+O)")
        open_btn.clicked.connect(self._open_archive)
        toolbar.addWidget(open_btn)

        extract_btn = QPushButton("Extract")
        extract_btn.setToolTip("Extract Archive (Ctrl+E)")
        extract_btn.clicked.connect(self._extract_archive)
        toolbar.addWidget(extract_btn)

        create_btn = QPushButton("Create")
        create_btn.setToolTip("Create Archive (Ctrl+N)")
        create_btn.clicked.connect(self._create_archive)
        toolbar.addWidget(create_btn)

        toolbar.addSeparator()

        test_btn = QPushButton("Test")
        test_btn.setToolTip("Test Archive Integrity (Ctrl+T)")
        test_btn.clicked.connect(self._test_archive)
        toolbar.addWidget(test_btn)

        pseudo_btn = QPushButton("Fake Enc?")
        pseudo_btn.setToolTip("Detect Fake/Pseudo Encryption")
        pseudo_btn.clicked.connect(self._detect_pseudo_encryption)
        toolbar.addWidget(pseudo_btn)

        toolbar.addSeparator()

        john_btn = QPushButton("Password Recovery")
        john_btn.setToolTip("John the Ripper (Ctrl+J)")
        john_btn.clicked.connect(self._open_john)
        toolbar.addWidget(john_btn)

    def _setup_statusbar(self):
        self.statusBar().showMessage("Ready")

    def _restore_state(self):
        geom = self.settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    # ---- Actions ----

    def _get_encoding_options(self) -> tuple:
        """Get current encoding mode and forced encoding from combo."""
        data = self.encoding_combo.currentData()
        if data == "auto":
            return "auto", "gbk"
        elif data == "none":
            return "none", ""
        elif data.startswith("force_"):
            enc = data.replace("force_", "")
            return "force", enc
        return "auto", "gbk"

    def _open_archive(self):
        exts = " ".join(f"*{e}" for e in ArchiveBackend.get_supported_extensions())
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Archive", "",
            f"Archives ({exts});;All Files (*)"
        )
        if path:
            self._load_archive(path)

    def _load_archive(self, path: str, password: Optional[str] = None):
        """Load and display an archive."""
        self.statusBar().showMessage(f"Loading: {path}")
        self.path_edit.setText(path)
        self.current_path = path

        enc_mode, forced_enc = self._get_encoding_options()

        try:
            info = self.backend.list_archive(
                path, password=password,
                encoding_mode=enc_mode,
                forced_encoding=forced_enc,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        if info.error:
            if "Wrong password" in info.error or "encrypted" in info.error.lower():
                # Ask for password
                from PyQt6.QtWidgets import QInputDialog
                pwd, ok = QInputDialog.getText(
                    self, "Password Required",
                    "This archive is encrypted. Enter password\n(supports Chinese characters):",
                    QLineEdit.EchoMode.Password,
                )
                if ok and pwd:
                    self._load_archive(path, password=pwd)
                return
            else:
                QMessageBox.warning(self, "Error", info.error)
                return

        self.current_archive = info
        self._populate_tree(info)
        self._show_archive_info(info)
        self.statusBar().showMessage(
            f"Loaded: {os.path.basename(path)} | "
            f"{len(info.entries)} entries | "
            f"Type: {info.type}"
        )

    def _populate_tree(self, info: ArchiveInfo):
        """Populate the tree widget with archive entries."""
        self.tree.clear()

        # Build directory structure
        dir_items = {}

        for entry in info.entries:
            parts = entry.filename.replace("\\", "/").split("/")
            parent = self.tree.invisibleRootItem()

            # Build path hierarchy
            current_path = ""
            for i, part in enumerate(parts):
                if not part:
                    continue
                current_path = current_path + "/" + part if current_path else part
                is_last = (i == len(parts) - 1)

                if current_path in dir_items:
                    parent = dir_items[current_path]
                    continue

                item = QTreeWidgetItem(parent)
                item.setText(0, part)

                if is_last and not entry.is_dir:
                    item.setText(1, self._format_size(entry.size))
                    item.setText(2, self._format_size(entry.compressed_size))
                    item.setText(3, entry.modified)
                    item.setText(4, entry.crc)
                    item.setText(5, "Yes" if entry.encrypted else "")
                    item.setText(6, entry.method)
                    item.setData(0, Qt.ItemDataRole.UserRole, entry)

                    if entry.encrypted:
                        item.setForeground(5, QColor("red"))
                else:
                    item.setText(0, part + "/")

                dir_items[current_path] = item
                parent = item

        self.tree.expandAll()

        # Update info label
        total_size = sum(e.size for e in info.entries)
        total_compressed = sum(e.compressed_size for e in info.entries)
        ratio = (1 - total_compressed / total_size * 1.0) * 100 if total_size > 0 else 0
        self.info_label.setText(
            f"Files: {len(info.entries)} | "
            f"Total Size: {self._format_size(total_size)} | "
            f"Compressed: {self._format_size(total_compressed)} | "
            f"Ratio: {ratio:.1f}%"
        )

    def _show_archive_info(self, info: ArchiveInfo):
        """Show archive comment and info in the right panel."""
        # Comment
        if info.comment:
            self.comment_text.setText(info.comment)
            self.comment_text.setStyleSheet(
                "background: #fffde7; border: 2px solid #ffc107; "
                "border-radius: 4px; padding: 8px;"
            )
        else:
            self.comment_text.clear()
            self.comment_text.setStyleSheet("")

        # Archive info
        info_lines = [
            f"Type: {info.type}",
            f"Path: {info.path}",
            f"Physical Size: {self._format_size(info.physical_size)}",
        ]
        if info.method:
            info_lines.append(f"Method: {info.method}")
        if info.solid:
            info_lines.append(f"Solid: {info.solid}")
        if info.blocks:
            info_lines.append(f"Blocks: {info.blocks}")
        if info.encrypted:
            info_lines.append("Encrypted: Yes")
        if info.headers_size:
            info_lines.append(f"Headers Size: {self._format_size(info.headers_size)}")

        self.archive_info_text.setText("\n".join(info_lines))

    def _on_preview_encoding_changed(self, index):
        """Re-load archive with new encoding settings."""
        if self.current_path:
            self._load_archive(self.current_path)

    def _extract_archive(self):
        if not self.current_path:
            QMessageBox.information(self, "Info", "No archive opened.")
            return

        dialog = ExtractDialog(self, self.current_path)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            opts = dialog.get_options()
            self.statusBar().showMessage("Extracting...")
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setVisible(True)

            self._worker = WorkerThread(
                self.backend.extract,
                self.current_path,
                opts["output_dir"],
                password=opts["password"],
                create_parent_dir=opts["create_parent_dir"],
                encoding_mode=opts["encoding_mode"],
                forced_encoding=opts["forced_encoding"],
                overwrite=opts["overwrite"],
            )
            self._worker.finished.connect(self._on_extract_finished)
            self._worker.start()

    def _on_extract_finished(self, success, message):
        self.progress_bar.setVisible(False)
        if success:
            self.statusBar().showMessage("Extraction complete.")
            QMessageBox.information(self, "Success", message)
        else:
            self.statusBar().showMessage("Extraction failed.")
            QMessageBox.warning(self, "Extraction Failed", message)
        self._worker = None

    def _create_archive(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Compress"
        )
        if not files:
            return

        dialog = CompressDialog(self, files)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            opts = dialog.get_options()
            self.statusBar().showMessage("Creating archive...")
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setVisible(True)

            self._worker = WorkerThread(
                self.backend.compress,
                opts["output_path"],
                files,
                format=opts["format"],
                compression_level=opts["compression_level"],
                password=opts["password"],
                encrypt_filenames=opts["encrypt_filenames"],
                solid=opts["solid"],
                method=opts["method"],
                volumes=opts["volumes"],
                encoding_mode=opts["encoding_mode"],
                forced_encoding=opts["forced_encoding"],
            )
            self._worker.finished.connect(self._on_compress_finished)
            self._worker.start()

    def _on_compress_finished(self, success, message):
        self.progress_bar.setVisible(False)
        if success:
            self.statusBar().showMessage("Archive created.")
            QMessageBox.information(self, "Success", message)
            # Open the newly created archive
            # Extract path from message
            if "Archive created:" in message:
                path = message.split("Archive created:")[1].strip()
                if os.path.exists(path):
                    self._load_archive(path)
        else:
            self.statusBar().showMessage("Compression failed.")
            QMessageBox.warning(self, "Compression Failed", message)
        self._worker = None

    def _test_archive(self):
        if not self.current_path:
            QMessageBox.information(self, "Info", "No archive opened.")
            return

        self.statusBar().showMessage("Testing archive...")
        success, message = self.backend.test_archive(self.current_path)

        if success:
            QMessageBox.information(self, "Test Result", message)
        else:
            QMessageBox.warning(self, "Test Result", message)
        self.statusBar().showMessage("Ready")

    def _detect_pseudo_encryption(self):
        if not self.current_path:
            QMessageBox.information(self, "Info", "No archive opened.")
            return

        dialog = PseudoEncryptionDialog(self, self.current_path)
        dialog.exec()

    def _add_files(self):
        if not self.current_path:
            QMessageBox.information(self, "Info", "No archive opened.")
            return

        files, _ = QFileDialog.getOpenFileNames(self, "Add Files to Archive")
        if not files:
            return

        self.statusBar().showMessage("Adding files...")
        args = ["a", self.current_path] + files
        result = self.backend._run_7z(args)

        if result.returncode == 0:
            QMessageBox.information(self, "Success", "Files added to archive.")
            self._load_archive(self.current_path)
        else:
            stderr = result.stderr.decode("utf-8", errors="replace")
            QMessageBox.warning(self, "Error", stderr)
        self.statusBar().showMessage("Ready")

    def _open_john(self):
        dialog = JohnDialog(
            self,
            john_backend=self.john,
            archive_path=self.current_path,
        )
        dialog.exec()

    def _benchmark(self):
        self.statusBar().showMessage("Running 7z benchmark...")
        result = self.backend._run_7z(["b"], timeout=120)
        output = result.stdout.decode("utf-8", errors="replace")

        dialog = QDialog(self)
        dialog.setWindowTitle("7z Benchmark")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Monospace", 10))
        text.setPlainText(output)
        layout.addWidget(text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        dialog.exec()
        self.statusBar().showMessage("Ready")

    def _show_about(self):
        QMessageBox.about(
            self, f"About {__app_name__}",
            f"<h2>{__app_name__} v{__version__}</h2>"
            f"<p>A 7-Zip based archive manager for Linux</p>"
            f"<p>Features:</p>"
            f"<ul>"
            f"<li>Browse, create, and extract archives via 7z</li>"
            f"<li>Chinese filename encoding support (GBK/GB18030/Big5/Shift-JIS)</li>"
            f"<li>Archive comment display</li>"
            f"<li>Fake/pseudo encryption detection</li>"
            f"<li>Chinese password support</li>"
            f"<li>John the Ripper integration for password recovery</li>"
            f"<li>Auto-create parent folder on extraction</li>"
            f"</ul>"
            f"<p>License: GPL-3.0</p>"
            f"<p>Built with PyQt6 + 7z CLI</p>"
        )

    @staticmethod
    def _format_size(size: int) -> str:
        """Format byte size to human readable."""
        if size < 0:
            return ""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if abs(size) < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
            size /= 1024
        return f"{size:.1f} PB"

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self._load_archive(path)
