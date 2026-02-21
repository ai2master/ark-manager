"""Tests for john_backend module."""

import pytest

from arkmanager.john_backend import JohnBackend, AttackMode, JohnResult


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
