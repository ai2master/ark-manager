"""
哈希/校验和计算模块 | Hash/checksum calculation module

为 ArkManager 提供文件完整性验证功能。
Provides file integrity verification features for ArkManager.
"""

import hashlib
import os
import zlib
from typing import Callable, Dict, List, Optional

# 支持的哈希算法 | Supported hash algorithms
SUPPORTED_ALGORITHMS = ['md5', 'sha1', 'sha256', 'sha512', 'crc32']

# 读取块大小：8MB | Read chunk size: 8MB
CHUNK_SIZE = 8 * 1024 * 1024


def calculate_hash(
    filepath: str,
    algorithm: str = 'sha256',
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> str:
    """
    计算单个文件的哈希值 | Calculate hash for a single file.

    Args:
        filepath: 文件路径 | File path
        algorithm: 算法名称 | Algorithm name (md5/sha1/sha256/sha512/crc32)
        progress_callback: 进度回调 (bytes_read, total_bytes) | Progress callback

    Returns:
        十六进制哈希字符串 | Hex hash string

    Raises:
        FileNotFoundError: 文件不存在 | File does not exist
        ValueError: 不支持的算法 | Unsupported algorithm
    """
    # 验证算法 | Validate algorithm
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"不支持的算法 | Unsupported algorithm: {algorithm}. "
            f"支持的算法 | Supported: {', '.join(SUPPORTED_ALGORITHMS)}"
        )

    # 检查文件是否存在 | Check if file exists
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"文件不存在 | File not found: {filepath}")

    # 获取文件大小 | Get file size
    total_bytes = os.path.getsize(filepath)
    bytes_read = 0

    # 初始化哈希对象 | Initialize hash object
    if algorithm == 'crc32':
        crc_value = 0
    else:
        hasher = hashlib.new(algorithm)

    try:
        with open(filepath, 'rb') as f:
            while True:
                # 读取数据块 | Read data chunk
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                # 更新哈希 | Update hash
                if algorithm == 'crc32':
                    crc_value = zlib.crc32(chunk, crc_value)
                else:
                    hasher.update(chunk)

                # 更新进度 | Update progress
                bytes_read += len(chunk)
                if progress_callback:
                    progress_callback(bytes_read, total_bytes)

        # 返回结果 | Return result
        if algorithm == 'crc32':
            # CRC32 格式化为 8 位大写十六进制 | Format CRC32 as 8-char uppercase hex
            return f"{crc_value & 0xFFFFFFFF:08X}"
        else:
            return hasher.hexdigest()

    except Exception as e:
        raise IOError(f"读取文件时出错 | Error reading file: {e}")


def calculate_multiple(
    filepath: str,
    algorithms: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, str]:
    """
    计算单个文件的多种哈希值 | Calculate multiple hashes for one file.

    只读取文件一次，同时更新所有哈希器，提高效率。
    Reads file once, updates all hashers simultaneously for efficiency.

    Args:
        filepath: 文件路径 | File path
        algorithms: 算法列表，None 则使用全部 | Algorithm list, None for all
        progress_callback: 进度回调 | Progress callback

    Returns:
        {algorithm: hex_hash} 字典 | Dict mapping algorithm to hex hash

    Raises:
        FileNotFoundError: 文件不存在 | File does not exist
        ValueError: 不支持的算法 | Unsupported algorithm
    """
    # 如果未指定算法，使用全部 | Use all algorithms if none specified
    if algorithms is None:
        algorithms = SUPPORTED_ALGORITHMS.copy()

    # 验证所有算法 | Validate all algorithms
    for algo in algorithms:
        if algo not in SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"不支持的算法 | Unsupported algorithm: {algo}. "
                f"支持的算法 | Supported: {', '.join(SUPPORTED_ALGORITHMS)}"
            )

    # 检查文件是否存在 | Check if file exists
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"文件不存在 | File not found: {filepath}")

    # 获取文件大小 | Get file size
    total_bytes = os.path.getsize(filepath)
    bytes_read = 0

    # 初始化所有哈希对象 | Initialize all hash objects
    hashers = {}
    crc_value = None

    for algo in algorithms:
        if algo == 'crc32':
            crc_value = 0
        else:
            hashers[algo] = hashlib.new(algo)

    try:
        with open(filepath, 'rb') as f:
            while True:
                # 读取数据块 | Read data chunk
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                # 同时更新所有哈希器 | Update all hashers simultaneously
                if crc_value is not None:
                    crc_value = zlib.crc32(chunk, crc_value)

                for hasher in hashers.values():
                    hasher.update(chunk)

                # 更新进度 | Update progress
                bytes_read += len(chunk)
                if progress_callback:
                    progress_callback(bytes_read, total_bytes)

        # 收集结果 | Collect results
        results = {}

        if crc_value is not None:
            # CRC32 格式化为 8 位大写十六进制 | Format CRC32 as 8-char uppercase hex
            results['crc32'] = f"{crc_value & 0xFFFFFFFF:08X}"

        for algo, hasher in hashers.items():
            results[algo] = hasher.hexdigest()

        return results

    except Exception as e:
        raise IOError(f"读取文件时出错 | Error reading file: {e}")


def verify_hash(
    filepath: str,
    expected_hash: str,
    algorithm: str = 'sha256'
) -> bool:
    """
    验证文件哈希是否匹配 | Verify if file hash matches expected value.

    不区分大小写进行比较。
    Case-insensitive comparison.

    Args:
        filepath: 文件路径 | File path
        expected_hash: 期望的哈希值 | Expected hash value
        algorithm: 算法名称 | Algorithm name

    Returns:
        是否匹配 | True if hash matches, False otherwise

    Raises:
        FileNotFoundError: 文件不存在 | File does not exist
        ValueError: 不支持的算法 | Unsupported algorithm
    """
    try:
        # 计算实际哈希值 | Calculate actual hash
        actual_hash = calculate_hash(filepath, algorithm)

        # 不区分大小写比较 | Case-insensitive comparison
        return actual_hash.lower() == expected_hash.lower()

    except (FileNotFoundError, ValueError):
        # 传递异常 | Propagate exceptions
        raise
    except Exception as e:
        # 其他错误视为不匹配 | Treat other errors as mismatch
        raise IOError(f"验证哈希时出错 | Error verifying hash: {e}")


def format_hash_report(results: Dict[str, str], filepath: str) -> str:
    """
    格式化哈希结果为可读报告 | Format hash results as readable report.

    Args:
        results: 哈希结果字典 | Hash results dictionary
        filepath: 文件路径 | File path

    Returns:
        多行格式化字符串 | Multi-line formatted string

    Example:
        File: /path/to/file
        Size: 1,234,567 bytes
        MD5:    abc123...
        SHA256: def456...
    """
    lines = []

    # 文件路径 | File path
    lines.append(f"File: {filepath}")

    # 文件大小 | File size
    try:
        size = os.path.getsize(filepath)
        # 使用千位分隔符格式化 | Format with thousands separator
        lines.append(f"Size: {size:,} bytes")
    except Exception:
        lines.append("Size: Unknown")

    # 添加空行 | Add blank line
    lines.append("")

    # 按固定顺序显示哈希值 | Display hashes in fixed order
    algorithm_order = ['crc32', 'md5', 'sha1', 'sha256', 'sha512']

    for algo in algorithm_order:
        if algo in results:
            # 算法名称大写，对齐显示 | Uppercase algorithm name, aligned display
            algo_display = algo.upper()
            lines.append(f"{algo_display:7} {results[algo]}")

    # 添加其他未在预定义顺序中的算法 | Add any other algorithms not in predefined order
    for algo, hash_value in results.items():
        if algo not in algorithm_order:
            algo_display = algo.upper()
            lines.append(f"{algo_display:7} {hash_value}")

    return "\n".join(lines)
