"""Tests for archive_backend module."""

import os
import subprocess
import tempfile
import pytest

from arkmanager.archive_backend import ArchiveBackend, ArchiveInfo, ArchiveEntry


def has_7z():
    """Check if 7z is available."""
    try:
        subprocess.run(["7z"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.mark.skipif(not has_7z(), reason="7z not available")
class TestArchiveBackend:
    @pytest.fixture
    def backend(self):
        return ArchiveBackend()

    @pytest.fixture
    def sample_zip(self, tmp_path):
        """Create a sample ZIP file for testing."""
        # Create test files
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        test_file2 = tmp_path / "subdir" / "data.txt"
        test_file2.parent.mkdir()
        test_file2.write_text("Test data content")

        # Create ZIP
        zip_path = tmp_path / "test.zip"
        subprocess.run(
            ["7z", "a", str(zip_path), str(test_file), str(test_file2)],
            capture_output=True,
        )
        return str(zip_path)

    def test_backend_init(self, backend):
        assert backend.seven_zip_path == "7z"

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
