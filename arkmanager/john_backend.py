"""John the Ripper 集成后端 | Backend for John the Ripper integration.

该模块集成John the Ripper (JTR)密码破解工具，支持从压缩包中提取密码哈希
并使用多种攻击模式破解。JTR是开源的密码审计工具，支持数百种哈希格式。

核心功能 | Core functionality:
1. 使用*2john工具从压缩包提取密码哈希（zip2john、rar2john等）
2. 支持四种攻击模式：字典、增量、单字、掩码
3. 管理破解进程生命周期（启动、监控、停止）
4. 查询已破解的密码

This module integrates John the Ripper (JTR) password cracking tool, supporting
hash extraction from archives and cracking with multiple attack modes. JTR is an
open-source password auditing tool supporting hundreds of hash formats.
"""

import os
import signal
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

# ==================== 枚举和数据类 | Enums and Data Classes ====================

class AttackMode(Enum):
    """攻击模式枚举 | Attack mode enumeration.

    四种主要攻击模式 | Four main attack modes:
    - WORDLIST: 字典攻击，使用预定义密码列表
      Dictionary attack with predefined password list
    - INCREMENTAL: 增量暴力破解，尝试所有可能组合
      Incremental brute-force trying all combinations
    - SINGLE: 单字模式，基于用户名等信息生成变体
      Single mode, generates variants based on username etc.
    - MASK: 掩码攻击，按规则生成密码（如"?u?l?l?d"）
      Mask attack, generates passwords by rules (e.g., "?u?l?l?d")
    """
    WORDLIST = "wordlist"
    INCREMENTAL = "incremental"
    SINGLE = "single"
    MASK = "mask"


@dataclass
class JohnResult:
    """John the Ripper 会话的结果 | Result from a John the Ripper session.

    封装JTR破解任务的完整结果信息，包括破解进度、速度、时间等统计数据。
    Encapsulates complete result information from JTR cracking task including
    progress, speed, time statistics.

    Attributes:
        hash_file: 哈希文件路径 | Hash file path
        password: 破解出的密码（如果成功） | Cracked password (if successful)
        found: 是否成功破解 | Whether cracking succeeded
        status: JTR状态输出 | JTR status output
        progress: 破解进度信息 | Cracking progress info
        speed: 破解速度（每秒尝试次数） | Cracking speed (tries per second)
        time_elapsed: 已用时间 | Time elapsed
        error: 错误信息（如果失败） | Error message (if failed)
    """
    hash_file: str = ""
    password: str = ""
    found: bool = False
    status: str = ""
    progress: str = ""
    speed: str = ""
    time_elapsed: str = ""
    error: str = ""


# ==================== John the Ripper 后端类 | John the Ripper Backend Class ====================

class JohnBackend:
    """John the Ripper 操作后端 | Backend for John the Ripper operations.

    封装JTR命令行工具的所有操作，包括哈希提取、密码破解、进程管理等。
    自动查找JTR安装位置，支持系统安装、snap安装等多种部署方式。

    Wraps all operations of JTR CLI tool including hash extraction, password
    cracking, process management. Auto-locates JTR installation, supports
    system installation, snap installation and other deployment methods.

    Attributes:
        john_path: JTR可执行文件路径 | JTR executable path
        john_dir: JTR安装目录 | JTR installation directory
        _process: 当前运行的JTR进程 | Currently running JTR process
        HASH_EXTRACTORS: 哈希提取工具映射表 | Hash extractor tool mappings
    """

    # 支持的 *2john 哈希提取工具映射表 | Supported *2john hash extractor tool mappings
    # 这些工具从加密文件中提取密码哈希，供JTR破解
    # These tools extract password hashes from encrypted files for JTR to crack
    HASH_EXTRACTORS = {
        ".zip": "zip2john",            # ZIP压缩包 | ZIP archives
        ".rar": "rar2john",            # RAR压缩包 | RAR archives
        ".7z": "7z2john.pl",           # 7z压缩包（Perl脚本） | 7z archives (Perl script)
        ".pdf": "pdf2john.pl",         # PDF文档（Perl脚本） | PDF documents (Perl script)
        ".doc": "office2john.py",      # Office文档（Python脚本） | Office documents (Python script)
        ".docx": "office2john.py",
        ".xls": "office2john.py",
        ".xlsx": "office2john.py",
        ".ppt": "office2john.py",
        ".pptx": "office2john.py",
        ".kdbx": "keepass2john",       # KeePass数据库 | KeePass databases
        ".gpg": "gpg2john",            # GPG加密文件 | GPG encrypted files
        ".ssh": "ssh2john",            # SSH私钥 | SSH private keys
    }

    def __init__(self, john_path: str = "john"):
        """初始化JTR后端 | Initialize JTR backend.

        Args:
            john_path: JTR可执行文件路径或命令名 | JTR executable path or command name
        """
        self.john_path = john_path
        self.john_dir = ""
        self._process: Optional[subprocess.Popen] = None
        self._find_john()

    # ==================== 内部辅助方法 | Internal Helper Methods ====================

    def _find_john(self):
        """查找 John the Ripper 安装路径 | Find John the Ripper installation.

        按优先级顺序查找JTR可执行文件：
        1. PATH中的john命令
        2. 系统标准路径（/usr/bin、/usr/local/bin等）
        3. 源码编译路径（/opt/john）
        4. snap安装路径

        Searches for JTR executable in priority order:
        1. john command in PATH
        2. System standard paths (/usr/bin, /usr/local/bin, etc.)
        3. Source compiled path (/opt/john)
        4. snap installation path
        """
        # 检查常见位置 | Check common locations
        search_paths = [
            "john",                                      # PATH中的命令 | Command in PATH
            "/usr/bin/john",                            # Debian/Ubuntu系统安装
            "/usr/sbin/john",                           # 某些发行版放在sbin | Some distros use sbin
            "/usr/local/bin/john",                      # 手动安装 | Manual installation
            "/opt/john/run/john",                       # 源码编译 | Source compiled
            "/snap/john-the-ripper/current/run/john",   # Snap安装 | Snap installation
        ]

        for path in search_paths:
            try:
                # 运行--help检查可执行性 | Run --help to check executability
                subprocess.run(
                    [path, "--help"],
                    capture_output=True, timeout=10
                )
                self.john_path = path
                # 保存安装目录，用于查找*2john工具 | Save installation dir for finding *2john tools
                self.john_dir = os.path.dirname(os.path.realpath(path))
                return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        # 尝试通过 snap 运行 | Try running via snap
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
        """检查 John the Ripper 是否可用 | Check if John the Ripper is available."""
        try:
            subprocess.run(
                self.john_path.split() + ["--help"],
                capture_output=True, timeout=10
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _find_tool(self, tool_name: str) -> Optional[str]:
        """查找 *2john 辅助工具 | Find a *2john helper tool."""
        # 检查常见位置 | Check common locations
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

        # 尝试在 PATH 中查找 | Try in PATH
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

    # ==================== 公共API方法 | Public API Methods ====================

    def extract_hash(self, archive_path: str) -> tuple:
        """从归档文件中提取密码哈希 | Extract password hash from an archive.

        使用对应的*2john工具从加密的压缩包中提取密码哈希值。
        哈希是密码的单向加密表示，JTR通过尝试大量密码并对比哈希来破解。

        Uses corresponding *2john tool to extract password hash from encrypted archive.
        Hash is one-way encrypted representation of password, JTR cracks by trying
        many passwords and comparing hashes.

        工作流程 | Workflow:
        1. 根据文件扩展名选择*2john工具
        2. 运行工具提取哈希
        3. 将哈希保存到临时文件
        4. 返回哈希文件路径供JTR使用

        Args:
            archive_path: 压缩包文件路径 | Archive file path

        Returns:
            (成功标志, 哈希文件路径, 错误信息) | (success: bool, hash_file_path: str, error: str)
        """
        # 步骤1：根据扩展名选择提取工具 | Step 1: Select extraction tool by extension
        ext = os.path.splitext(archive_path)[1].lower()
        tool_name = self.HASH_EXTRACTORS.get(ext)

        if not tool_name:
            return False, "", f"Unsupported format for hash extraction: {ext}"

        # 步骤2：查找工具路径 | Step 2: Find tool path
        tool_path = self._find_tool(tool_name)
        if not tool_path:
            return False, "", f"{tool_name} not found. Install john-the-ripper."

        # 步骤3：创建临时文件存储哈希 | Step 3: Create temp file for hash storage
        # 使用tempfile确保文件名唯一且自动清理
        # Use tempfile to ensure unique filename and auto-cleanup
        hash_fd, hash_file = tempfile.mkstemp(suffix=".hash", prefix="arkman_")
        os.close(hash_fd)  # 关闭文件描述符，后续用open()操作 | Close fd, use open() later

        try:
            # 步骤4：确定如何运行工具 | Step 4: Determine how to run the tool
            # Perl脚本需要perl解释器，Python脚本需要python3
            # Perl scripts need perl interpreter, Python scripts need python3
            cmd = []
            if tool_name.endswith(".pl"):
                cmd = ["perl", tool_path, archive_path]
            elif tool_name.endswith(".py"):
                cmd = ["python3", tool_path, archive_path]
            else:
                cmd = [tool_path, archive_path]

            # 步骤5：运行提取工具 | Step 5: Run extraction tool
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,  # 1分钟超时 | 1 minute timeout
            )

            # 步骤6：解析输出 | Step 6: Parse output
            output = result.stdout.decode("utf-8", errors="replace")

            if output.strip():
                # 哈希提取成功，保存到文件 | Hash extracted successfully, save to file
                with open(hash_file, "w") as f:
                    f.write(output)
                return True, hash_file, ""
            else:
                # 无输出，提取失败 | No output, extraction failed
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
        """运行 John the Ripper 破解哈希 | Run John the Ripper to crack a hash.

        启动JTR进程执行密码破解任务。支持四种攻击模式和多种配置选项。
        破解过程可能耗时很长（几分钟到几天），设置2小时超时。

        Starts JTR process to perform password cracking task. Supports four attack
        modes and multiple configuration options. Cracking may take very long
        (minutes to days), timeout set to 2 hours.

        Args:
            hash_file: 哈希文件路径 | Hash file path
            attack_mode: 攻击模式（字典/增量/单字/掩码）
                Attack mode (wordlist/incremental/single/mask)
            wordlist: 字典文件路径（字典模式） | Wordlist file path (wordlist mode)
            mask: 掩码规则（掩码模式，如"?u?l?l?d?d"）
                Mask rule (mask mode, e.g., "?u?l?l?d?d")
            charset: 字符集（增量模式，如"alpha"、"digits"）
                Charset (incremental mode, e.g., "alpha", "digits")
            min_length: 最小密码长度 | Minimum password length
            max_length: 最大密码长度 | Maximum password length
            format_hint: 哈希格式提示（如"zip"） | Hash format hint (e.g., "zip")
            extra_args: 额外命令行参数 | Extra command-line arguments
            progress_callback: 进度回调函数 | Progress callback function

        Returns:
            包含破解结果的 JohnResult | JohnResult with findings
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
                # 检查是否找到密码 | Check if password was found
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
        """显示已破解的密码 | Show already cracked passwords."""
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
            # 解析输出：格式通常是 "哈希:密码" | Parse output: format is usually "hash:password"
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
        """停止运行中的 John 进程 | Stop the running John process."""
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
        """获取运行中或已完成会话的状态 | Get status of a running or completed session."""
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
        """列出可用的哈希格式 | List available hash formats."""
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
