"""使用7z命令进行归档操作的后端 | Backend for archive operations using the 7z command."""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .encoding_utils import (
    auto_detect_zip_filename,
    fix_zip_filename,
)


@dataclass
class ArchiveEntry:
    """表示归档文件中的单个条目 | Represents a single entry in an archive."""
    filename: str
    original_filename: str  # 编码修复前的原始文件名 | Raw filename before encoding fix
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
    """归档文件的信息 | Information about an archive."""
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


class ArchiveBackend:
    """调用7z CLI进行归档操作的后端 | Backend that calls 7z CLI for archive operations."""

    SUPPORTED_FORMATS = [
        "7z", "zip", "tar", "gz", "bz2", "xz", "rar", "cab", "iso",
        "wim", "arj", "cpio", "rpm", "deb", "lzh", "lzma", "z",
        "tar.gz", "tar.bz2", "tar.xz", "tgz", "tbz2", "txz",
        "zst", "tar.zst",
    ]

    def __init__(self, seven_zip_path: str = "7z"):
        # 验证路径合法性，防止注入任意命令 | Validate path to prevent arbitrary command injection
        resolved = shutil.which(seven_zip_path)
        self.seven_zip_path = resolved if resolved else seven_zip_path
        self._verify_7z()

    def _verify_7z(self):
        """验证7z是否可用 | Verify 7z is available."""
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
            pass

    def _run_7z(self, args: List[str], password: Optional[str] = None,
                encoding: str = "utf-8", timeout: int = 300) -> subprocess.CompletedProcess:
        """使用给定参数运行7z | Run 7z with given arguments."""
        cmd = [self.seven_zip_path] + args

        if password is not None:
            # 已知限制: 密码通过命令行传递，进程运行期间可通过 /proc/PID/cmdline 查看
            # 7z CLI 不支持 stdin 或环境变量传递密码，这是 7z 的设计限制
            # Known limitation: password passed via CLI, visible in /proc/PID/cmdline.
            # 7z CLI does not support stdin or env var for passwords by design.
            cmd.append(f"-p{password}")

        env = os.environ.copy()
        # 强制7z输出使用UTF-8区域设置 | Force UTF-8 locale for 7z output
        env["LANG"] = "en_US.UTF-8"
        env["LC_ALL"] = "en_US.UTF-8"

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                env=env,
            )
            return result
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"7z command timed out after {timeout}s")

    def list_archive(self, filepath: str, password: Optional[str] = None,
                     encoding_mode: str = "auto",
                     forced_encoding: str = "gbk") -> ArchiveInfo:
        """列出归档文件内容并支持编码处理 | List contents of an archive with encoding support.

        Args:
            filepath: 归档文件路径 | Path to the archive.
            password: 加密归档文件的可选密码 | Optional password for encrypted archives.
            encoding_mode: "auto"、"force"或"none" | "auto", "force", or "none".
            forced_encoding: 强制编码 | Encoding when mode is "force".
        """
        info = ArchiveInfo(path=filepath)

        # 获取技术列表 | Get technical listing
        args = ["l", "-slt", filepath]
        result = self._run_7z(args, password=password)

        stdout = result.stdout
        # 尝试解码输出 | Try decoding output
        try:
            output = stdout.decode("utf-8")
        except UnicodeDecodeError:
            try:
                output = stdout.decode("gbk")
            except UnicodeDecodeError:
                output = stdout.decode("utf-8", errors="replace")

        if result.returncode != 0:
            stderr_text = result.stderr.decode("utf-8", errors="replace")
            if "Wrong password" in stderr_text or "wrong password" in output.lower():
                info.error = "Wrong password or encrypted archive"
            elif "Cannot open" in stderr_text:
                info.error = f"Cannot open archive: {filepath}"
            else:
                info.error = stderr_text or output
            return info

        # 解析归档信息 | Parse archive info
        info = self._parse_list_output(output, filepath, encoding_mode, forced_encoding)

        # 获取zip文件注释 | Get comment if it's a zip file
        if filepath.lower().endswith(".zip"):
            comment = self._get_zip_comment(filepath)
            if comment:
                info.comment = comment

        return info

    def _parse_list_output(self, output: str, filepath: str,
                           encoding_mode: str, forced_encoding: str) -> ArchiveInfo:
        """将7z l -slt输出解析为ArchiveInfo | Parse 7z l -slt output into ArchiveInfo."""
        info = ArchiveInfo(path=filepath)
        current_entry = None

        for line in output.split("\n"):
            line = line.strip()

            # 归档级属性 | Archive-level properties
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

            # 条目级属性 | Entry-level properties
            elif line.startswith("Path = "):
                if current_entry:
                    info.entries.append(current_entry)
                raw_name = line[7:]
                fixed_name = self._fix_filename(raw_name, encoding_mode, forced_encoding)
                current_entry = ArchiveEntry(
                    filename=fixed_name,
                    original_filename=raw_name,
                )
            elif current_entry:
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
                    current_entry.is_dir = "D" in attr
                elif line.startswith("CRC = "):
                    current_entry.crc = line[6:]
                elif line.startswith("Encrypted = "):
                    current_entry.encrypted = line[12:] == "+"
                elif line.startswith("Method = "):
                    current_entry.method = line[9:]

        if current_entry:
            info.entries.append(current_entry)

        return info

    def _fix_filename(self, filename: str, encoding_mode: str,
                      forced_encoding: str) -> str:
        """根据模式修复文件名编码 | Fix filename encoding based on mode."""
        if encoding_mode == "none":
            return filename
        elif encoding_mode == "force":
            return fix_zip_filename(filename, "cp437", forced_encoding)
        else:  # auto
            return auto_detect_zip_filename(filename)

    def _get_zip_comment(self, filepath: str) -> str:
        """提取ZIP归档注释 | Extract ZIP archive comment."""
        try:
            import zipfile
            with zipfile.ZipFile(filepath, "r") as zf:
                if zf.comment:
                    # 先尝试UTF-8，然后GBK，最后降级处理 | Try UTF-8 first, then GBK, then fallback
                    for enc in ("utf-8", "gbk", "gb18030", "latin-1"):
                        try:
                            return zf.comment.decode(enc)
                        except (UnicodeDecodeError, LookupError):
                            continue
                    return zf.comment.decode("utf-8", errors="replace")
        except Exception:
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

        Args:
            filepath: 归档文件路径 | Archive path.
            output_dir: 目标目录 | Destination directory.
            password: 可选密码 | Optional password.
            entries: 要提取的特定条目列表 | Optional list of entries to extract.
            create_parent_dir: 创建父文件夹 | Create a parent folder.
            encoding_mode: "auto"、"force"或"none" | "auto", "force", or "none".
            forced_encoding: mode为"force"时的编码 | Encoding when mode is "force".
            overwrite: 覆盖现有文件 | Overwrite existing files.
            progress_callback: 回调函数(文件名, 百分比) | Callback(filename, percent).

        Returns:
            (成功: bool, 消息: str) | (success: bool, message: str)
        """
        if create_parent_dir:
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            # 处理如.tar.gz的双扩展名 | Handle double extensions like .tar.gz
            if base_name.endswith(".tar"):
                base_name = base_name[:-4]
            output_dir = os.path.join(output_dir, base_name)
            os.makedirs(output_dir, exist_ok=True)

        args = ["x", filepath, f"-o{output_dir}"]

        if overwrite:
            args.append("-aoa")  # 覆盖所有 | Overwrite all
        else:
            args.append("-aos")  # 跳过现有 | Skip existing

        if entries:
            args.extend(entries)

        result = self._run_7z(args, password=password, timeout=3600)

        try:
            output = result.stdout.decode("utf-8", errors="replace")
        except Exception:
            output = ""

        if result.returncode == 0:
            # 如果需要编码修复，重命名提取的文件 | If encoding fix needed, rename extracted files
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
        """提取后重命名乱码文件名 | Rename files with garbled names after extraction."""
        # 获取目标目录的真实路径用于路径遍历校验 | Get real path for traversal validation
        real_dir = os.path.realpath(directory)
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files + dirs:
                fixed = self._fix_filename(name, encoding_mode, forced_encoding)
                if fixed != name:
                    old_path = os.path.join(root, name)
                    new_path = os.path.join(root, fixed)
                    # 防止路径遍历: 确保新路径仍在目标目录内
                    # Prevent path traversal: ensure new path stays within target dir
                    if not os.path.realpath(new_path).startswith(real_dir + os.sep):
                        continue
                    if not os.path.exists(new_path):
                        try:
                            os.rename(old_path, new_path)
                        except OSError:
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

        Returns:
            (成功: bool, 消息: str) | (success: bool, message: str)
        """
        args = ["a", output_path]

        # 格式 | Format
        args.append(f"-t{format}")

        # 压缩级别(0-9) | Compression level (0-9)
        args.append(f"-mx={compression_level}")

        # 方法 | Method
        if method:
            args.append(f"-m0={method}")

        # 固实模式(仅7z) | Solid mode (7z only)
        if format == "7z":
            args.append(f"-ms={'on' if solid else 'off'}")

        # 加密文件名(仅7z) | Encrypt filenames (7z only)
        if encrypt_filenames and password and format == "7z":
            args.append("-mhe=on")

        # 分卷 | Volume splitting
        if volumes:
            args.append(f"-v{volumes}")

        # ZIP编码 | Encoding for ZIP
        if format == "zip":
            if encoding_mode == "force" and forced_encoding.lower() in ("gbk", "gb2312", "gb18030"):
                # 使用ZIP文件名代码页 | Use codepage for ZIP filenames
                args.append("-mcp=936")  # CP936 = GBK
            else:
                args.append("-mcu=on")  # 强制文件名使用UTF-8 | Force UTF-8 for filenames

        args.extend(input_paths)

        result = self._run_7z(args, password=password, timeout=3600)

        try:
            output = result.stdout.decode("utf-8", errors="replace")
        except Exception:
            output = ""

        if result.returncode == 0:
            return True, f"Archive created: {output_path}"
        else:
            stderr = result.stderr.decode("utf-8", errors="replace")
            return False, stderr or output

    def test_archive(self, filepath: str, password: Optional[str] = None) -> tuple:
        """测试归档文件完整性 | Test archive integrity.

        Returns:
            (成功: bool, 消息: str) | (success: bool, message: str)
        """
        args = ["t", filepath]
        result = self._run_7z(args, password=password)

        try:
            output = result.stdout.decode("utf-8", errors="replace")
        except Exception:
            output = ""

        if result.returncode == 0:
            return True, "Archive test passed: OK"
        else:
            stderr = result.stderr.decode("utf-8", errors="replace")
            return False, stderr or output

    @staticmethod
    def get_supported_extensions() -> List[str]:
        """获取可处理的文件扩展名列表 | Get list of file extensions we can handle."""
        return [
            ".7z", ".zip", ".rar", ".tar", ".gz", ".bz2", ".xz",
            ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz",
            ".cab", ".iso", ".wim", ".arj", ".cpio", ".rpm", ".deb",
            ".lzh", ".lzma", ".z", ".zst", ".tar.zst",
        ]
