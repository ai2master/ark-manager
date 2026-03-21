"""编码检测和转换工具 | Encoding detection and conversion utilities.

该模块解决压缩包中文文件名乱码问题，主要针对ZIP格式。核心问题：
1. ZIP标准使用CP437编码存储文件名，但国内软件常用GBK编码
2. 7z等工具误将GBK字节解析为CP437，导致中文显示为乱码
3. 解决方案：检测编码并重新解码字节序列

还提供ZIP伪加密检测功能，检查加密标志位的一致性。

This module solves Chinese filename garbled text issues in archives, mainly for ZIP format.
Core problem:
1. ZIP standard uses CP437 encoding for filenames, but Chinese software often uses GBK
2. Tools like 7z misinterpret GBK bytes as CP437, causing Chinese to display as garbled text
3. Solution: detect encoding and re-decode byte sequences

Also provides ZIP pseudo-encryption detection by checking encryption flag consistency.
"""

import mmap
import os
import shutil
import struct
from typing import Optional

# 尝试导入chardet用于自动编码检测 | Try importing chardet for automatic encoding detection
try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False


# ==================== 常量定义 | Constant Definitions ====================

# 常用CJK编码列表，按流行度排序 | Common CJK encodings, sorted by popularity
# 用于自动检测和手动选择 | Used for auto-detection and manual selection
CJK_ENCODINGS = [
    ("gbk", "GBK (Simplified Chinese)"),          # 中国大陆最常用 | Most common in mainland China
    ("gb2312", "GB2312 (Simplified Chinese)"),    # GBK的子集 | Subset of GBK
    ("gb18030", "GB18030 (Chinese Universal)"),
    # 中文国标完整版 | Complete Chinese national standard
    ("big5", "Big5 (Traditional Chinese)"),       # 台湾、香港常用 | Common in Taiwan, Hong Kong
    ("shift_jis", "Shift-JIS (Japanese)"),        # 日本常用 | Common in Japan
    ("euc-jp", "EUC-JP (Japanese)"),              # 日本Unix系统 | Japanese Unix systems
    ("euc-kr", "EUC-KR (Korean)"),                # 韩国常用 | Common in Korea
    ("cp949", "CP949 (Korean)"),                  # 韩国Windows | Korean Windows
    ("utf-8", "UTF-8"),                           # 国际标准 | International standard
    ("cp437", "CP437 (DOS Latin)"),               # DOS原始编码 | DOS original encoding
    ("cp850", "CP850 (DOS Western European)"),   # DOS西欧 | DOS Western European
    ("latin-1", "ISO-8859-1 (Latin-1)"),          # 西欧标准 | Western European standard
]

# ZIP通用标志位：第11位表示文件名使用UTF-8编码
# ZIP general purpose flag: bit 11 indicates UTF-8 filename
ZIP_FILENAME_UTF8_FLAG = 0x800


# ==================== 编码检测函数 | Encoding Detection Functions ====================

def detect_encoding(data: bytes) -> Optional[str]:
    """使用chardet检测原始字节的编码 | Detect the encoding of raw bytes using chardet.

    chardet库基于字节频率统计和字符集特征来推测编码。对于CJK文本，
    需要足够的样本量（建议至少20-30个字符）才能准确检测。

    The chardet library infers encoding based on byte frequency statistics
    and charset characteristics. For CJK text, sufficient sample size
    (recommend at least 20-30 characters) is needed for accurate detection.

    Args:
        data: 待检测的原始字节序列 | Raw byte sequence to detect

    Returns:
        检测到的编码名称（如"gbk"、"utf-8"），失败返回None | Detected encoding name, None on failure
    """
    if not HAS_CHARDET:
        return None
    result = chardet.detect(data)
    if result and result.get("encoding"):
        return result["encoding"]
    return None


def try_decode(data: bytes, encoding: str) -> Optional[str]:
    """尝试用指定编码解码字节 | Try to decode bytes with the given encoding.

    安全地尝试解码，不抛出异常。用于批量尝试多种编码时的容错处理。

    Safely attempts decoding without throwing exceptions. Used for error
    tolerance when trying multiple encodings in batch.

    Args:
        data: 待解码的字节序列 | Byte sequence to decode
        encoding: 编码名称（如"gbk"、"utf-8"） | Encoding name (e.g., "gbk", "utf-8")

    Returns:
        解码后的字符串，失败返回None | Decoded string, None on failure
    """
    try:
        return data.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return None


# ==================== 文件名编码修复函数 | Filename Encoding Fix Functions ====================

def fix_zip_filename(filename: str, source_encoding: str = "cp437",
                     target_encoding: str = "gbk") -> str:
    """通过重新编码修复乱码文件名 | Fix garbled filename by re-encoding.

    核心原理：将错误解析的字符串重新编码回原始字节，再用正确的编码解码。
    例如："翱ｯｼｦ┤┐.txt" -> encode(cp437) -> b'\xb2\xe2\xca\xd4' -> decode(gbk) -> "测试.txt"

    Core principle: re-encode incorrectly parsed string back to original bytes,
    then decode with correct encoding.
    Example: "翱ｯｼｦ┤┐.txt" -> encode(cp437) -> b'\xb2\xe2\xca\xd4' -> decode(gbk) -> "测试.txt"

    Args:
        filename: 乱码文件名 | Garbled filename
        source_encoding: 错误使用的编码（通常是cp437） | Incorrectly used encoding (usually cp437)
        target_encoding: 正确的编码（如gbk） | Correct encoding (e.g., gbk)

    Returns:
        修复后的文件名，失败返回原值 | Fixed filename, returns original on failure
    """
    try:
        # 步骤1：用错误编码重新编码，获取原始字节
        # Step 1: re-encode with wrong encoding to get original bytes
        raw_bytes = filename.encode(source_encoding)
        # 步骤2：用正确编码解码原始字节
        # Step 2: decode original bytes with correct encoding
        return raw_bytes.decode(target_encoding)
    except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
        # 如果失败（如无法编码），返回原文件名 | If failed (e.g., cannot encode), return original
        return filename


def auto_detect_zip_filename(filename: str) -> str:
    """自动检测并修复ZIP文件名编码 | Auto-detect and fix ZIP filename encoding.

    自动化流程：
    1. 将疑似乱码的字符串编码为CP437获取原始字节
    2. 如果有chardet，使用它检测字节的真实编码
    3. 如果chardet检测失败，遍历常用CJK编码逐个尝试
    4. 过滤掉包含控制字符的结果（说明解码错误）
    5. 返回第一个合理的解码结果

    Automated workflow:
    1. Encode suspected garbled string as CP437 to get original bytes
    2. If chardet available, use it to detect true encoding of bytes
    3. If chardet fails, try common CJK encodings one by one
    4. Filter results containing control characters (indicating decode error)
    5. Return first reasonable decoded result

    Args:
        filename: 疑似乱码的文件名 | Suspected garbled filename

    Returns:
        修复后的文件名，失败返回原值 | Fixed filename, returns original on failure
    """
    # 步骤1：重新编码为CP437获取原始字节 | Step 1: re-encode as CP437 to get original bytes
    try:
        raw_bytes = filename.encode("cp437")
    except UnicodeEncodeError:
        # 无法编码为CP437，说明不是从CP437误解析的，保持原样
        # Cannot encode to CP437, not misinterpreted from CP437, keep original
        return filename

    # 步骤2：使用chardet自动检测 | Step 2: use chardet for automatic detection
    if HAS_CHARDET:
        detected = chardet.detect(raw_bytes)
        if detected and detected.get("encoding"):
            enc = detected["encoding"].lower()
            # 只处理CJK编码，避免误判 | Only handle CJK encodings to avoid false positives
            if enc in ("gb2312", "gbk", "gb18030", "big5", "shift_jis",
                       "euc-jp", "euc-kr", "cp949"):
                decoded = try_decode(raw_bytes, enc)
                if decoded:
                    return decoded

    # 步骤3：后备方案，遍历常用CJK编码 | Step 3: fallback, try common CJK encodings
    for enc, _ in CJK_ENCODINGS:
        # 跳过非CJK编码，避免误判 | Skip non-CJK encodings to avoid false positives
        if enc in ("utf-8", "cp437", "cp850", "latin-1"):
            continue
        decoded = try_decode(raw_bytes, enc)
        # 验证解码结果：不包含控制字符（ASCII < 32，除了换行）
        # Validate result: no control characters (ASCII < 32, except newline)
        if decoded and not any(ord(c) < 32 for c in decoded if c != '\n'):
            return decoded

    # 所有尝试都失败，返回原文件名 | All attempts failed, return original
    return filename


# ==================== ZIP伪加密检测 | ZIP Pseudo-Encryption Detection ====================

def detect_zip_pseudo_encryption(filepath: str) -> dict:
    """检测ZIP文件是否使用伪加密 | Detect if ZIP uses pseudo-encryption.

    ZIP伪加密原理：ZIP文件包含两种头部，本地文件头（LFH）和中央目录头（CDH）。
    真正的加密会在两处都设置加密标志位(bit 0)。伪加密只在其中一处设置标志，
    实际数据并未加密，但解压软件检测到标志后要求输入密码。

    ZIP pseudo-encryption principle: ZIP files contain two types of headers,
    Local File Header (LFH) and Central Directory Header (CDH). Real encryption
    sets encryption flag (bit 0) in both. Pseudo-encryption only sets flag in one,
    actual data is not encrypted, but extraction tools detect flag and ask for password.

    检测方法 | Detection methods:
    1. LFH和CDH加密标志不一致 | LFH and CDH encryption flags mismatch
    2. 有加密标志但数据包含明显的文件头签名
       Encryption flag set but data contains obvious file signatures

    Args:
        filepath: ZIP文件路径 | ZIP file path

    Returns:
        包含检测结果的字典 | Dict with detection results:
        - is_pseudo_encrypted: 是否为伪加密 | Whether pseudo-encrypted
        - details: 详细发现列表 | List of detailed findings
        - entries: 每个条目的详细信息 | Per-entry details
    """
    # ZIP文件签名常量 | ZIP file signature constants
    SIG_LFH = b"\x50\x4b\x03\x04"  # 本地文件头签名 | Local File Header signature
    SIG_CDH = b"\x50\x4b\x01\x02"  # 中央目录头签名 | Central Directory Header signature

    # 初始化结果字典 | Initialize result dict
    result = {
        "is_pseudo_encrypted": False,
        "details": [],
        "entries": [],
    }

    # 打开文件 | Open file
    try:
        f = open(filepath, "rb")
    except (OSError, IOError) as e:
        result["details"].append(f"Cannot read file: {e}")
        return result

    try:
        # 使用mmap避免将整个文件加载到Python堆内存，OS自动管理内存页
        # 对于大文件（几GB），mmap只映射虚拟地址，实际访问时才加载页
        # Use mmap instead of f.read() for memory efficiency; OS manages pages
        # For large files (several GB), mmap only maps virtual addresses,
        # loads pages on actual access
        data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    except ValueError:
        # 空文件无法mmap | Empty file cannot be mmapped
        f.close()
        result["details"].append("File is empty.")
        return result
    except (OSError, IOError) as e:
        f.close()
        result["details"].append(f"Cannot memory-map file: {e}")
        return result

    # ==================== 解析本地文件头 | Parse Local File Headers ====================
    # LFH结构（前30字节） | LFH structure (first 30 bytes):
    # +0:  签名(4字节) | Signature (4 bytes)
    # +4:  最低版本(2字节) | Version needed (2 bytes)
    # +6:  通用标志(2字节) <- 加密标志在bit 0
    #      General purpose flags (2 bytes) <- encryption flag at bit 0
    # +8:  压缩方法(2字节) | Compression method (2 bytes)
    # +10: 修改时间(2字节) | Last mod time (2 bytes)
    # +12: 修改日期(2字节) | Last mod date (2 bytes)
    # +14: CRC-32(4字节) | CRC-32 (4 bytes)
    # +18: 压缩大小(4字节) | Compressed size (4 bytes)
    # +22: 未压缩大小(4字节) | Uncompressed size (4 bytes)
    # +26: 文件名长度(2字节) | Filename length (2 bytes)
    # +28: 扩展字段长度(2字节) | Extra field length (2 bytes)
    # +30: 文件名 | Filename
    # ...: 扩展字段 | Extra field
    # ...: 数据 | Data

    lfh_entries = []
    pos = 0
    while True:
        # 查找下一个LFH签名 | Find next LFH signature
        pos = data.find(SIG_LFH, pos)
        if pos == -1:
            break
        # 确保有足够的数据读取完整头部 | Ensure enough data to read full header
        if pos + 30 > len(data):
            break

        # 提取关键字段 | Extract key fields
        flags = struct.unpack_from("<H", data, pos + 6)[0]  # 通用标志 | General purpose flags
        comp_method = struct.unpack_from("<H", data, pos + 8)[0]  # 压缩方法 | Compression method
        fname_len = struct.unpack_from("<H", data, pos + 26)[0]  # 文件名长度 | Filename length
        extra_len = struct.unpack_from("<H", data, pos + 28)[0]  # 扩展字段长度 | Extra field length
        fname = data[pos + 30:pos + 30 + fname_len]  # 文件名 | Filename

        # 保存条目信息 | Save entry info
        lfh_entries.append({
            "offset": pos,
            "flags": flags,
            "encrypted_flag": bool(flags & 0x01),  # bit 0是加密标志 | bit 0 is encryption flag
            "compression": comp_method,
            "filename": fname,
        })

        # 移动到下一个可能的签名位置 | Move to next possible signature position
        pos += 30 + fname_len + extra_len + 1

    # ==================== 解析中央目录头 | Parse Central Directory Headers ====================
    # CDH结构（前46字节） | CDH structure (first 46 bytes):
    # +0:  签名(4字节) | Signature (4 bytes)
    # +4:  制作版本(2字节) | Version made by (2 bytes)
    # +6:  最低版本(2字节) | Version needed (2 bytes)
    # +8:  通用标志(2字节) <- 加密标志在bit 0
    #      General purpose flags (2 bytes) <- encryption flag at bit 0
    # +10: 压缩方法(2字节) | Compression method (2 bytes)
    # +12: 修改时间(2字节) | Last mod time (2 bytes)
    # +14: 修改日期(2字节) | Last mod date (2 bytes)
    # +16: CRC-32(4字节) | CRC-32 (4 bytes)
    # +20: 压缩大小(4字节) | Compressed size (4 bytes)
    # +24: 未压缩大小(4字节) | Uncompressed size (4 bytes)
    # +28: 文件名长度(2字节) | Filename length (2 bytes)
    # +30: 扩展字段长度(2字节) | Extra field length (2 bytes)
    # +32: 注释长度(2字节) | Comment length (2 bytes)
    # +34: 磁盘号(2字节) | Disk number start (2 bytes)
    # +36: 内部属性(2字节) | Internal attributes (2 bytes)
    # +38: 外部属性(4字节) | External attributes (4 bytes)
    # +42: LFH偏移(4字节) | Relative offset of LFH (4 bytes)
    # +46: 文件名 | Filename
    # ...: 扩展字段 | Extra field
    # ...: 注释 | Comment

    cdh_entries = []
    pos = 0
    while True:
        # 查找下一个CDH签名 | Find next CDH signature
        pos = data.find(SIG_CDH, pos)
        if pos == -1:
            break
        # 确保有足够的数据读取完整头部 | Ensure enough data to read full header
        if pos + 46 > len(data):
            break

        # 提取关键字段 | Extract key fields
        flags = struct.unpack_from("<H", data, pos + 8)[0]  # 通用标志 | General purpose flags
        comp_method = struct.unpack_from("<H", data, pos + 10)[0]  # 压缩方法 | Compression method
        fname_len = struct.unpack_from("<H", data, pos + 28)[0]  # 文件名长度 | Filename length
        extra_len = struct.unpack_from("<H", data, pos + 30)[0]  # 扩展字段长度 | Extra field length
        comment_len = struct.unpack_from("<H", data, pos + 32)[0]  # 注释长度 | Comment length
        fname = data[pos + 46:pos + 46 + fname_len]  # 文件名 | Filename

        # 保存条目信息 | Save entry info
        cdh_entries.append({
            "offset": pos,
            "flags": flags,
            "encrypted_flag": bool(flags & 0x01),  # bit 0是加密标志 | bit 0 is encryption flag
            "compression": comp_method,
            "filename": fname,
        })

        # 移动到下一个可能的签名位置 | Move to next possible signature position
        pos += 46 + fname_len + extra_len + comment_len + 1

    # ==================== 分析加密标志一致性 ====================
    # Analyze Encryption Flag Consistency
    # 统计加密条目数量 | Count encrypted entries
    encrypted_lfh = sum(1 for e in lfh_entries if e["encrypted_flag"])
    encrypted_cdh = sum(1 for e in cdh_entries if e["encrypted_flag"])

    # 检测方法1：LFH和CDH加密标志不一致（最常见的伪加密手法）
    # Detection method 1: LFH and CDH encryption flags mismatch
    # (most common pseudo-encryption technique)
    for i, lfh in enumerate(lfh_entries):
        # 构建条目信息 | Build entry info
        entry_info = {
            "filename": lfh["filename"].decode("utf-8", errors="replace"),
            "lfh_encrypted": lfh["encrypted_flag"],
            "cdh_encrypted": cdh_entries[i]["encrypted_flag"] if i < len(cdh_entries) else None,
            "is_pseudo": False,
        }

        # 比对LFH和CDH的加密标志 | Compare encryption flags between LFH and CDH
        if i < len(cdh_entries):
            cdh = cdh_entries[i]
            # 如果两个标志不一致，判定为伪加密 | If flags mismatch, identified as pseudo-encryption
            if lfh["encrypted_flag"] != cdh["encrypted_flag"]:
                entry_info["is_pseudo"] = True
                result["is_pseudo_encrypted"] = True
                mismatch_msg = (
                    f"Entry '{entry_info['filename']}': "
                    f"LFH encrypted={lfh['encrypted_flag']}, "
                    f"CDH encrypted={cdh['encrypted_flag']} - MISMATCH "
                    f"(伪加密特征 | Pseudo-encryption signature)"
                )
                result["details"].append(mismatch_msg)

        result["entries"].append(entry_info)

    # 检测方法2：标志已设置但数据包含明显的文件头签名（更深层检测）
    # Detection method 2: Flag set but data contains obvious file signatures (deeper detection)
    if encrypted_lfh > 0 and encrypted_cdh > 0:
        # 只检查常见压缩方法（STORED=0, DEFLATE=8）的文件
        # Only check files with common compression methods (STORED=0, DEFLATE=8)
        for i, lfh in enumerate(lfh_entries):
            if lfh["encrypted_flag"] and lfh["compression"] in (0, 8):
                # 计算数据起始偏移 | Calculate data start offset
                # 数据位于：LFH头(30字节) + 文件名 + 扩展字段 之后
                # Data is located after: LFH header(30 bytes) + filename + extra field
                data_offset = lfh["offset"] + 30 + \
                    struct.unpack_from("<H", data, lfh["offset"] + 26)[0] + \
                    struct.unpack_from("<H", data, lfh["offset"] + 28)[0]

                if data_offset < len(data):
                    # 真正加密的ZIP会有12字节的加密头，数据无法识别
                    # Real encrypted ZIP has 12-byte encryption header, data is unrecognizable
                    # STORED（未压缩）的文件更容易检测签名
                    # STORED (uncompressed) files are easier to detect signatures
                    if lfh["compression"] == 0:  # STORED
                        # 读取前4字节检查文件签名 | Read first 4 bytes to check file signature
                        preview = data[data_offset:data_offset + 4]
                        # 常见文件格式的魔数 | Magic numbers of common file formats
                        # PNG: 89 50 4E 47 | JPEG: FF D8 FF | ZIP: 50 4B 03 04
                        # ELF: 7F 45 4C 46 | PDF: 25 50 44 46
                        if preview in (b'\x89PNG', b'\xff\xd8\xff', b'PK\x03\x04',
                                       b'\x7fELF', b'%PDF'):
                            result["is_pseudo_encrypted"] = True
                            fname = lfh['filename'].decode('utf-8', errors='replace')
                            result["details"].append(
                                f"Entry '{fname}': 加密标志已设置但数据包含明显文件头 "
                                f"(识别出文件签名) | Encrypted flag set "
                                f"but data appears unencrypted "
                                f"(recognized file signature)"
                            )

    # 生成总结信息 | Generate summary info
    if not result["details"]:
        if encrypted_lfh > 0 or encrypted_cdh > 0:
            result["details"].append(
                f"Archive has {encrypted_lfh} LFH and {encrypted_cdh} CDH "
                f"encrypted entries. Flags are consistent - likely real encryption."
            )
        else:
            result["details"].append("No encryption flags detected.")

    # 释放mmap和文件句柄 | Release mmap and file handle
    data.close()
    f.close()
    return result


# ==================== ZIP伪加密修复 | ZIP Pseudo-Encryption Patching ====================

def patch_pseudo_encryption(filepath: str, output_path: str) -> bool:
    """从ZIP文件中移除伪加密标志 | Remove fake encryption flags from ZIP file.

    修复流程 | Patching workflow:
    1. 复制原文件到输出路径（保护原文件）| Copy original to output (protect original)
    2. 使用mmap打开副本进行就地二进制修改 | Use mmap to open copy for in-place binary modification
    3. 查找所有LFH和CDH，清除加密标志位(bit 0) | Find all LFH and CDH, clear encryption flag (bit 0)
    4. 修复后的文件可以无需密码直接解压 | Patched file can be extracted without password

    使用mmap的优势 | Advantages of using mmap:
    - 避免将整个文件读入Python堆内存（支持大文件）
      Avoids loading entire file into Python heap (supports large files)
    - OS管理内存页，按需加载 | OS manages memory pages, loads on demand
    - 就地修改，无需重建整个文件 | In-place modification, no need to rebuild entire file

    Args:
        filepath: 原始ZIP文件路径 | Original ZIP file path
        output_path: 输出文件路径（可与原路径相同） | Output file path (can be same as original)

    Returns:
        是否成功修复 | Whether patching succeeded
    """
    # ZIP文件签名常量 | ZIP file signature constants
    SIG_LFH = b"\x50\x4b\x03\x04"  # 本地文件头签名 | Local File Header signature
    SIG_CDH = b"\x50\x4b\x01\x02"  # 中央目录头签名 | Central Directory Header signature

    # 步骤1：复制文件到目标路径 | Step 1: Copy file to output path
    # 如果路径相同则跳过复制 | Skip copy if paths are the same
    try:
        if os.path.realpath(filepath) != os.path.realpath(output_path):
            shutil.copy2(filepath, output_path)
    except (OSError, IOError):
        return False

    # 步骤2：打开副本进行mmap就地修改 | Step 2: Open copy for mmap in-place patching
    # "r+b"模式：读写二进制 | "r+b" mode: read-write binary
    try:
        f = open(output_path, "r+b")
    except (OSError, IOError):
        return False

    # 步骤3：创建内存映射 | Step 3: Create memory map
    try:
        data = mmap.mmap(f.fileno(), 0)
    except (ValueError, OSError):
        f.close()
        # 清理失败的副本 | Clean up failed copy
        if os.path.realpath(filepath) != os.path.realpath(output_path):
            try:
                os.unlink(output_path)
            except OSError:
                pass
        return False

    # 步骤4：修补所有LFH和CDH的加密标志 | Step 4: Patch encryption flags in all LFH and CDH
    patched = 0

    # 修补本地文件头条目（标志位于偏移+6） | Patch LFH entries (flag at offset +6)
    # LFH结构：签名(4) + 版本(2) + 标志(2) <- 偏移6
    # LFH structure: sig(4) + ver(2) + flags(2) <- offset 6
    pos = 0
    while True:
        pos = data.find(SIG_LFH, pos)
        if pos == -1:
            break
        # 读取当前标志 | Read current flags
        flags = struct.unpack_from("<H", data, pos + 6)[0]
        # 如果加密标志位(bit 0)已设置 | If encryption flag (bit 0) is set
        if flags & 0x01:
            # 清除bit 0：flags & 0xFFFE (二进制: 1111 1111 1111 1110)
            # Clear bit 0: flags & 0xFFFE (binary: 1111 1111 1111 1110)
            struct.pack_into("<H", data, pos + 6, flags & 0xFFFE)
            patched += 1
        pos += 4

    # 修补中央目录头条目（标志位于偏移+8） | Patch CDH entries (flag at offset +8)
    # CDH结构：签名(4) + 制作版本(2) + 最低版本(2) + 标志(2) <- 偏移8
    # CDH structure: sig(4) + ver_made(2) + ver_need(2) + flags(2) <- offset 8
    pos = 0
    while True:
        pos = data.find(SIG_CDH, pos)
        if pos == -1:
            break
        # 读取当前标志 | Read current flags
        flags = struct.unpack_from("<H", data, pos + 8)[0]
        # 如果加密标志位(bit 0)已设置 | If encryption flag (bit 0) is set
        if flags & 0x01:
            # 清除bit 0 | Clear bit 0
            struct.pack_into("<H", data, pos + 8, flags & 0xFFFE)
            patched += 1
        pos += 4

    # 步骤5：释放资源 | Step 5: Release resources
    # mmap会将修改同步到磁盘 | mmap will sync changes to disk
    data.close()
    f.close()

    # 步骤6：检查是否有实际修改 | Step 6: Check if any actual changes
    if patched == 0:
        # 无需修补（无加密标志），删除副本 | Nothing to patch (no encryption flags), remove copy
        if os.path.realpath(filepath) != os.path.realpath(output_path):
            try:
                os.unlink(output_path)
            except OSError:
                pass
        return False
    return True
