"""john_backend模块的单元测试 | Unit tests for john_backend module.

测试覆盖 | Test coverage:
- JohnBackend类的初始化 | JohnBackend class initialization
- 哈希提取器映射表 | Hash extractor mappings
- 攻击模式枚举 | Attack mode enumerations
- 不支持格式的错误处理 | Error handling for unsupported formats

注意：这些测试不依赖实际的JTR安装，只测试接口和数据结构。
Note: These tests don't depend on actual JTR installation, only test interfaces and data structures.
"""

import pytest

from arkmanager.john_backend import JohnBackend, AttackMode, JohnResult


# ==================== 测试类 | Test Classes ====================


class TestJohnResult:
    def test_defaults(self):
        result = JohnResult()
        assert not result.found
        assert result.password == ""
        assert result.error == ""


class TestJohnBackend:
    def test_init(self):
        john = JohnBackend()
        # Should not raise even if john is not installed
        assert john.john_path

    def test_hash_extractors(self):
        assert ".zip" in JohnBackend.HASH_EXTRACTORS
        assert ".rar" in JohnBackend.HASH_EXTRACTORS
        assert ".7z" in JohnBackend.HASH_EXTRACTORS
        assert ".pdf" in JohnBackend.HASH_EXTRACTORS

    def test_unsupported_format(self):
        john = JohnBackend()
        success, path, error = john.extract_hash("/test/file.xyz")
        assert not success
        assert "Unsupported" in error

    def test_attack_modes(self):
        assert AttackMode.WORDLIST.value == "wordlist"
        assert AttackMode.INCREMENTAL.value == "incremental"
        assert AttackMode.SINGLE.value == "single"
        assert AttackMode.MASK.value == "mask"
