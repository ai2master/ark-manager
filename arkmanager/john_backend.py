"""Backend for John the Ripper integration."""

import os
import signal
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional


class AttackMode(Enum):
    WORDLIST = "wordlist"
    INCREMENTAL = "incremental"
    SINGLE = "single"
    MASK = "mask"


@dataclass
class JohnResult:
    """Result from a John the Ripper session."""
    hash_file: str = ""
    password: str = ""
    found: bool = False
    status: str = ""
    progress: str = ""
    speed: str = ""
    time_elapsed: str = ""
    error: str = ""


class JohnBackend:
    """Backend for John the Ripper operations."""

    # Supported *2john tools
    HASH_EXTRACTORS = {
        ".zip": "zip2john",
        ".rar": "rar2john",
        ".7z": "7z2john.pl",
        ".pdf": "pdf2john.pl",
        ".doc": "office2john.py",
        ".docx": "office2john.py",
        ".xls": "office2john.py",
        ".xlsx": "office2john.py",
        ".ppt": "office2john.py",
        ".pptx": "office2john.py",
        ".kdbx": "keepass2john",
        ".gpg": "gpg2john",
        ".ssh": "ssh2john",
    }

    def __init__(self, john_path: str = "john"):
        self.john_path = john_path
        self.john_dir = ""
        self._process: Optional[subprocess.Popen] = None
        self._find_john()

    def _find_john(self):
        """Find John the Ripper installation."""
        # Check common locations
        search_paths = [
            "john",
            "/usr/bin/john",
            "/usr/sbin/john",
            "/usr/local/bin/john",
            "/opt/john/run/john",
            "/snap/john-the-ripper/current/run/john",
        ]

        for path in search_paths:
            try:
                subprocess.run(
                    [path, "--help"],
                    capture_output=True, timeout=10
                )
                self.john_path = path
                self.john_dir = os.path.dirname(os.path.realpath(path))
                return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        # Try via snap
        try:
            subprocess.run(
                ["snap", "run", "john-the-ripper"],
                capture_output=True, timeout=10
            )
            self.john_path = "snap run john-the-ripper"
            return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def is_available(self) -> bool:
        """Check if John the Ripper is available."""
        try:
            subprocess.run(
                self.john_path.split() + ["--help"],
                capture_output=True, timeout=10
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _find_tool(self, tool_name: str) -> Optional[str]:
        """Find a *2john helper tool."""
        # Check common locations
        search_dirs = [
            self.john_dir,
            os.path.join(self.john_dir, ".."),
            "/usr/bin",
            "/usr/share/john",
            "/usr/lib/john",
            "/opt/john/run",
            "/snap/john-the-ripper/current/run",
        ]

        for d in search_dirs:
            path = os.path.join(d, tool_name)
            if os.path.isfile(path):
                return path

        # Try in PATH
        try:
            result = subprocess.run(
                ["which", tool_name],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.decode().strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def extract_hash(self, archive_path: str) -> tuple:
        """Extract password hash from an archive.

        Returns:
            (success: bool, hash_file_path: str, error: str)
        """
        ext = os.path.splitext(archive_path)[1].lower()
        tool_name = self.HASH_EXTRACTORS.get(ext)

        if not tool_name:
            return False, "", f"Unsupported format for hash extraction: {ext}"

        tool_path = self._find_tool(tool_name)
        if not tool_path:
            return False, "", f"{tool_name} not found. Install john-the-ripper."

        # Create temp file for hash
        hash_fd, hash_file = tempfile.mkstemp(suffix=".hash", prefix="arkman_")
        os.close(hash_fd)

        try:
            # Determine how to run the tool
            cmd = []
            if tool_name.endswith(".pl"):
                cmd = ["perl", tool_path, archive_path]
            elif tool_name.endswith(".py"):
                cmd = ["python3", tool_path, archive_path]
            else:
                cmd = [tool_path, archive_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
            )

            output = result.stdout.decode("utf-8", errors="replace")

            if output.strip():
                with open(hash_file, "w") as f:
                    f.write(output)
                return True, hash_file, ""
            else:
                stderr = result.stderr.decode("utf-8", errors="replace")
                os.unlink(hash_file)
                return False, "", stderr or "No hash extracted"

        except subprocess.TimeoutExpired:
            os.unlink(hash_file)
            return False, "", "Hash extraction timed out"
        except Exception as e:
            os.unlink(hash_file)
            return False, "", str(e)

    def crack(self, hash_file: str,
              attack_mode: AttackMode = AttackMode.WORDLIST,
              wordlist: str = "",
              mask: str = "",
              charset: str = "",
              min_length: int = 0,
              max_length: int = 0,
              format_hint: str = "",
              extra_args: Optional[List[str]] = None,
              progress_callback: Optional[Callable[[str], None]] = None) -> JohnResult:
        """Run John the Ripper to crack a hash.

        Returns JohnResult with findings.
        """
        result = JohnResult(hash_file=hash_file)

        cmd = self.john_path.split()

        if attack_mode == AttackMode.WORDLIST:
            if wordlist:
                cmd.append(f"--wordlist={wordlist}")
            else:
                cmd.append("--wordlist")
        elif attack_mode == AttackMode.INCREMENTAL:
            if charset:
                cmd.append(f"--incremental={charset}")
            else:
                cmd.append("--incremental")
        elif attack_mode == AttackMode.SINGLE:
            cmd.append("--single")
        elif attack_mode == AttackMode.MASK:
            if mask:
                cmd.append(f"--mask={mask}")

        if min_length > 0:
            cmd.append(f"--min-length={min_length}")
        if max_length > 0:
            cmd.append(f"--max-length={max_length}")

        if format_hint:
            cmd.append(f"--format={format_hint}")

        if extra_args:
            cmd.extend(extra_args)

        cmd.append(hash_file)

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "LANG": "en_US.UTF-8"},
            )

            stdout, stderr = self._process.communicate(timeout=7200)

            output = stdout.decode("utf-8", errors="replace")
            err_output = stderr.decode("utf-8", errors="replace")

            result.status = output
            if self._process.returncode == 0:
                # Check if password was found
                found = self.show_cracked(hash_file, format_hint)
                if found:
                    result.password = found
                    result.found = True
            else:
                result.error = err_output

        except subprocess.TimeoutExpired:
            if self._process:
                self._process.kill()
            result.error = "Cracking timed out"
        except Exception as e:
            result.error = str(e)
        finally:
            self._process = None

        return result

    def show_cracked(self, hash_file: str, format_hint: str = "") -> str:
        """Show already cracked passwords."""
        cmd = self.john_path.split() + ["--show"]
        if format_hint:
            cmd.append(f"--format={format_hint}")
        cmd.append(hash_file)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
            )
            output = result.stdout.decode("utf-8", errors="replace")
            # Parse output: format is usually "hash:password"
            lines = output.strip().split("\n")
            for line in lines:
                if ":" in line and "password hash" not in line.lower():
                    parts = line.split(":")
                    if len(parts) >= 2:
                        return parts[1]
            return ""
        except Exception:
            return ""

    def stop(self):
        """Stop the running John process."""
        if self._process:
            try:
                self._process.send_signal(signal.SIGINT)
                self._process.wait(timeout=10)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    self._process.kill()
                except ProcessLookupError:
                    pass
            finally:
                self._process = None

    def get_status(self, hash_file: str) -> str:
        """Get status of a running or completed session."""
        cmd = self.john_path.split() + ["--status"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
            )
            return result.stdout.decode("utf-8", errors="replace")
        except Exception:
            return ""

    def list_formats(self) -> List[str]:
        """List available hash formats."""
        cmd = self.john_path.split() + ["--list=formats"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
            )
            output = result.stdout.decode("utf-8", errors="replace")
            formats = []
            for line in output.split("\n"):
                for fmt in line.split(","):
                    fmt = fmt.strip()
                    if fmt:
                        formats.append(fmt)
            return formats
        except Exception:
            return []
