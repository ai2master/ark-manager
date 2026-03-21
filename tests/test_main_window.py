"""主窗口和对话框的 GUI 测试 | GUI tests for main window and dialogs.

测试覆盖 | Test coverage:
- MainWindow 初始化、菜单栏、工具栏 | MainWindow init, menubar, toolbar
- 编码选择器 | Encoding selector
- 压缩包加载和树视图 | Archive loading and tree view
- 注释面板 | Comment panel
- ExtractDialog / CompressDialog / PseudoEncryptionDialog / JohnDialog
- 操作流程（解压/压缩/测试）| Operation flows
- 多格式往返测试 | Multi-format roundtrip
- 安全测试 | Security tests

Uses pytest-qt, running in headless mode (QT_QPA_PLATFORM=offscreen).
"""

import os

import pytest

from tests.conftest import skip_no_7z

# ==================== MainWindow 基础测试 | MainWindow Basic Tests ====================


class TestMainWindowInit:
    """主窗口初始化和基本结构测试 | Main window init and structure tests."""

    @skip_no_7z
    def test_window_created(self, qapp):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        assert w.windowTitle().startswith("ArkManager")
        w.close()

    @skip_no_7z
    def test_minimum_size(self, qapp):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        assert w.minimumWidth() >= 1000
        assert w.minimumHeight() >= 650
        w.close()

    @skip_no_7z
    def test_menubar_menus(self, qapp):
        """菜单栏包含 File/Actions/Tools/Help | Menubar has File/Actions/Tools/Help."""
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        titles = [a.text() for a in w.menuBar().actions()]
        joined = " ".join(titles)
        assert "File" in joined
        assert "Actions" in joined
        assert "Tools" in joined
        assert "Help" in joined
        w.close()

    @skip_no_7z
    def test_encoding_combo_options(self, qapp):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        combo = w.encoding_combo
        assert combo.count() >= 6
        texts = [combo.itemText(i) for i in range(combo.count())]
        assert any("Auto" in t for t in texts)
        assert any("GBK" in t for t in texts)
        w.close()

    @skip_no_7z
    def test_tree_7_columns(self, qapp):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        assert w.tree.columnCount() == 7
        cols = [w.tree.headerItem().text(i) for i in range(7)]
        assert "Name" in cols
        assert "Size" in cols
        assert "CRC" in cols
        w.close()

    @skip_no_7z
    def test_initial_state_empty(self, qapp):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        assert w.current_archive is None
        assert w.current_path == ""
        assert w.tree.topLevelItemCount() == 0
        w.close()

    @skip_no_7z
    def test_comment_panel_readonly(self, qapp):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        assert w.comment_text.isReadOnly()
        w.close()

    @skip_no_7z
    def test_worker_not_busy_initially(self, qapp):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        assert not w._is_worker_busy()
        w.close()


# ==================== 压缩包加载测试 | Archive Loading Tests ====================


class TestArchiveLoading:

    @skip_no_7z
    def test_load_zip(self, qapp, sample_zip):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        w._load_archive(sample_zip)
        assert w.current_path == sample_zip
        assert w.current_archive is not None
        assert w.tree.topLevelItemCount() > 0
        w.close()

    @skip_no_7z
    def test_load_7z(self, qapp, sample_7z):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        w._load_archive(sample_7z)
        assert w.current_archive is not None
        w.close()

    @skip_no_7z
    def test_load_updates_path_edit(self, qapp, sample_zip):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        w._load_archive(sample_zip)
        assert w.path_edit.text() != ""
        w.close()

    @skip_no_7z
    def test_load_nonexistent(self, qapp, monkeypatch):
        """加载不存在文件不崩溃 | Loading nonexistent file doesn't crash."""
        from PyQt6.QtWidgets import QMessageBox

        from arkmanager.main_window import MainWindow
        # Mock QMessageBox 避免模态对话框阻塞 | Mock to avoid modal blocking
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
        monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: QMessageBox.StandardButton.Ok)
        w = MainWindow()
        w._load_archive("/nonexistent/file.zip")
        w.close()

    @skip_no_7z
    def test_load_commented_zip(self, qapp, commented_zip):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        w._load_archive(commented_zip)
        comment = w.comment_text.toPlainText()
        assert len(comment) > 0
        w.close()

    @skip_no_7z
    def test_encoding_switch(self, qapp, sample_zip):
        from arkmanager.main_window import MainWindow
        w = MainWindow()
        w._load_archive(sample_zip)
        w.encoding_combo.setCurrentIndex(1)
        assert w.tree.topLevelItemCount() > 0
        w.close()


# ==================== ExtractDialog 测试 ====================


class TestExtractDialog:

    @skip_no_7z
    def test_defaults(self, qapp):
        from arkmanager.main_window import ExtractDialog
        dlg = ExtractDialog(filepath="/test/file.zip")
        opts = dlg.get_options()
        assert opts["create_parent_dir"] is True
        assert opts["overwrite"] is True
        dlg.close()

    @skip_no_7z
    def test_password_field(self, qapp):
        from arkmanager.main_window import ExtractDialog
        dlg = ExtractDialog(filepath="/test/file.zip")
        dlg.password_edit.setText("中文密码")
        assert dlg.get_options()["password"] == "中文密码"
        dlg.close()

    @skip_no_7z
    def test_encoding_force(self, qapp):
        from arkmanager.main_window import ExtractDialog
        dlg = ExtractDialog(filepath="/test/file.zip")
        for i in range(dlg.encoding_combo.count()):
            if dlg.encoding_combo.itemData(i) == "force":
                dlg.encoding_combo.setCurrentIndex(i)
                break
        assert dlg.get_options()["encoding_mode"] == "force"
        dlg.close()


# ==================== CompressDialog 测试 ====================


class TestCompressDialog:

    @skip_no_7z
    def test_format_options(self, qapp):
        from arkmanager.main_window import CompressDialog
        dlg = CompressDialog(input_paths=["/test/file.txt"])
        fmts = [dlg.format_combo.itemText(i).lower() for i in range(dlg.format_combo.count())]
        assert "7z" in fmts
        assert "zip" in fmts
        dlg.close()

    @skip_no_7z
    def test_level_range(self, qapp):
        from arkmanager.main_window import CompressDialog
        dlg = CompressDialog(input_paths=["/test/file.txt"])
        assert dlg.level_spin.minimum() == 0
        assert dlg.level_spin.maximum() == 9
        assert dlg.level_spin.value() == 5
        dlg.close()

    @skip_no_7z
    def test_get_options(self, qapp, tmp_path):
        from arkmanager.main_window import CompressDialog
        dlg = CompressDialog(input_paths=[str(tmp_path / "f.txt")])
        dlg.output_edit.setText(str(tmp_path / "out.7z"))
        opts = dlg.get_options()
        assert "output_path" in opts
        assert "format" in opts
        assert "compression_level" in opts
        dlg.close()


# ==================== PseudoEncryptionDialog 测试 ====================


class TestPseudoEncryptionDialog:

    @skip_no_7z
    def test_detect_pseudo(self, qapp, pseudo_encrypted_zip):
        from arkmanager.main_window import PseudoEncryptionDialog
        dlg = PseudoEncryptionDialog(filepath=pseudo_encrypted_zip)
        details = dlg.details_text.toPlainText()
        assert len(details) > 0
        dlg.close()

    @skip_no_7z
    def test_detect_genuine(self, qapp, genuine_encrypted_zip):
        from arkmanager.main_window import PseudoEncryptionDialog
        dlg = PseudoEncryptionDialog(filepath=genuine_encrypted_zip)
        details = dlg.details_text.toPlainText()
        assert "SUSPICIOUS" not in details or "consistent" in details.lower() or "GENUINE" in details
        dlg.close()


# ==================== JohnDialog 测试 ====================


class TestJohnDialog:

    @skip_no_7z
    def test_created(self, qapp):
        from arkmanager.john_backend import JohnBackend
        from arkmanager.main_window import JohnDialog
        dlg = JohnDialog(john_backend=JohnBackend(), archive_path="/test/f.zip")
        assert dlg is not None
        dlg.close()

    @skip_no_7z
    def test_attack_modes(self, qapp):
        from arkmanager.john_backend import JohnBackend
        from arkmanager.main_window import JohnDialog
        dlg = JohnDialog(john_backend=JohnBackend(), archive_path="/test/f.zip")
        assert dlg.mode_combo.count() >= 4
        dlg.close()


# ==================== 多格式操作测试 | Multi-Format Operation Tests ====================


class TestMultiFormat:

    @skip_no_7z
    @pytest.mark.parametrize("fmt", ["7z", "zip", "tar"])
    def test_compress_roundtrip(self, qapp, sample_files, tmp_path, fmt):
        """压缩后解压的完整往返 | Compress then extract roundtrip."""
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        archive = str(tmp_path / f"rt.{fmt}")
        ok, _ = backend.compress(archive, [sample_files["hello"]], format=fmt)
        assert ok
        out = str(tmp_path / f"ext_{fmt}")
        os.makedirs(out)
        ok, _ = backend.extract(archive, out)
        assert ok
        assert len(os.listdir(out)) > 0

    @skip_no_7z
    def test_compress_with_password(self, sample_files, tmp_path):
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        archive = str(tmp_path / "enc.7z")
        ok, _ = backend.compress(archive, [sample_files["hello"]], format="7z", password="pw123")
        assert ok
        out = str(tmp_path / "dec")
        os.makedirs(out)
        ok, _ = backend.extract(archive, out, password="pw123")
        assert ok

    @skip_no_7z
    def test_compress_solid(self, sample_files, tmp_path):
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        archive = str(tmp_path / "solid.7z")
        ok, _ = backend.compress(archive, sample_files["all"], format="7z", solid=True, compression_level=9)
        assert ok

    @skip_no_7z
    def test_compress_zip_gbk(self, sample_files, tmp_path):
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        archive = str(tmp_path / "gbk.zip")
        ok, _ = backend.compress(
            archive, [sample_files["hello"]],
            format="zip", encoding_mode="force", forced_encoding="gbk"
        )
        assert ok

    @skip_no_7z
    def test_test_archive(self, sample_zip):
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        ok, msg = backend.test_archive(sample_zip)
        assert ok
        assert "OK" in msg

    @skip_no_7z
    def test_encrypted_list_with_password(self, encrypted_zip):
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        info = backend.list_archive(encrypted_zip, password="test123")
        assert not info.error or len(info.entries) > 0


# ==================== 安全测试 | Security Tests ====================


class TestSecurity:

    @skip_no_7z
    def test_path_traversal_protection(self, tmp_path):
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        safe = str(tmp_path / "safe")
        os.makedirs(safe)
        with open(os.path.join(safe, "ok.txt"), "w") as f:
            f.write("test")
        parent_before = set(os.listdir(str(tmp_path)))
        backend._fix_extracted_filenames(safe, "auto", "gbk")
        parent_after = set(os.listdir(str(tmp_path)))
        assert parent_before == parent_after

    def test_pseudo_detect_readonly(self, pseudo_encrypted_zip):
        from arkmanager.encoding_utils import detect_zip_pseudo_encryption
        before = open(pseudo_encrypted_zip, "rb").read()
        detect_zip_pseudo_encryption(pseudo_encrypted_zip)
        after = open(pseudo_encrypted_zip, "rb").read()
        assert before == after

    def test_patch_creates_copy(self, pseudo_encrypted_zip, tmp_path):
        from arkmanager.encoding_utils import patch_pseudo_encryption
        before = open(pseudo_encrypted_zip, "rb").read()
        out = str(tmp_path / "patched.zip")
        patch_pseudo_encryption(pseudo_encrypted_zip, out)
        after = open(pseudo_encrypted_zip, "rb").read()
        assert before == after
        assert os.path.exists(out)

    @skip_no_7z
    def test_backend_resolved_path(self):
        from arkmanager.archive_backend import ArchiveBackend
        backend = ArchiveBackend()
        assert backend.seven_zip_path.endswith("7z")


# ==================== 静态方法测试 | Static Method Tests ====================


class TestStaticMethods:

    @skip_no_7z
    def test_format_size(self, qapp):
        from arkmanager.main_window import MainWindow
        assert "B" in MainWindow._format_size(100)
        assert "KB" in MainWindow._format_size(2048)
        assert "MB" in MainWindow._format_size(2 * 1024 * 1024)
        assert "GB" in MainWindow._format_size(2 * 1024 * 1024 * 1024)

    def test_supported_extensions(self):
        from arkmanager.archive_backend import ArchiveBackend
        exts = ArchiveBackend.get_supported_extensions()
        assert ".zip" in exts
        assert ".7z" in exts
        assert ".tar" in exts
        assert ".rar" in exts
        assert ".iso" in exts

    def test_supported_formats_list(self):
        from arkmanager.archive_backend import ArchiveBackend
        fmts = ArchiveBackend.SUPPORTED_FORMATS
        assert "7z" in fmts
        assert "zip" in fmts
        assert "rar" in fmts


# ==================== 数据类测试 | Data Class Tests ====================


class TestDataClasses:

    def test_archive_entry_defaults(self):
        from arkmanager.archive_backend import ArchiveEntry
        e = ArchiveEntry(filename="t.txt", original_filename="t.txt")
        assert e.size == 0
        assert not e.encrypted
        assert not e.is_dir

    def test_archive_entry_custom(self):
        from arkmanager.archive_backend import ArchiveEntry
        e = ArchiveEntry(
            filename="d.pdf", original_filename="d.pdf",
            size=1024, compressed_size=512, encrypted=True, method="LZMA2",
        )
        assert e.size == 1024
        assert e.encrypted

    def test_archive_info_defaults(self):
        from arkmanager.archive_backend import ArchiveInfo
        i = ArchiveInfo(path="/t.zip")
        assert i.type == ""
        assert not i.encrypted
        assert len(i.entries) == 0

    def test_john_result_defaults(self):
        from arkmanager.john_backend import JohnResult
        r = JohnResult()
        assert not r.found
        assert r.password == ""

    def test_attack_modes(self):
        from arkmanager.john_backend import AttackMode
        assert AttackMode.WORDLIST.value == "wordlist"
        assert AttackMode.INCREMENTAL.value == "incremental"
        assert AttackMode.SINGLE.value == "single"
        assert AttackMode.MASK.value == "mask"
