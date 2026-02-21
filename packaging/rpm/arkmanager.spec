Name:           arkmanager
Version:        1.0.0
Release:        1%{?dist}
Summary:        7-Zip based archive manager for Linux with Chinese encoding support

License:        GPL-3.0-or-later
URL:            https://github.com/aidev666888/ark-manager
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:       python3 >= 3.9
Requires:       python3-qt6
Requires:       python3-chardet
Requires:       p7zip
Requires:       p7zip-plugins
Recommends:     john

%description
ArkManager is a GUI archive manager that uses the 7z CLI backend.
Features include Chinese filename encoding support (GBK/GB18030/Big5),
archive comment display, fake/pseudo encryption detection, Chinese
password support, and John the Ripper integration for password recovery.

%prep
%autosetup

%build
%py3_build

%install
%py3_install
install -Dm644 resources/arkmanager.desktop %{buildroot}%{_datadir}/applications/arkmanager.desktop
install -Dm644 resources/arkmanager.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/arkmanager.svg

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/arkmanager/
%{python3_sitelib}/arkmanager-*.egg-info/
%{_bindir}/arkmanager
%{_datadir}/applications/arkmanager.desktop
%{_datadir}/icons/hicolor/scalable/apps/arkmanager.svg

%changelog
* Sat Feb 22 2025 ArkManager Contributors <arkmanager@users.noreply.github.com> - 1.0.0-1
- Initial release
- Chinese filename encoding support (auto-detect, GBK, GB18030, Big5, Shift-JIS)
- Archive comment display
- Fake/pseudo encryption detection and patching
- John the Ripper integration for password recovery
- Auto-create parent folder option on extraction
