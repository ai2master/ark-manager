"""使用7z命令进行归档操作的后端 | Backend for archive operations using the 7z command.

该模块封装p7zip-full提供的7z命令行工具，通过子进程调用实现所有压缩包操作。
支持20+种格式（7z/ZIP/RAR/TAR/GZ/BZ2/XZ等），提供编码自动检测、密码保护、
分卷压缩、固实压缩等高级功能。所有操作均通过subprocess执行，确保安全隔离。

This module wraps the 7z CLI tool from p7zip-full via subprocess calls for all
archive operations. Supports 20+ formats (7z/ZIP/RAR/TAR/GZ/BZ2/XZ etc.) with
advanced features like auto-encoding detection, password protection, volume splitting,
and solid compression. All operations run via subprocess for security isolation.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .encoding_utils import (
    auto_detect_zip_filename,
    fix_zip_filename,
)

# ==================== 数据类定义 | Data Class Definitions ====================


@dataclass
class ArchiveEntry:
    """表示归档文件中的单个条目 | Represents a single entry in an archive.

    保存压缩包内每个文件或目录的详细信息，包括大小、时间戳、CRC校验值、
    加密状态等。支持编码修复前后的文件名对比。

    Stores detailed information for each file or directory in the archive,
    including size, timestamp, CRC checksum, encryption status, etc.
    Supports filename comparison before/after encoding fix.

    Attributes:
        filename: 修复后的文件名（用户可见） | Fixed filename (user-visible)
        original_filename: 编码修复前的原始文件名 | Raw filename before encoding fix
        size: 原始文件大小（字节） | Uncompressed size in bytes
        compressed_size: 压缩后大小（字节） | Compressed size in bytes
        modified: 修改时间戳字符串 | Modification timestamp string
        attributes: 文件属性字符串（如"D"表示目录）
                   | File attributes string (e.g., "D" for directory)
        crc: CRC32校验值（十六进制） | CRC32 checksum (hexadecimal)
        encrypted: 是否加密 | Whether the entry is encrypted
        method: 压缩方法（如"LZMA"、"Deflate"） | Compression method (e.g., "LZMA", "Deflate")
        is_dir: 是否为目录 | Whether this is a directory
    """
    filename: str
    original_filename: str
    size: int = 0
    compressed_size: int = 0
    modified: str = ""
    attributes: str = ""
    crc: str = ""
    encrypted: bool = False
    method: str = ""
    is_dir: bool = False


@dataclass
class ArchiveInfo:
    """归档文件的信息 | Information about an archive.

    保存压缩包整体的元数据，包括格式类型、压缩方法、物理大小、
    加密状态、注释等，以及包含的所有文件条目列表。

    Stores archive-level metadata including format type, compression method,
    physical size, encryption status, comments, and the list of all file entries.

    Attributes:
        path: 压缩包文件路径 | Archive file path
        type: 压缩包类型（如"7z"、"zip"） | Archive type (e.g., "7z", "zip")
        method: 压缩方法（如"LZMA2"） | Compression method (e.g., "LZMA2")
        solid: 是否为固实压缩（7z特性） | Whether solid compression is used (7z feature)
        blocks: 固实块数量（7z特性） | Number of solid blocks (7z feature)
        physical_size: 压缩包物理大小（字节） | Physical archive size in bytes
        headers_size: 文件头大小（字节） | Headers size in bytes
        comment: 压缩包注释（ZIP支持） | Archive comment (ZIP supports this)
        encrypted: 是否整体加密 | Whether the archive is encrypted
        entries: 包含的文件条目列表 | List of file entries contained
        error: 错误信息（如果操作失败） | Error message (if operation failed)
    """
    path: str
    type: str = ""
    method: str = ""
    solid: str = ""
    blocks: int = 0
    physical_size: int = 0
    headers_size: int = 0
    comment: str = ""
    encrypted: bool = False
    entries: List[ArchiveEntry] = field(default_factory=list)
    error: str = ""


# ==================== 7z命令行封装类 | 7z CLI Wrapper Class ====================

class ArchiveBackend:
    """调用7z CLI进行归档操作的后端 | Backend that calls 7z CLI for archive operations.

    通过subprocess调用p7zip-full提供的7z命令行工具执行所有压缩包操作。
    支持列表、提取、压缩、测试等功能，处理密码、编码、多格式等复杂场景。
    所有命令执行都有超时保护，避免长时操作阻塞UI。

    Executes all archive operations via subprocess calls to the 7z CLI tool
    from p7zip-full. Supports listing, extraction, compression, testing with
    password, encoding, multi-format handling. All commands have timeout protection
    to avoid blocking UI with long operations.

    Attributes:
        seven_zip_path: 7z可执行文件路径 | Path to 7z executable
        SUPPORTED_FORMATS: 支持的压缩格式列表 | List of supported archive formats
    """

    # 支持的压缩格式列表（按常用程度排序） | Supported formats (sorted by popularity)
    SUPPORTED_FORMATS = [
        "7z", "zip", "tar", "gz", "bz2", "xz", "rar", "cab", "iso",
        "wim", "arj", "cpio", "rpm", "deb", "lzh", "lzma", "z",
        "tar.gz", "tar.bz2", "tar.xz", "tgz", "tbz2", "txz",
        "zst", "tar.zst",
    ]

    def __init__(self, seven_zip_path: str = "7z"):
        """初始化后端，验证7z可用性 | Initialize backend and verify 7z availability.

        Args:
            seven_zip_path: 7z可执行文件路径或命令名 | Path to 7z executable or command name

        Raises:
            RuntimeError: 如果找不到7z命令 | If 7z command is not found
        """
        # 验证路径合法性，防止注入任意命令 | Validate path to prevent arbitrary command injection
        # 使用shutil.which()在PATH中查找可执行文件
        # Use shutil.which() to locate executable in PATH
        resolved = shutil.which(seven_zip_path)
        self.seven_zip_path = resolved if resolved else seven_zip_path
        self._verify_7z()

    # ==================== 内部辅助方法 | Internal Helper Methods ====================

    def _verify_7z(self):
        """验证7z是否可用 | Verify 7z is available.

        运行7z命令检查是否已安装。如果未找到，抛出友好的错误提示，
        包含各主流Linux发行版的安装命令。

        Runs 7z command to check if installed. If not found, raises a friendly
        error message with installation commands for major Linux distributions.

        Raises:
            RuntimeError: 如果7z命令不存在 | If 7z command does not exist
        """
        try:
            subprocess.run(
                [self.seven_zip_path],
                capture_output=True, timeout=10
            )
        except FileNotFoundError:
            raise RuntimeError(
                "7z command not found. Please install p7zip-full:\n"
                "  Ubuntu/Debian: sudo apt install p7zip-full\n"
                "  Fedora: sudo dnf install p7zip p7zip-plugins\n"
                "  Arch: sudo pacman -S p7zip"
            )
        except subprocess.TimeoutExpired:
            # 命令存在但超时，视为可用 | Command exists but timed out, consider available
            pass

    def _run_7z(self, args: List[str], password: Optional[str] = None,
                encoding: str = "utf-8", timeout: int = 300) -> subprocess.CompletedProcess:
        """使用给定参数运行7z | Run 7z with given arguments.

        所有7z命令的统一执行入口，负责构建命令行、处理密码、设置环境变量、
        执行子进程、超时控制等。强制UTF-8输出避免乱码。

        Unified execution entry for all 7z commands. Handles command building,
        password processing, environment setup, subprocess execution, timeout control.
        Forces UTF-8 output to avoid garbled text.

        Args:
            args: 7z命令参数列表（如["l", "-slt", "file.zip"]） | 7z command arguments
            password: 可选密码，将添加-p参数 | Optional password, will add -p flag
            encoding: 保留参数，暂未使用 | Reserved parameter, currently unused
            timeout: 超时时间（秒），默认300秒 | Timeout in seconds, default 300s

        Returns:
            subprocess.CompletedProcess: 命令执行结果 | Command execution result

        Raises:
            RuntimeError: 如果命令超时 | If command times out
        """
        # 构建完整的命令行 | Build complete command line
        cmd = [self.seven_zip_path] + args

        # 添加密码参数（如果提供） | Add password argument (if provided)
        if password is not None:
            # 已知安全限制: 密码通过命令行传递，进程运行期间可通过 /proc/PID/cmdline 查看
            # 7z CLI 不支持 stdin 或环境变量传递密码，这是 7z 的设计限制
            # Known security limitation: password passed via CLI, visible in
            # /proc/PID/cmdline during process execution. 7z CLI does not support
            # stdin or env var for passwords by design.
            cmd.append(f"-p{password}")

        # 复制当前环境变量 | Copy current environment variables
        env = os.environ.copy()
        # 强制7z输出使用UTF-8区域设置，避免中文乱码
        # Force UTF-8 locale for 7z output to avoid Chinese garbled text
        env["LANG"] = "en_US.UTF-8"
        env["LC_ALL"] = "en_US.UTF-8"

        try:
            # 执行子进程，捕获标准输出和错误输出 | Execute subprocess, capture stdout and stderr
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                env=env,
            )
            return result
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"7z command timed out after {timeout}s")

    # ==================== 公共API方法 | Public API Methods ====================

    def list_archive(self, filepath: str, password: Optional[str] = None,
                     encoding_mode: str = "auto",
                     forced_encoding: str = "gbk") -> ArchiveInfo:
        """列出归档文件内容并支持编码处理 | List contents of an archive with encoding support.

        使用7z的-slt（技术列表）选项获取压缩包详细信息，包括每个文件的大小、
        时间戳、CRC、加密状态等。支持三种编码处理模式：自动检测、强制指定、不处理。
        对于ZIP文件还会提取归档注释。

        Uses 7z's -slt (technical list) option to get detailed archive information
        including file size, timestamp, CRC, encryption status for each entry.
        Supports three encoding modes: auto-detect, force, or none.
        Also extracts archive comments for ZIP files.

        Args:
            filepath: 归档文件路径 | Path to the archive file
            password: 加密归档文件的可选密码 | Optional password for encrypted archives
            encoding_mode: 编码处理模式："auto"（自动检测）、"force"（强制指定）
                          或"none"（不处理） | Encoding handling mode: "auto"
                          (detect), "force" (specify), or "none" (skip)
            forced_encoding: mode为"force"时使用的编码（如"gbk"）
                            | Encoding when mode is "force" (e.g., "gbk")

        Returns:
            ArchiveInfo: 包含压缩包元数据和文件列表 | Archive metadata and file list
        """
        info = ArchiveInfo(path=filepath)

        # 构建7z列表命令：l=列表，-slt=技术详细模式
        # Build 7z list command: l=list, -slt=technical detail mode
        args = ["l", "-slt", filepath]
        result = self._run_7z(args, password=password)

        stdout = result.stdout
        # 尝试按优先级解码输出：UTF-8 > GBK > UTF-8容错
        # Try decoding output by priority: UTF-8 > GBK > UTF-8 fallback
        try:
            output = stdout.decode("utf-8")
        except UnicodeDecodeError:
            try:
                output = stdout.decode("gbk")
            except UnicodeDecodeError:
                output = stdout.decode("utf-8", errors="replace")

        # 检查命令是否执行成功 | Check if command succeeded
        if result.returncode != 0:
            stderr_text = result.stderr.decode("utf-8", errors="replace")
            # 根据错误类型设置友好的错误信息 | Set friendly error messages based on error type
            if "Wrong password" in stderr_text or "wrong password" in output.lower():
                info.error = "Wrong password or encrypted archive"
            elif "Cannot open" in stderr_text:
                info.error = f"Cannot open archive: {filepath}"
            else:
                info.error = stderr_text or output
            return info

        # 解析7z输出为结构化数据 | Parse 7z output into structured data
        info = self._parse_list_output(output, filepath, encoding_mode, forced_encoding)

        # ZIP格式特殊处理：提取归档注释 | Special handling for ZIP: extract archive comment
        if filepath.lower().endswith(".zip"):
            comment = self._get_zip_comment(filepath)
            if comment:
                info.comment = comment

        return info

    def _parse_list_output(self, output: str, filepath: str,
                           encoding_mode: str, forced_encoding: str) -> ArchiveInfo:
        """将7z l -slt输出解析为ArchiveInfo | Parse 7z l -slt output into ArchiveInfo.

        解析7z技术列表模式（-slt）的输出文本，提取压缩包级别的属性（类型、大小、
        方法等）和每个文件条目的详细信息。根据encoding_mode处理文件名编码问题。

        Parses 7z technical list mode (-slt) output text to extract archive-level
        properties (type, size, method, etc.) and detailed info for each file entry.
        Handles filename encoding issues based on encoding_mode.

        Args:
            output: 7z命令的标准输出文本 | stdout text from 7z command
            filepath: 压缩包文件路径 | Archive file path
            encoding_mode: 编码处理模式 | Encoding handling mode
            forced_encoding: 强制使用的编码 | Forced encoding to use

        Returns:
            ArchiveInfo: 解析后的压缩包信息 | Parsed archive information
        """
        info = ArchiveInfo(path=filepath)
        current_entry = None

        # 逐行解析输出 | Parse output line by line
        for line in output.split("\n"):
            line = line.strip()

            # ==================== 解析归档级属性
            # Parse Archive-Level Properties ====================
            # 这些属性描述整个压缩包 | These properties describe the entire archive
            if line.startswith("Type = "):
                info.type = line[7:]
            elif line.startswith("Physical Size = "):
                try:
                    info.physical_size = int(line[16:])
                except ValueError:
                    pass
            elif line.startswith("Method = "):
                info.method = line[9:]
            elif line.startswith("Solid = "):
                info.solid = line[8:]
            elif line.startswith("Blocks = "):
                try:
                    info.blocks = int(line[9:])
                except ValueError:
                    pass
            elif line.startswith("Headers Size = "):
                try:
                    info.headers_size = int(line[15:])
                except ValueError:
                    pass
            elif line.startswith("Comment = "):
                info.comment = line[10:]
            elif line.startswith("Encrypted = +"):
                info.encrypted = True

            # ==================== 解析条目级属性
            # Parse Entry-Level Properties ====================
            # 这些属性描述压缩包内的单个文件或目录
            # These properties describe individual files or directories
            elif line.startswith("Path = "):
                # 新条目开始，保存上一个条目 | New entry starts, save previous entry
                if current_entry:
                    info.entries.append(current_entry)
                # 提取并修复文件名编码 | Extract and fix filename encoding
                raw_name = line[7:]
                fixed_name = self._fix_filename(raw_name, encoding_mode, forced_encoding)
                current_entry = ArchiveEntry(
                    filename=fixed_name,
                    original_filename=raw_name,
                )
            elif current_entry:
                # 解析当前条目的其他属性 | Parse other properties of current entry
                if line.startswith("Size = "):
                    try:
                        current_entry.size = int(line[7:])
                    except ValueError:
                        pass
                elif line.startswith("Packed Size = "):
                    try:
                        current_entry.compressed_size = int(line[14:])
                    except ValueError:
                        pass
                elif line.startswith("Modified = "):
                    current_entry.modified = line[11:]
                elif line.startswith("Attributes = "):
                    attr = line[13:]
                    current_entry.attributes = attr
                    # "D"标志表示目录 | "D" flag indicates directory
                    current_entry.is_dir = "D" in attr
                elif line.startswith("CRC = "):
                    current_entry.crc = line[6:]
                elif line.startswith("Encrypted = "):
                    # "+"表示加密，"-"表示未加密
                    # "+" means encrypted, "-" means not encrypted
                    current_entry.encrypted = line[12:] == "+"
                elif line.startswith("Method = "):
                    current_entry.method = line[9:]

        # 保存最后一个条目 | Save last entry
        if current_entry:
            info.entries.append(current_entry)

        return info

    def _fix_filename(self, filename: str, encoding_mode: str,
                      forced_encoding: str) -> str:
        """根据模式修复文件名编码 | Fix filename encoding based on mode.

        处理压缩包中非UTF-8编码的文件名（如GBK、Big5等）。7z通常将文件名
        误解为CP437编码，需要重新编码才能正确显示中文。

        Handles non-UTF-8 encoded filenames in archives (e.g., GBK, Big5).
        7z typically misinterprets filenames as CP437 encoding, requiring
        re-encoding to display Chinese correctly.

        Args:
            filename: 原始文件名 | Original filename
            encoding_mode: "none"（不处理）、"force"（强制）、"auto"（自动检测）
                          | "none" (skip), "force" (force), "auto" (detect)
            forced_encoding: mode为"force"时的目标编码 | Target encoding when mode is "force"

        Returns:
            修复后的文件名 | Fixed filename
        """
        if encoding_mode == "none":
            return filename
        elif encoding_mode == "force":
            # 强制模式：假设原始为CP437，转换为指定编码
            # Force mode: assume CP437, convert to specified encoding
            return fix_zip_filename(filename, "cp437", forced_encoding)
        else:  # auto
            # 自动模式：使用chardet检测编码 | Auto mode: use chardet to detect encoding
            return auto_detect_zip_filename(filename)

    def _get_zip_comment(self, filepath: str) -> str:
        """提取ZIP归档注释 | Extract ZIP archive comment.

        ZIP格式支持在文件末尾添加注释（最多65535字节）。该方法使用Python的
        zipfile模块读取注释，并尝试多种编码解码。

        ZIP format supports adding comments at file end (up to 65535 bytes).
        This method uses Python's zipfile module to read comments and tries
        multiple encodings for decoding.

        Args:
            filepath: ZIP文件路径 | ZIP file path

        Returns:
            解码后的注释文本，失败返回空字符串 | Decoded comment text, empty string on failure
        """
        try:
            import zipfile
            with zipfile.ZipFile(filepath, "r") as zf:
                if zf.comment:
                    # 按优先级尝试多种编码 | Try multiple encodings by priority
                    # UTF-8（国际标准） -> GBK（中文简体） -> GB18030（中文完整）
                    # -> Latin-1（容错）
                    # UTF-8 (international) -> GBK (Simplified Chinese) ->
                    # GB18030 (Chinese full) -> Latin-1 (fallback)
                    for enc in ("utf-8", "gbk", "gb18030", "latin-1"):
                        try:
                            return zf.comment.decode(enc)
                        except (UnicodeDecodeError, LookupError):
                            continue
                    # 所有编码都失败，使用UTF-8容错模式
                    # All encodings failed, use UTF-8 with error handling
                    return zf.comment.decode("utf-8", errors="replace")
        except Exception:
            # 文件损坏或不是有效ZIP | File corrupted or not a valid ZIP
            pass
        return ""

    def extract(self, filepath: str, output_dir: str,
                password: Optional[str] = None,
                entries: Optional[List[str]] = None,
                create_parent_dir: bool = False,
                encoding_mode: str = "auto",
                forced_encoding: str = "gbk",
                overwrite: bool = True,
                progress_callback: Optional[Callable[[str, int], None]] = None) -> tuple:
        """提取归档文件到输出目录 | Extract archive to output_dir.

        使用7z的x命令提取压缩包内容。支持部分提取（指定文件列表）、
        密码保护、编码修复、覆盖控制。提取后会根据encoding_mode重命名乱码文件。

        Uses 7z's x command to extract archive contents. Supports partial extraction
        (specified file list), password protection, encoding fix, overwrite control.
        After extraction, renames garbled filenames based on encoding_mode.

        Args:
            filepath: 归档文件路径 | Archive path
            output_dir: 目标目录 | Destination directory
            password: 可选密码 | Optional password
            entries: 要提取的特定条目列表（相对路径）
                    | Optional list of entries to extract (relative paths)
            create_parent_dir: 是否创建以压缩包命名的父文件夹
                              | Whether to create parent folder named after archive
            encoding_mode: 编码处理模式："auto"、"force"或"none"
                          | Encoding mode: "auto", "force", or "none"
            forced_encoding: mode为"force"时的编码 | Encoding when mode is "force"
            overwrite: 是否覆盖现有文件 | Whether to overwrite existing files
            progress_callback: 进度回调函数(文件名, 百分比) | Progress callback(filename, percent)

        Returns:
            (成功: bool, 消息: str) | (success: bool, message: str)
        """
        # 如果需要，创建父目录 | Create parent directory if needed
        if create_parent_dir:
            # 从文件名提取基础名（去除扩展名） | Extract base name from filename (remove extension)
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            # 处理双扩展名，如.tar.gz | Handle double extensions like .tar.gz
            if base_name.endswith(".tar"):
                base_name = base_name[:-4]
            output_dir = os.path.join(output_dir, base_name)
            os.makedirs(output_dir, exist_ok=True)

        # 构建7z提取命令 | Build 7z extract command
        # x: 保持目录结构的提取 | x: extract with full paths
        # -o: 指定输出目录（无空格） | -o: specify output directory (no space)
        args = ["x", filepath, f"-o{output_dir}"]

        # 设置覆盖模式 | Set overwrite mode
        if overwrite:
            args.append("-aoa")  # 覆盖所有文件 | Overwrite all files
        else:
            args.append("-aos")  # 跳过已存在的文件 | Skip existing files

        # 如果指定了要提取的条目，添加到命令行 | If specific entries specified, add to command line
        if entries:
            args.extend(entries)

        # 执行提取命令，超时设置为1小时 | Execute extract command with 1-hour timeout
        result = self._run_7z(args, password=password, timeout=3600)

        # 尝试解码输出 | Try to decode output
        try:
            output = result.stdout.decode("utf-8", errors="replace")
        except Exception:
            output = ""

        # 检查提取是否成功 | Check if extraction succeeded
        if result.returncode == 0:
            # 如果需要编码修复，重命名提取的文件
            # If encoding fix needed, rename extracted files
            # 7z提取时会保留原始文件名，需要后处理修复乱码
            # 7z preserves original filenames during extraction, need
            # post-processing to fix garbled names
            if encoding_mode != "none":
                self._fix_extracted_filenames(
                    output_dir, encoding_mode, forced_encoding
                )
            return True, f"Extracted to: {output_dir}"
        else:
            stderr = result.stderr.decode("utf-8", errors="replace")
            return False, stderr or output

    def _fix_extracted_filenames(self, directory: str, encoding_mode: str,
                                 forced_encoding: str):
        """提取后重命名乱码文件名 | Rename files with garbled names after extraction.

        递归遍历提取目录，检测并修复所有乱码文件名。使用topdown=False确保
        先处理子文件，再处理父目录，避免重命名目录后路径失效。

        Recursively traverses extraction directory to detect and fix all garbled filenames.
        Uses topdown=False to process child files before parent directories, avoiding
        path invalidation after directory renaming.

        Args:
            directory: 提取目录路径 | Extraction directory path
            encoding_mode: 编码处理模式 | Encoding handling mode
            forced_encoding: 强制使用的编码 | Forced encoding to use

        Security:
            防止路径遍历攻击：验证修复后的路径仍在目标目录内
            Prevents path traversal attacks: validates fixed paths stay within
            target directory
        """
        # 获取目标目录的真实路径用于路径遍历校验
        # Get real path for traversal validation
        # realpath()解析符号链接，避免绕过安全检查
        # realpath() resolves symlinks to avoid bypassing security checks
        real_dir = os.path.realpath(directory)

        # topdown=False: 自底向上遍历，先处理文件再处理目录
        # topdown=False: traverse bottom-up, process files before directories
        for root, dirs, files in os.walk(directory, topdown=False):
            # 处理所有文件和目录 | Process all files and directories
            for name in files + dirs:
                # 尝试修复文件名编码 | Try to fix filename encoding
                fixed = self._fix_filename(name, encoding_mode, forced_encoding)
                if fixed != name:
                    old_path = os.path.join(root, name)
                    new_path = os.path.join(root, fixed)
                    # 安全检查：防止路径遍历攻击 | Security check: prevent path traversal attack
                    # 确保新路径仍在目标目录内，防止"../"等恶意路径
                    # Ensure new path stays within target dir, preventing malicious paths like "../"
                    if not os.path.realpath(new_path).startswith(real_dir + os.sep):
                        continue
                    # 避免覆盖已存在的文件 | Avoid overwriting existing files
                    if not os.path.exists(new_path):
                        try:
                            os.rename(old_path, new_path)
                        except OSError:
                            # 重命名失败（如跨文件系统），忽略
                            # Rename failed (e.g., cross-filesystem), ignore
                            pass

    def compress(self, output_path: str, input_paths: List[str],
                 format: str = "7z",
                 compression_level: int = 5,
                 password: Optional[str] = None,
                 encrypt_filenames: bool = False,
                 solid: bool = True,
                 method: str = "",
                 volumes: str = "",
                 encoding_mode: str = "auto",
                 forced_encoding: str = "gbk",
                 progress_callback: Optional[Callable[[str, int], None]] = None) -> tuple:
        """创建新的归档文件 | Create a new archive.

        使用7z的a命令创建压缩包。支持多种格式、压缩级别、加密选项、固实压缩、
        分卷压缩等高级功能。对于ZIP格式会特殊处理中文文件名编码。

        Uses 7z's a command to create archives. Supports multiple formats, compression
        levels, encryption options, solid compression, volume splitting and other advanced
        features. Special handling for Chinese filename encoding in ZIP format.

        Args:
            output_path: 输出压缩包路径 | Output archive path
            input_paths: 要压缩的文件/目录路径列表 | List of file/directory paths to compress
            format: 压缩格式（如"7z"、"zip"、"tar"） | Archive format (e.g., "7z", "zip", "tar")
            compression_level: 压缩级别0-9，0=不压缩，9=最大压缩
                              | Compression level 0-9, 0=store, 9=ultra
            password: 可选密码保护 | Optional password protection
            encrypt_filenames: 是否加密文件名（仅7z支持） | Whether to encrypt filenames (7z only)
            solid: 是否启用固实压缩（7z特性，提高压缩率）
                  | Whether to enable solid compression (7z feature, improves ratio)
            method: 压缩方法（如"LZMA2"、"Deflate"） | Compression method (e.g., "LZMA2", "Deflate")
            volumes: 分卷大小（如"100m"、"4g"） | Volume size (e.g., "100m", "4g")
            encoding_mode: 编码处理模式（仅ZIP） | Encoding mode (ZIP only)
            forced_encoding: 强制编码（仅ZIP） | Forced encoding (ZIP only)
            progress_callback: 进度回调函数 | Progress callback function

        Returns:
            (成功: bool, 消息: str) | (success: bool, message: str)
        """
        # 构建7z压缩命令 | Build 7z compression command
        # a: 添加文件到压缩包 | a: add files to archive
        args = ["a", output_path]

        # 指定压缩格式 | Specify archive format
        args.append(f"-t{format}")

        # 设置压缩级别(0-9) | Set compression level (0-9)
        # 0=仅存储，1=最快，5=正常，9=最大压缩 | 0=store, 1=fastest, 5=normal, 9=ultra
        args.append(f"-mx={compression_level}")

        # 指定压缩方法 | Specify compression method
        if method:
            args.append(f"-m0={method}")

        # 固实模式(仅7z格式支持) | Solid mode (7z format only)
        # 固实压缩将所有文件视为一个数据流，压缩率更高但不能单独提取
        # Solid compression treats all files as one data stream, better ratio
        # but can't extract individually
        if format == "7z":
            args.append(f"-ms={'on' if solid else 'off'}")

        # 加密文件名(仅7z格式支持) | Encrypt filenames (7z format only)
        # 启用后连文件名都加密，需要密码才能查看列表
        # When enabled, even filenames are encrypted, password required to view list
        if encrypt_filenames and password and format == "7z":
            args.append("-mhe=on")

        # 分卷压缩 | Volume splitting
        # 将大压缩包分割成多个小文件，方便传输
        # Split large archive into multiple small files for easier transfer
        if volumes:
            args.append(f"-v{volumes}")

        # ZIP格式的编码处理 | Encoding handling for ZIP format
        # ZIP标准使用CP437编码，但国内软件常用GBK，需要特殊处理
        # ZIP standard uses CP437, but Chinese software often uses GBK, needs special handling
        if format == "zip":
            if encoding_mode == "force" and forced_encoding.lower() in ("gbk", "gb2312", "gb18030"):
                # 使用GBK代码页(CP936)存储文件名 | Use GBK codepage (CP936) for filenames
                args.append("-mcp=936")  # CP936 = GBK
            else:
                # 强制使用UTF-8编码文件名（推荐） | Force UTF-8 for filenames (recommended)
                args.append("-mcu=on")

        # 添加要压缩的文件列表 | Add list of files to compress
        args.extend(input_paths)

        # 执行压缩命令，超时设置为1小时 | Execute compression command with 1-hour timeout
        result = self._run_7z(args, password=password, timeout=3600)

        # 尝试解码输出 | Try to decode output
        try:
            output = result.stdout.decode("utf-8", errors="replace")
        except Exception:
            output = ""

        # 检查压缩是否成功 | Check if compression succeeded
        if result.returncode == 0:
            return True, f"Archive created: {output_path}"
        else:
            stderr = result.stderr.decode("utf-8", errors="replace")
            return False, stderr or output

    def test_archive(self, filepath: str, password: Optional[str] = None) -> tuple:
        """测试归档文件完整性 | Test archive integrity.

        使用7z的t命令验证压缩包是否损坏。会解压所有数据到内存进行CRC校验，
        但不写入磁盘。用于检测下载损坏、传输错误、存储介质问题等。

        Uses 7z's t command to verify if archive is corrupted. Decompresses all data
        to memory for CRC checking but doesn't write to disk. Useful for detecting
        download corruption, transfer errors, storage media issues, etc.

        Args:
            filepath: 压缩包文件路径 | Archive file path
            password: 可选密码（加密压缩包需要）
                     | Optional password (required for encrypted archives)

        Returns:
            (成功: bool, 消息: str) | (success: bool, message: str)
        """
        # 构建7z测试命令 | Build 7z test command
        # t: 测试压缩包完整性 | t: test archive integrity
        args = ["t", filepath]
        result = self._run_7z(args, password=password)

        # 尝试解码输出 | Try to decode output
        try:
            output = result.stdout.decode("utf-8", errors="replace")
        except Exception:
            output = ""

        # 检查测试是否通过 | Check if test passed
        if result.returncode == 0:
            return True, "Archive test passed: OK"
        else:
            stderr = result.stderr.decode("utf-8", errors="replace")
            return False, stderr or output

    # ==================== 静态辅助方法 | Static Helper Methods ====================

    @staticmethod
    def get_supported_extensions() -> List[str]:
        """获取可处理的文件扩展名列表 | Get list of file extensions we can handle.

        返回所有支持的压缩包文件扩展名，用于文件类型过滤和拖放支持。
        包括单扩展名（如.zip）和双扩展名（如.tar.gz）。

        Returns list of all supported archive file extensions for file type
        filtering and drag-drop support. Includes single extensions (e.g., .zip)
        and double extensions (e.g., .tar.gz).

        Returns:
            扩展名列表（小写，带点） | List of extensions (lowercase, with dot)
        """
        return [
            ".7z", ".zip", ".rar", ".tar", ".gz", ".bz2", ".xz",
            ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz",
            ".cab", ".iso", ".wim", ".arj", ".cpio", ".rpm", ".deb",
            ".lzh", ".lzma", ".z", ".zst", ".tar.zst",
        ]
