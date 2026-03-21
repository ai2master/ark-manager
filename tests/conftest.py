"""pytest 全局配置和共享 fixture | pytest global configuration and shared fixtures.

提供所有测试共享的 fixture，包括：
- QApplication 实例（GUI 测试必需）
- 临时测试压缩包（ZIP、7z、加密、带注释等）
- ArchiveBackend 实例

Provides shared fixtures for all tests, including:
- QApplication instance (required for GUI tests)
- Temporary test archives (ZIP, 7z, encrypted, with comments, etc.)
- ArchiveBackend instance
"""

import struct
import subprocess

import pytest

# ==================== 辅助函数 | Helper Functions ====================


def has_7z():
    """检查 7z 是否可用 | Check if 7z is available."""
    try:
        subprocess.run(["7z"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def has_john():
    """检查 John the Ripper 是否可用 | Check if John the Ripper is available."""
    try:
        subprocess.run(["john", "--help"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ==================== 标记条件 | Skip Conditions ====================

skip_no_7z = pytest.mark.skipif(not has_7z(), reason="7z not available")
skip_no_john = pytest.mark.skipif(not has_john(), reason="John the Ripper not available")


# ==================== QApplication fixture ====================


@pytest.fixture(scope="session")
def qapp():
    """创建全局 QApplication 实例 | Create global QApplication instance.

    GUI 测试需要 QApplication 实例才能创建 QWidget。
    scope=session 确保整个测试会话只创建一次。

    GUI tests need a QApplication instance to create QWidgets.
    scope=session ensures it's created only once per test session.
    """
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ==================== 压缩包 fixture | Archive Fixtures ====================


@pytest.fixture
def sample_files(tmp_path):
    """创建用于测试的样本文件集 | Create sample file set for testing.

    生成多种类型的测试文件：
    - 文本文件（ASCII、中文）
    - 子目录结构
    - 空文件

    Generates various types of test files:
    - Text files (ASCII, Chinese)
    - Subdirectory structure
    - Empty file
    """
    # 普通文本文件 | Plain text file
    f1 = tmp_path / "hello.txt"
    f1.write_text("Hello, World!", encoding="utf-8")

    # 中文内容文件 | Chinese content file
    f2 = tmp_path / "chinese.txt"
    f2.write_text("你好世界！这是测试文件。", encoding="utf-8")

    # 子目录结构 | Subdirectory structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    f3 = subdir / "nested.txt"
    f3.write_text("Nested file content")

    # 空文件 | Empty file
    f4 = tmp_path / "empty.dat"
    f4.write_bytes(b"")

    return {
        "dir": tmp_path,
        "hello": str(f1),
        "chinese": str(f2),
        "nested": str(f3),
        "empty": str(f4),
        "all": [str(f1), str(f2), str(f3), str(f4)],
    }


@pytest.fixture
def sample_zip(tmp_path, sample_files):
    """创建测试用 ZIP 文件 | Create a test ZIP file."""
    if not has_7z():
        pytest.skip("7z not available")
    zip_path = tmp_path / "test_archive" / "test.zip"
    zip_path.parent.mkdir(exist_ok=True)
    subprocess.run(
        ["7z", "a", str(zip_path)] + sample_files["all"],
        capture_output=True,
    )
    return str(zip_path)


@pytest.fixture
def sample_7z(tmp_path, sample_files):
    """创建测试用 7z 文件 | Create a test 7z file."""
    if not has_7z():
        pytest.skip("7z not available")
    path = tmp_path / "test_archive" / "test.7z"
    path.parent.mkdir(exist_ok=True)
    subprocess.run(
        ["7z", "a", str(path)] + sample_files["all"],
        capture_output=True,
    )
    return str(path)


@pytest.fixture
def encrypted_zip(tmp_path, sample_files):
    """创建加密 ZIP 文件（密码: test123）| Create encrypted ZIP (password: test123)."""
    if not has_7z():
        pytest.skip("7z not available")
    path = tmp_path / "test_archive" / "encrypted.zip"
    path.parent.mkdir(exist_ok=True)
    subprocess.run(
        ["7z", "a", "-ptest123", str(path), sample_files["hello"]],
        capture_output=True,
    )
    return str(path)


@pytest.fixture
def encrypted_7z_with_names(tmp_path, sample_files):
    """创建加密文件名的 7z 文件（密码: secret）| Create 7z with encrypted filenames (password: secret)."""
    if not has_7z():
        pytest.skip("7z not available")
    path = tmp_path / "test_archive" / "encrypted_names.7z"
    path.parent.mkdir(exist_ok=True)
    subprocess.run(
        ["7z", "a", "-psecret", "-mhe=on", str(path), sample_files["hello"]],
        capture_output=True,
    )
    return str(path)


@pytest.fixture
def commented_zip(tmp_path, sample_files):
    """创建带注释的 ZIP 文件 | Create ZIP with comment."""
    if not has_7z():
        pytest.skip("7z not available")
    import zipfile

    path = tmp_path / "test_archive" / "commented.zip"
    path.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(str(path), "w") as zf:
        zf.write(sample_files["hello"], "hello.txt")
        zf.comment = "这是测试注释 | This is a test comment".encode("utf-8")
    return str(path)


@pytest.fixture
def pseudo_encrypted_zip(tmp_path):
    """创建伪加密 ZIP 文件（LFH 加密，CDH 不加密）| Create pseudo-encrypted ZIP (LFH encrypted, CDH not)."""
    filename = b"test.txt"
    data = b"Hello World"

    lfh = struct.pack(
        "<4sHHHHHIIIHH",
        b"\x50\x4b\x03\x04",
        20, 0x01, 0, 0, 0, 0,
        len(data), len(data), len(filename), 0,
    )
    lfh += filename + data

    cdh = struct.pack(
        "<4sHHHHHHIIIHHHHHII",
        b"\x50\x4b\x01\x02",
        20, 20, 0x00, 0, 0, 0, 0,
        len(data), len(data), len(filename),
        0, 0, 0, 0, 0, 0,
    )
    cdh += filename

    eocd = struct.pack(
        "<4sHHHHIIH",
        b"\x50\x4b\x05\x06",
        0, 0, 1, 1, len(cdh), len(lfh), 0,
    )

    path = tmp_path / "pseudo_enc.zip"
    path.write_bytes(lfh + cdh + eocd)
    return str(path)


@pytest.fixture
def genuine_encrypted_zip(tmp_path):
    """创建真加密 ZIP 文件（LFH 和 CDH 都加密）| Create genuinely encrypted ZIP (both LFH and CDH encrypted)."""
    filename = b"test.txt"
    data = b"Hello World"

    lfh = struct.pack(
        "<4sHHHHHIIIHH",
        b"\x50\x4b\x03\x04",
        20, 0x01, 0, 0, 0, 0,
        len(data), len(data), len(filename), 0,
    )
    lfh += filename + data

    cdh = struct.pack(
        "<4sHHHHHHIIIHHHHHII",
        b"\x50\x4b\x01\x02",
        20, 20, 0x01, 0, 0, 0, 0,
        len(data), len(data), len(filename),
        0, 0, 0, 0, 0, 0,
    )
    cdh += filename

    eocd = struct.pack(
        "<4sHHHHIIH",
        b"\x50\x4b\x05\x06",
        0, 0, 1, 1, len(cdh), len(lfh), 0,
    )

    path = tmp_path / "genuine_enc.zip"
    path.write_bytes(lfh + cdh + eocd)
    return str(path)
