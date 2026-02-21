"""Backend for archive operations using the 7z command."""

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional, Callable

from .encoding_utils import (
    auto_detect_zip_filename,
    fix_zip_filename,
    CJK_ENCODINGS,
)


@dataclass
class ArchiveEntry:
    """Represents a single entry in an archive."""
    filename: str
    original_filename: str  # Raw filename before encoding fix
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
    """Information about an archive."""
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
    """Backend that calls 7z CLI for archive operations."""

    SUPPORTED_FORMATS = [
        "7z", "zip", "tar", "gz", "bz2", "xz", "rar", "cab", "iso",
        "wim", "arj", "cpio", "rpm", "deb", "lzh", "lzma", "z",
        "tar.gz", "tar.bz2", "tar.xz", "tgz", "tbz2", "txz",
        "zst", "tar.zst",
    ]

    def __init__(self, seven_zip_path: str = "7z"):
        self.seven_zip_path = seven_zip_path
        self._verify_7z()

    def _verify_7z(self):
        """Verify 7z is available."""
        try:
            result = subprocess.run(
                [self.seven_zip_path],
                capture_output=True, timeout=10
            )
            # 7z returns 0 or prints version info
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
        """Run 7z with given arguments."""
        cmd = [self.seven_zip_path] + args

        if password is not None:
            # Handle Chinese passwords: pass as-is, 7z handles encoding
            cmd.append(f"-p{password}")

        env = os.environ.copy()
        # Force UTF-8 locale for 7z output
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
        """List contents of an archive with encoding support.

        Args:
            filepath: Path to the archive.
            password: Optional password for encrypted archives.
            encoding_mode: "auto", "force", or "none".
            forced_encoding: Encoding to use when encoding_mode is "force".
        """
        info = ArchiveInfo(path=filepath)

        # Get technical listing
        args = ["l", "-slt", filepath]
        result = self._run_7z(args, password=password)

        stdout = result.stdout
        # Try decoding output
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

        # Parse archive info
        info = self._parse_list_output(output, filepath, encoding_mode, forced_encoding)

        # Get comment if it's a zip file
        if filepath.lower().endswith(".zip"):
            comment = self._get_zip_comment(filepath)
            if comment:
                info.comment = comment

        return info

    def _parse_list_output(self, output: str, filepath: str,
                           encoding_mode: str, forced_encoding: str) -> ArchiveInfo:
        """Parse 7z l -slt output into ArchiveInfo."""
        info = ArchiveInfo(path=filepath)
        current_entry = None

        for line in output.split("\n"):
            line = line.strip()

            # Archive-level properties
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

            # Entry-level properties
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
        """Fix filename encoding based on mode."""
        if encoding_mode == "none":
            return filename
        elif encoding_mode == "force":
            return fix_zip_filename(filename, "cp437", forced_encoding)
        else:  # auto
            return auto_detect_zip_filename(filename)

    def _get_zip_comment(self, filepath: str) -> str:
        """Extract ZIP archive comment."""
        try:
            import zipfile
            with zipfile.ZipFile(filepath, "r") as zf:
                if zf.comment:
                    # Try UTF-8 first, then GBK, then fallback
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
        """Extract archive to output_dir.

        Args:
            filepath: Archive path.
            output_dir: Destination directory.
            password: Optional password.
            entries: Optional list of specific entries to extract.
            create_parent_dir: Create a parent folder named after the archive.
            encoding_mode: "auto", "force", or "none".
            forced_encoding: Encoding when mode is "force".
            overwrite: Overwrite existing files.
            progress_callback: Callback(filename, percent).

        Returns:
            (success: bool, message: str)
        """
        if create_parent_dir:
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            # Handle double extensions like .tar.gz
            if base_name.endswith(".tar"):
                base_name = base_name[:-4]
            output_dir = os.path.join(output_dir, base_name)
            os.makedirs(output_dir, exist_ok=True)

        args = ["x", filepath, f"-o{output_dir}"]

        if overwrite:
            args.append("-aoa")  # Overwrite all
        else:
            args.append("-aos")  # Skip existing

        if entries:
            args.extend(entries)

        result = self._run_7z(args, password=password, timeout=3600)

        try:
            output = result.stdout.decode("utf-8", errors="replace")
        except Exception:
            output = ""

        if result.returncode == 0:
            # If encoding fix needed, rename extracted files
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
        """Rename files with garbled names after extraction."""
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files + dirs:
                fixed = self._fix_filename(name, encoding_mode, forced_encoding)
                if fixed != name:
                    old_path = os.path.join(root, name)
                    new_path = os.path.join(root, fixed)
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
        """Create a new archive.

        Returns:
            (success: bool, message: str)
        """
        args = ["a", output_path]

        # Format
        args.append(f"-t{format}")

        # Compression level (0-9)
        args.append(f"-mx={compression_level}")

        # Method
        if method:
            args.append(f"-m0={method}")

        # Solid mode (7z only)
        if format == "7z":
            args.append(f"-ms={'on' if solid else 'off'}")

        # Encrypt filenames (7z only)
        if encrypt_filenames and password and format == "7z":
            args.append("-mhe=on")

        # Volume splitting
        if volumes:
            args.append(f"-v{volumes}")

        # Encoding for ZIP
        if format == "zip":
            if encoding_mode == "force" and forced_encoding.lower() in ("gbk", "gb2312", "gb18030"):
                # Use codepage for ZIP filenames
                args.append("-mcp=936")  # CP936 = GBK
            else:
                args.append("-mcu=on")  # Force UTF-8 for filenames

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
        """Test archive integrity.

        Returns:
            (success: bool, message: str)
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
        """Get list of file extensions we can handle."""
        return [
            ".7z", ".zip", ".rar", ".tar", ".gz", ".bz2", ".xz",
            ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz",
            ".cab", ".iso", ".wim", ".arj", ".cpio", ".rpm", ".deb",
            ".lzh", ".lzma", ".z", ".zst", ".tar.zst",
        ]
