"""Tests for encoding_utils module."""

import os
import struct
import tempfile
import pytest

from arkmanager.encoding_utils import (
    detect_encoding,
    try_decode,
    fix_zip_filename,
    auto_detect_zip_filename,
    detect_zip_pseudo_encryption,
    patch_pseudo_encryption,
    HAS_CHARDET,
)


class TestTryDecode:
    def test_valid_utf8(self):
        data = "Hello".encode("utf-8")
        assert try_decode(data, "utf-8") == "Hello"

    def test_valid_gbk(self):
        data = "测试".encode("gbk")
        assert try_decode(data, "gbk") == "测试"

    def test_invalid_encoding(self):
        data = b"\xff\xfe"
        result = try_decode(data, "ascii")
        assert result is None

    def test_unknown_encoding(self):
        result = try_decode(b"test", "nonexistent-encoding")
        assert result is None


class TestFixZipFilename:
    def test_gbk_filename(self):
        # Simulate a GBK-encoded filename that was decoded as CP437
        original = "测试文件.txt"
        gbk_bytes = original.encode("gbk")
        garbled = gbk_bytes.decode("cp437", errors="replace")
        fixed = fix_zip_filename(garbled, "cp437", "gbk")
        # Should recover the original
        assert fixed == original

    def test_already_correct(self):
        result = fix_zip_filename("normal_file.txt", "cp437", "gbk")
        # ASCII filenames should pass through
        assert "normal" in result or result == "normal_file.txt"

    def test_unencodable_returns_original(self):
        # If the filename can't be encoded to source encoding, return as-is
        result = fix_zip_filename("日本語テスト", "ascii", "gbk")
        assert result == "日本語テスト"


class TestDetectEncoding:
    @pytest.mark.skipif(not HAS_CHARDET, reason="chardet not installed")
    def test_detect_gbk(self):
        data = "这是一个测试文件名称".encode("gbk")
        enc = detect_encoding(data)
        assert enc is not None
        # chardet might detect as GB2312 or GBK or GB18030
        assert enc.lower() in ("gb2312", "gbk", "gb18030", "iso-8859-1", "windows-1252")

    @pytest.mark.skipif(not HAS_CHARDET, reason="chardet not installed")
    def test_detect_utf8(self):
        data = "Hello World".encode("utf-8")
        enc = detect_encoding(data)
        assert enc is not None


class TestPseudoEncryption:
    def _make_minimal_zip(self, lfh_encrypted=False, cdh_encrypted=False):
        """Create a minimal ZIP file with controlled encryption flags."""
        # Minimal ZIP with one STORED file
        filename = b"test.txt"
        data = b"Hello World"

        lfh_flags = 0x01 if lfh_encrypted else 0x00
        cdh_flags = 0x01 if cdh_encrypted else 0x00

        # Local File Header
        lfh = struct.pack(
            "<4sHHHHHIIIHH",
            b"\x50\x4b\x03\x04",  # Signature
            20,           # Version needed
            lfh_flags,    # General purpose bit flag
            0,            # Compression method (STORED)
            0,            # Last mod time
            0,            # Last mod date
            0,            # CRC-32 (placeholder)
            len(data),    # Compressed size
            len(data),    # Uncompressed size
            len(filename),  # Filename length
            0,            # Extra field length
        )
        lfh += filename + data

        # Central Directory Header
        cdh = struct.pack(
            "<4sHHHHHHIIIHHHHHII",
            b"\x50\x4b\x01\x02",  # Signature
            20,           # Version made by
            20,           # Version needed
            cdh_flags,    # General purpose bit flag
            0,            # Compression method
            0,            # Last mod time
            0,            # Last mod date
            0,            # CRC-32
            len(data),    # Compressed size
            len(data),    # Uncompressed size
            len(filename),  # Filename length
            0,            # Extra field length
            0,            # File comment length
            0,            # Disk number start
            0,            # Internal file attributes
            0,            # External file attributes
            0,            # Relative offset of local header
        )
        cdh += filename

        # End of Central Directory
        eocd = struct.pack(
            "<4sHHHHIIH",
            b"\x50\x4b\x05\x06",  # Signature
            0,            # Disk number
            0,            # Disk with central directory
            1,            # Number of entries on this disk
            1,            # Total number of entries
            len(cdh),     # Size of central directory
            len(lfh),     # Offset of central directory
            0,            # Comment length
        )

        return lfh + cdh + eocd

    def test_detect_no_encryption(self):
        data = self._make_minimal_zip(False, False)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(data)
            f.flush()
            result = detect_zip_pseudo_encryption(f.name)
        os.unlink(f.name)
        assert not result["is_pseudo_encrypted"]

    def test_detect_mismatched_flags(self):
        data = self._make_minimal_zip(lfh_encrypted=True, cdh_encrypted=False)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(data)
            f.flush()
            result = detect_zip_pseudo_encryption(f.name)
        os.unlink(f.name)
        assert result["is_pseudo_encrypted"]

    def test_patch_pseudo_encryption(self):
        data = self._make_minimal_zip(lfh_encrypted=True, cdh_encrypted=False)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(data)
            input_path = f.name

        output_path = input_path + ".patched"
        try:
            success = patch_pseudo_encryption(input_path, output_path)
            assert success
            # Verify the patched file has no encryption flags
            result = detect_zip_pseudo_encryption(output_path)
            assert not result["is_pseudo_encrypted"]
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_non_zip_file(self):
        result = detect_zip_pseudo_encryption("/nonexistent/file.zip")
        assert not result["is_pseudo_encrypted"]
        assert "Cannot read" in result["details"][0]


class TestAutoDetect:
    def test_ascii_filename(self):
        result = auto_detect_zip_filename("readme.txt")
        assert result == "readme.txt"

    def test_already_unicode(self):
        # If filename is already properly decoded Unicode, it might not
        # round-trip through cp437
        result = auto_detect_zip_filename("already_unicode_file.txt")
        assert "already_unicode_file" in result
