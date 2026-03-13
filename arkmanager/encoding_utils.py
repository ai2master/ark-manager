"""编码检测和转换工具 | Encoding detection and conversion utilities.

用于处理压缩包文件名 | For handling archive filenames.
"""

import struct
from typing import Optional

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False


# 常用CJK编码列表 | Common encodings for CJK archives
CJK_ENCODINGS = [
    ("gbk", "GBK (Simplified Chinese)"),
    ("gb2312", "GB2312 (Simplified Chinese)"),
    ("gb18030", "GB18030 (Chinese Universal)"),
    ("big5", "Big5 (Traditional Chinese)"),
    ("shift_jis", "Shift-JIS (Japanese)"),
    ("euc-jp", "EUC-JP (Japanese)"),
    ("euc-kr", "EUC-KR (Korean)"),
    ("cp949", "CP949 (Korean)"),
    ("utf-8", "UTF-8"),
    ("cp437", "CP437 (DOS Latin)"),
    ("cp850", "CP850 (DOS Western European)"),
    ("latin-1", "ISO-8859-1 (Latin-1)"),
]

ZIP_FILENAME_UTF8_FLAG = 0x800


def detect_encoding(data: bytes) -> Optional[str]:
    """使用chardet检测原始字节的编码 | Detect the encoding of raw bytes using chardet."""
    if not HAS_CHARDET:
        return None
    result = chardet.detect(data)
    if result and result.get("encoding"):
        return result["encoding"]
    return None


def try_decode(data: bytes, encoding: str) -> Optional[str]:
    """尝试用指定编码解码字节 | Try to decode bytes with the given encoding."""
    try:
        return data.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return None


def fix_zip_filename(filename: str, source_encoding: str = "cp437",
                     target_encoding: str = "gbk") -> str:
    """通过重新编码修复乱码文件名 | Fix garbled filename by re-encoding."""
    try:
        raw_bytes = filename.encode(source_encoding)
        return raw_bytes.decode(target_encoding)
    except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
        return filename


def auto_detect_zip_filename(filename: str) -> str:
    """自动检测并修复ZIP文件名编码 | Auto-detect and fix ZIP filename encoding."""
    try:
        raw_bytes = filename.encode("cp437")
    except UnicodeEncodeError:
        return filename

    if HAS_CHARDET:
        detected = chardet.detect(raw_bytes)
        if detected and detected.get("encoding"):
            enc = detected["encoding"].lower()
            if enc in ("gb2312", "gbk", "gb18030", "big5", "shift_jis",
                       "euc-jp", "euc-kr", "cp949"):
                decoded = try_decode(raw_bytes, enc)
                if decoded:
                    return decoded

    # 后备方案：尝试常用CJK编码 | Fallback: try common CJK encodings
    for enc, _ in CJK_ENCODINGS:
        if enc in ("utf-8", "cp437", "cp850", "latin-1"):
            continue
        decoded = try_decode(raw_bytes, enc)
        if decoded and not any(ord(c) < 32 for c in decoded if c != '\n'):
            return decoded

    return filename


def detect_zip_pseudo_encryption(filepath: str) -> dict:
    """检测ZIP文件是否使用伪加密 | Detect if ZIP uses pseudo-encryption.

    检查加密标志的不一致性 | Checks for flag inconsistencies.
    Between local file headers and central directory headers.

    返回包含以下内容的字典 | Returns dict with:
        - is_pseudo_encrypted: bool
        - details: list of str describing findings
        - entries: list of dict with per-entry details
    """
    SIG_LFH = b"\x50\x4b\x03\x04"
    SIG_CDH = b"\x50\x4b\x01\x02"

    result = {
        "is_pseudo_encrypted": False,
        "details": [],
        "entries": [],
    }

    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except (OSError, IOError) as e:
        result["details"].append(f"Cannot read file: {e}")
        return result

    # 收集本地文件头条目 | Collect LFH entries
    lfh_entries = []
    pos = 0
    while True:
        pos = data.find(SIG_LFH, pos)
        if pos == -1:
            break
        if pos + 30 > len(data):
            break
        flags = struct.unpack_from("<H", data, pos + 6)[0]
        comp_method = struct.unpack_from("<H", data, pos + 8)[0]
        fname_len = struct.unpack_from("<H", data, pos + 26)[0]
        extra_len = struct.unpack_from("<H", data, pos + 28)[0]
        fname = data[pos + 30:pos + 30 + fname_len]
        lfh_entries.append({
            "offset": pos,
            "flags": flags,
            "encrypted_flag": bool(flags & 0x01),
            "compression": comp_method,
            "filename": fname,
        })
        pos += 30 + fname_len + extra_len + 1

    # 收集中央目录头条目 | Collect CDH entries
    cdh_entries = []
    pos = 0
    while True:
        pos = data.find(SIG_CDH, pos)
        if pos == -1:
            break
        if pos + 46 > len(data):
            break
        flags = struct.unpack_from("<H", data, pos + 8)[0]
        comp_method = struct.unpack_from("<H", data, pos + 10)[0]
        fname_len = struct.unpack_from("<H", data, pos + 28)[0]
        extra_len = struct.unpack_from("<H", data, pos + 30)[0]
        comment_len = struct.unpack_from("<H", data, pos + 32)[0]
        fname = data[pos + 46:pos + 46 + fname_len]
        cdh_entries.append({
            "offset": pos,
            "flags": flags,
            "encrypted_flag": bool(flags & 0x01),
            "compression": comp_method,
            "filename": fname,
        })
        pos += 46 + fname_len + extra_len + comment_len + 1

    # 比较本地文件头和中央目录头条目 | Compare LFH and CDH entries
    encrypted_lfh = sum(1 for e in lfh_entries if e["encrypted_flag"])
    encrypted_cdh = sum(1 for e in cdh_entries if e["encrypted_flag"])

    # 情况1：加密标志已设置但无加密头数据
    # Case 1: Encryption flag set but no encryption header data
    for i, lfh in enumerate(lfh_entries):
        entry_info = {
            "filename": lfh["filename"].decode("utf-8", errors="replace"),
            "lfh_encrypted": lfh["encrypted_flag"],
            "cdh_encrypted": cdh_entries[i]["encrypted_flag"] if i < len(cdh_entries) else None,
            "is_pseudo": False,
        }

        if i < len(cdh_entries):
            cdh = cdh_entries[i]
            # 本地文件头和中央目录头加密标志不匹配 | Mismatch between LFH and CDH encryption flags
            if lfh["encrypted_flag"] != cdh["encrypted_flag"]:
                entry_info["is_pseudo"] = True
                result["is_pseudo_encrypted"] = True
                result["details"].append(
                    f"Entry '{entry_info['filename']}': LFH encrypted={lfh['encrypted_flag']}, "
                    f"CDH encrypted={cdh['encrypted_flag']} - MISMATCH"
                )

        result["entries"].append(entry_info)

    # 情况2：两个标志都已设置但无实际加密数据
    # Case 2: Both flags set but no actual encryption data
    if encrypted_lfh > 0 and encrypted_cdh > 0:
        # 检查常见的伪加密模式：加密位已设置但未指定加密方法
        # Check for common pseudo-encryption pattern
        for i, lfh in enumerate(lfh_entries):
            if lfh["encrypted_flag"] and lfh["compression"] in (0, 8):
                # 检查移除标志是否允许正常提取
                # Check if removing the flag allows normal extraction
                data_offset = lfh["offset"] + 30 + \
                    struct.unpack_from("<H", data, lfh["offset"] + 26)[0] + \
                    struct.unpack_from("<H", data, lfh["offset"] + 28)[0]

                if data_offset < len(data):
                    # 对于带加密标志的STORED文件，数据应该有12字节的加密头
                    # For STORED files with encryption flag
                    if lfh["compression"] == 0:  # STORED
                        # 检查常见文件签名 | Check common file signatures
                        preview = data[data_offset:data_offset + 4]
                        if preview in (b'\x89PNG', b'\xff\xd8\xff', b'PK\x03\x04',
                                       b'\x7fELF', b'%PDF'):
                            result["is_pseudo_encrypted"] = True
                            fname = lfh['filename'].decode('utf-8', errors='replace')
                            result["details"].append(
                                f"Entry '{fname}': Encrypted flag set "
                                f"but data appears unencrypted "
                                f"(recognized file header)"
                            )

    if not result["details"]:
        if encrypted_lfh > 0 or encrypted_cdh > 0:
            result["details"].append(
                f"Archive has {encrypted_lfh} LFH and {encrypted_cdh} CDH "
                f"encrypted entries. Flags are consistent - likely real encryption."
            )
        else:
            result["details"].append("No encryption flags detected.")

    return result


def patch_pseudo_encryption(filepath: str, output_path: str) -> bool:
    """从ZIP文件中移除伪加密标志 | Remove fake encryption flags.

    清除加密标志位 | Clears encryption flag bit from headers.
    """
    SIG_LFH = b"\x50\x4b\x03\x04"
    SIG_CDH = b"\x50\x4b\x01\x02"

    try:
        with open(filepath, "rb") as f:
            data = bytearray(f.read())
    except (OSError, IOError):
        return False

    patched = 0
    # 修补本地文件头条目（标志位于偏移+6） | Patch LFH entries (flag at offset +6)
    pos = 0
    while True:
        pos = data.find(SIG_LFH, pos)
        if pos == -1:
            break
        flags = struct.unpack_from("<H", data, pos + 6)[0]
        if flags & 0x01:
            struct.pack_into("<H", data, pos + 6, flags & 0xFFFE)
            patched += 1
        pos += 4

    # 修补中央目录头条目（标志位于偏移+8） | Patch CDH entries (flag at offset +8)
    pos = 0
    while True:
        pos = data.find(SIG_CDH, pos)
        if pos == -1:
            break
        flags = struct.unpack_from("<H", data, pos + 8)[0]
        if flags & 0x01:
            struct.pack_into("<H", data, pos + 8, flags & 0xFFFE)
            patched += 1
        pos += 4

    if patched > 0:
        try:
            with open(output_path, "wb") as f:
                f.write(data)
            return True
        except (OSError, IOError):
            return False
    return False
