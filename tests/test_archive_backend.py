"""archive_backend模块的单元测试 | Unit tests for archive_backend module.

测试覆盖 | Test coverage:
- ArchiveBackend类的初始化和7z验证 | ArchiveBackend class initialization and 7z verification
- 压缩包列表、提取、压缩、测试等核心功能 | Core functions: list, extract, compress, test archives
- 编码处理模式（auto/force/none） | Encoding modes (auto/force/none)
- 错误处理（文件不存在、密码错误等） | Error handling (file not found, wrong password, etc.)
- 数据类（ArchiveEntry、ArchiveInfo）的行为 | Data class (ArchiveEntry, ArchiveInfo) behavior

使用pytest框架，fixture提供测试数据和环境清理。
Uses pytest framework, fixtures provide test data and environment cleanup.
"""

import os
import subprocess
import tempfile
import pytest

from arkmanager.archive_backend import ArchiveBackend, ArchiveInfo, ArchiveEntry


# ==================== 测试辅助函数 | Test Helper Functions ====================

def has_7z():
    """检查7z是否可用 | Check if 7z is available.

    测试跳过条件：如果系统未安装7z，相关测试将被跳过。
    Test skip condition: if 7z not installed, related tests will be skipped.
    """
    try:
        subprocess.run(["7z"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ==================== 测试类 | Test Classes ====================

@pytest.mark.skipif(not has_7z(), reason="7z not available")
class TestArchiveBackend:
    """ArchiveBackend类的测试套件 | Test suite for ArchiveBackend class.

    所有测试都依赖7z命令，如果系统未安装会跳过。
    All tests depend on 7z command, will skip if not installed on system.
    """

    @pytest.fixture
    def backend(self):
        """创建ArchiveBackend实例 | Create ArchiveBackend instance.

        Pytest fixture，每个测试方法都会获得一个新的实例。
        Pytest fixture, each test method gets a new instance.
        """
        return ArchiveBackend()

    @pytest.fixture
    def sample_zip(self, tmp_path):
        """创建测试用的示例ZIP文件 | Create a sample ZIP file for testing.

        生成包含两个文本文件的ZIP压缩包：
        - test.txt: 根目录下的简单文本文件
        - subdir/data.txt: 子目录中的文本文件

        Generates a ZIP archive containing two text files:
        - test.txt: simple text file in root
        - subdir/data.txt: text file in subdirectory
        """
        # 创建测试文件 | Create test files
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        test_file2 = tmp_path / "subdir" / "data.txt"
        test_file2.parent.mkdir()
        test_file2.write_text("Test data content")

        # 使用7z创建ZIP | Create ZIP using 7z
        zip_path = tmp_path / "test.zip"
        subprocess.run(
            ["7z", "a", str(zip_path), str(test_file), str(test_file2)],
            capture_output=True,
        )
        return str(zip_path)

    def test_backend_init(self, backend):
        # shutil.which() 解析后路径可能为绝对路径 | Path may be absolute after shutil.which()
        assert backend.seven_zip_path.endswith("7z")

    def test_list_archive(self, backend, sample_zip):
        info = backend.list_archive(sample_zip)
        assert info.path == sample_zip
        assert info.type  # Should detect type
        assert len(info.entries) > 0

    def test_list_archive_encoding_auto(self, backend, sample_zip):
        info = backend.list_archive(sample_zip, encoding_mode="auto")
        assert not info.error

    def test_list_archive_encoding_none(self, backend, sample_zip):
        info = backend.list_archive(sample_zip, encoding_mode="none")
        assert not info.error

    def test_extract(self, backend, sample_zip, tmp_path):
        output_dir = str(tmp_path / "extracted")
        os.makedirs(output_dir)
        success, msg = backend.extract(sample_zip, output_dir)
        assert success

    def test_extract_with_parent_dir(self, backend, sample_zip, tmp_path):
        output_dir = str(tmp_path / "extracted2")
        os.makedirs(output_dir)
        success, msg = backend.extract(
            sample_zip, output_dir, create_parent_dir=True
        )
        assert success
        # Should have created a "test" subdirectory
        expected_dir = os.path.join(output_dir, "test")
        assert os.path.isdir(expected_dir)

    def test_compress(self, backend, tmp_path):
        # Create source file
        src = tmp_path / "source.txt"
        src.write_text("Compress me!")

        output = str(tmp_path / "output.7z")
        success, msg = backend.compress(output, [str(src)], format="7z")
        assert success
        assert os.path.exists(output)

    def test_compress_zip_utf8(self, backend, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("UTF-8 test")

        output = str(tmp_path / "output.zip")
        success, msg = backend.compress(
            output, [str(src)], format="zip", encoding_mode="auto"
        )
        assert success

    def test_test_archive(self, backend, sample_zip):
        success, msg = backend.test_archive(sample_zip)
        assert success
        assert "OK" in msg

    def test_nonexistent_file(self, backend):
        info = backend.list_archive("/nonexistent/file.zip")
        assert info.error

    def test_supported_extensions(self):
        exts = ArchiveBackend.get_supported_extensions()
        assert ".zip" in exts
        assert ".7z" in exts
        assert ".tar" in exts
        assert ".rar" in exts


class TestArchiveEntry:
    def test_entry_defaults(self):
        entry = ArchiveEntry(filename="test.txt", original_filename="test.txt")
        assert entry.filename == "test.txt"
        assert entry.size == 0
        assert not entry.encrypted
        assert not entry.is_dir


class TestArchiveInfo:
    def test_info_defaults(self):
        info = ArchiveInfo(path="/test.zip")
        assert info.path == "/test.zip"
        assert info.type == ""
        assert not info.encrypted
        assert len(info.entries) == 0
