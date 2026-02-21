"""Encoding detection and conversion utilities for archive filenames."""

import struct
from typing import Optional

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False


# Common encodings for CJK archives
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
    """Detect the encoding of raw bytes using chardet."""
    if not HAS_CHARDET:
        return None
    result = chardet.detect(data)
    if result and result.get("encoding"):
        return result["encoding"]
    return None


def try_decode(data: bytes, encoding: str) -> Optional[str]:
    """Try to decode bytes with the given encoding."""
    try:
        return data.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return None


def fix_zip_filename(filename: str, source_encoding: str = "cp437",
                     target_encoding: str = "gbk") -> str:
    """Fix a garbled ZIP filename by re-encoding from source to target."""
    try:
        raw_bytes = filename.encode(source_encoding)
        return raw_bytes.decode(target_encoding)
    except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
        return filename


def auto_detect_zip_filename(filename: str) -> str:
    """Auto-detect and fix ZIP filename encoding."""
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

    # Fallback: try common CJK encodings
    for enc, _ in CJK_ENCODINGS:
        if enc in ("utf-8", "cp437", "cp850", "latin-1"):
            continue
        decoded = try_decode(raw_bytes, enc)
        if decoded and not any(ord(c) < 32 for c in decoded if c != '\n'):
            return decoded

    return filename


def detect_zip_pseudo_encryption(filepath: str) -> dict:
    """Detect if a ZIP file uses pseudo/fake encryption.

    Checks for inconsistencies between local file headers and central
    directory headers regarding encryption flags.

    Returns dict with:
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

    # Collect LFH entries
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

    # Collect CDH entries
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

    # Compare LFH and CDH entries
    encrypted_lfh = sum(1 for e in lfh_entries if e["encrypted_flag"])
    encrypted_cdh = sum(1 for e in cdh_entries if e["encrypted_flag"])

    # Case 1: Encryption flag set but compression method is STORED (0) or
    # DEFLATED (8) without encryption header data
    for i, lfh in enumerate(lfh_entries):
        entry_info = {
            "filename": lfh["filename"].decode("utf-8", errors="replace"),
            "lfh_encrypted": lfh["encrypted_flag"],
            "cdh_encrypted": cdh_entries[i]["encrypted_flag"] if i < len(cdh_entries) else None,
            "is_pseudo": False,
        }

        if i < len(cdh_entries):
            cdh = cdh_entries[i]
            # Mismatch between LFH and CDH encryption flags
            if lfh["encrypted_flag"] != cdh["encrypted_flag"]:
                entry_info["is_pseudo"] = True
                result["is_pseudo_encrypted"] = True
                result["details"].append(
                    f"Entry '{entry_info['filename']}': LFH encrypted={lfh['encrypted_flag']}, "
                    f"CDH encrypted={cdh['encrypted_flag']} - MISMATCH"
                )

        result["entries"].append(entry_info)

    # Case 2: Both flags set but no actual encryption data
    # (heuristic: check if data starts with expected compression signatures)
    if encrypted_lfh > 0 and encrypted_cdh > 0:
        # If both say encrypted, check for common pseudo-encryption pattern:
        # encryption bit set but no encryption method specified
        for i, lfh in enumerate(lfh_entries):
            if lfh["encrypted_flag"] and lfh["compression"] in (0, 8):
                # Check if removing the flag would allow normal extraction
                # This is a heuristic - true encrypted files have additional
                # encryption header bytes
                data_offset = lfh["offset"] + 30 + \
                    struct.unpack_from("<H", data, lfh["offset"] + 26)[0] + \
                    struct.unpack_from("<H", data, lfh["offset"] + 28)[0]

                if data_offset < len(data):
                    # For STORED files with encryption flag, the data should
                    # have a 12-byte encryption header. If data looks like
                    # normal file content, it's likely pseudo-encrypted.
                    if lfh["compression"] == 0:  # STORED
                        # Check first bytes for common file signatures
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
    """Remove fake encryption flags from a ZIP file.

    Clears bit 0 (encryption flag) from both LFH and CDH headers.
    """
    SIG_LFH = b"\x50\x4b\x03\x04"
    SIG_CDH = b"\x50\x4b\x01\x02"

    try:
        with open(filepath, "rb") as f:
            data = bytearray(f.read())
    except (OSError, IOError):
        return False

    patched = 0
    # Patch LFH entries (flag at offset +6)
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

    # Patch CDH entries (flag at offset +8)
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
