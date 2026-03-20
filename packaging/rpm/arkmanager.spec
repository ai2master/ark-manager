# ==============================================================================
# ArkManager RPM 规格文件 | ArkManager RPM Spec File
# ==============================================================================
# RPM .spec 文件是 Red Hat 系 Linux 打包的核心配置，定义了：
#   - 包的元数据（名称、版本、依赖）
#   - 构建步骤（prep → build → install）
#   - 安装的文件列表
#   - 变更日志
#
# RPM .spec is the core packaging config for Red Hat family Linux, defining:
#   - Package metadata (name, version, dependencies)
#   - Build steps (prep → build → install)
#   - Installed file list
#   - Changelog
# ==============================================================================

# -------------------- 包元数据 | Package Metadata --------------------
Name:           arkmanager
Version:        1.0.0
Release:        1%{?dist}
Summary:        7-Zip based archive manager for Linux with Chinese encoding support

License:        GPL-3.0-or-later
URL:            https://github.com/ai2master/ark-manager
Source0:        %{name}-%{version}.tar.gz

# noarch 表示纯 Python 包，不含架构相关的编译代码
# noarch means pure Python package with no architecture-specific compiled code
BuildArch:      noarch

# -------------------- 构建依赖 | Build Dependencies --------------------
# 构建时需要的包，只在 rpmbuild 过程中使用
# Packages needed at build time, only used during rpmbuild process
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel

# -------------------- 运行依赖 | Runtime Dependencies --------------------
# 安装后运行时需要的包 | Packages required at runtime after installation
Requires:       python3 >= 3.9
Requires:       python3-qt6         # PyQt6 GUI 框架 | PyQt6 GUI framework
Requires:       python3-chardet     # 字符编码自动检测 | Auto encoding detection
Requires:       p7zip               # 7z 命令行核心 | 7z CLI core
Requires:       p7zip-plugins       # 7z 额外格式插件（RAR 等）| Extra format plugins (RAR, etc.)
# Recommends 是推荐但非必需的依赖，不安装也不影响核心功能
# Recommends are suggested but optional deps, core features work without them
Recommends:     john                # John the Ripper 密码恢复工具 | Password recovery tool

# -------------------- 详细描述 | Detailed Description --------------------
%description
ArkManager is a GUI archive manager that uses the 7z CLI backend.
Features include Chinese filename encoding support (GBK/GB18030/Big5),
archive comment display, fake/pseudo encryption detection, Chinese
password support, and John the Ripper integration for password recovery.

# ==================== 构建阶段 | Build Phases ====================

# --- %prep: 解压源码 | Extract source ---
# %autosetup 自动解压 Source0 并进入源码目录
# %autosetup automatically extracts Source0 and enters the source directory
%prep
%autosetup

# --- %build: 编译/打包 | Compile/Package ---
# 使用 pyproject.toml 构建 Python wheel 包
# Build Python wheel package using pyproject.toml
%build
%{python3} -m pip wheel --no-deps --no-build-isolation -w dist .

# --- %install: 安装到构建根目录 | Install to buildroot ---
# 将 wheel 安装到 %{buildroot}（虚拟安装目录），rpmbuild 从中收集文件
# Install wheel to %{buildroot} (virtual install dir), rpmbuild collects files from it
%install
%{python3} -m pip install --no-deps --root=%{buildroot} --prefix=%{_prefix} dist/*.whl
# 安装 .desktop 桌面集成文件（644 权限 = rw-r--r--）
# Install .desktop desktop integration file (644 permissions = rw-r--r--)
install -Dm644 resources/arkmanager.desktop %{buildroot}%{_datadir}/applications/arkmanager.desktop
# 安装 SVG 应用图标 | Install SVG application icon
install -Dm644 resources/arkmanager.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/arkmanager.svg

# ==================== 文件列表 | File List ====================
# 列出此 RPM 包安装的所有文件，rpmbuild 据此生成包内容
# Lists all files installed by this RPM; rpmbuild uses this to generate package contents
%files
%license LICENSE                                              # 许可证文件（特殊标记）| License file (special tag)
%doc README.md                                                # 文档文件 | Documentation file
%{python3_sitelib}/arkmanager/                                # Python 应用包 | Python app package
%{python3_sitelib}/arkmanager-*.dist-info/                    # pip 安装元数据 | pip install metadata
%{_bindir}/arkmanager                                         # CLI 启动脚本 | CLI launcher script
%{_bindir}/arkmanager-gui                                     # GUI 启动脚本 | GUI launcher script
%{_datadir}/applications/arkmanager.desktop                   # 桌面集成文件 | Desktop integration file
%{_datadir}/icons/hicolor/scalable/apps/arkmanager.svg        # 应用图标 | Application icon

# ==================== 变更日志 | Changelog ====================
%changelog
* Sat Feb 22 2025 ArkManager Contributors <arkmanager@users.noreply.github.com> - 1.0.0-1
- Initial release
- Chinese filename encoding support (auto-detect, GBK, GB18030, Big5, Shift-JIS)
- Archive comment display
- Fake/pseudo encryption detection and patching
- John the Ripper integration for password recovery
- Auto-create parent folder option on extraction
