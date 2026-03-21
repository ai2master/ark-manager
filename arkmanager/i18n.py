# -*- coding: utf-8 -*-
"""
国际化模块 | Internationalization module

提供基于字典的多语言支持。
Provides dictionary-based multilingual support.
"""

from PyQt6.QtCore import QLocale, QSettings

# 当前语言代码 | Current language code
_current_lang = 'en_US'

# 翻译字典 | Translation dictionary
_TRANSLATIONS = {
    'zh_CN': {
        # ==================== 窗口标题 | Window titles ====================
        'Extract Archive': '解压压缩包',
        'Create Archive': '创建压缩包',
        'Fake Encryption Detection': '伪加密检测',
        'Password Recovery (John the Ripper)': '密码恢复 (John the Ripper)',
        'Checksum / Hash': '校验和 / 哈希',
        'About ArkManager': '关于 ArkManager',
        'Benchmark Result': '基准测试结果',
        'Keyboard Shortcuts': '键盘快捷键',
        'Batch Extract': '批量解压',
        'Properties': '属性',

        # ==================== 菜单栏 | Menu bar ====================
        '&File': '文件(&F)',
        '&Open Archive...': '打开压缩包(&O)...',
        'Open &Recent': '最近打开(&R)',
        '&Create Archive...': '创建压缩包(&C)...',
        'Batch E&xtract...': '批量解压(&X)...',
        'Close Archive': '关闭压缩包',
        'E&xit': '退出(&X)',
        '&Edit': '编辑(&E)',
        'Select &All': '全选(&A)',
        '&Invert Selection': '反选(&I)',
        '&Copy Path': '复制路径(&C)',
        '&Actions': '操作(&A)',
        '&Extract...': '解压(&E)...',
        'Extract &Here': '解压到此处(&H)',
        '&Test Archive': '测试压缩包(&T)',
        'Add &Files to Archive...': '添加文件到压缩包(&F)...',
        '&Delete from Archive': '从压缩包删除(&D)',
        'Detect &Fake Encryption...': '检测伪加密(&F)...',
        '&View': '视图(&V)',
        '&Flat View': '平铺视图(&F)',
        '&Search': '搜索(&S)',
        'Show &Preview': '显示预览(&P)',
        'Show &Console': '显示控制台(&C)',
        'Show &Toolbar': '显示工具栏(&T)',
        '&Refresh': '刷新(&R)',
        '&Tools': '工具(&T)',
        'Checksum / &Hash...': '校验和 / 哈希(&H)...',
        '&Password Recovery...': '密码恢复(&P)...',
        '&Benchmark...': '基准测试(&B)...',
        'Install &Desktop Integration': '安装桌面集成(&D)',
        'Remove Desktop Integration': '移除桌面集成',
        '&Settings': '设置(&S)',
        '&Language': '语言(&L)',
        '&Theme': '主题(&T)',
        'Light': '浅色',
        'Dark': '暗色',
        '&Help': '帮助(&H)',
        '&About ArkManager': '关于 ArkManager(&A)',
        '&GitHub Repository': 'GitHub 仓库(&G)',
        '&Keyboard Shortcuts': '键盘快捷键(&K)',

        # ==================== 工具栏按钮 | Toolbar buttons ====================
        'Open': '打开',
        'Extract': '解压',
        'Create': '创建',
        'Test': '测试',
        'Fake Enc?': '伪加密?',
        'Password Recovery': '密码恢复',
        'Checksum': '校验和',
        'Search': '搜索',
        'Flat View': '平铺视图',
        'Tree View': '树形视图',

        # ==================== 分组框和标签 | Group boxes and labels ====================
        'Source': '来源',
        'Destination': '目标',
        'Options': '选项',
        'Password': '密码',
        'Output': '输出',
        'Format && Compression': '格式和压缩',
        'Filename Encoding (ZIP only)': '文件名编码 (仅ZIP)',
        'Encryption': '加密',
        'Target': '目标',
        'Hash Extraction': '哈希提取',
        'Attack Configuration': '攻击配置',
        'Archive Comment': '压缩包注释',
        'Archive Info': '压缩包信息',
        'Preview': '预览',
        'Console': '控制台',
        'File': '文件',
        'Algorithm': '算法',
        'Hash Value': '哈希值',

        # ==================== 按钮 | Buttons ====================
        'Browse...': '浏览...',
        'OK': '确定',
        'Cancel': '取消',
        'Close': '关闭',
        'Start Cracking': '开始破解',
        'Stop': '停止',
        'Extract Hash': '提取哈希',
        'Remove Fake Encryption': '移除伪加密',
        'Show': '显示',
        'Show password': '显示密码',
        'Copy': '复制',
        'Copy All': '复制全部',
        'Export...': '导出...',
        'Verify': '校验',
        'Calculate': '计算',
        'Add Files...': '添加文件...',
        'Clear': '清除',
        'Save Log...': '保存日志...',

        # ==================== 复选框和选项 | Checkboxes and options ====================
        'Create parent folder (named after the archive)': '创建以压缩包命名的父文件夹',
        'Overwrite existing files': '覆盖已有文件',
        'Smart extract (auto-detect subfolder)': '智能解压 (自动检测子文件夹)',
        'Encrypt filenames (7z only)': '加密文件名 (仅7z)',
        'Solid archive (7z only)': '固实压缩 (仅7z)',

        # ==================== 组合框项目 | Combo box items ====================
        'Auto Detect': '自动检测',
        'Force GBK (Simplified Chinese)': '强制 GBK (简体中文)',
        'Force GB18030': '强制 GB18030',
        'Force Big5': '强制 Big5',
        'Force Shift-JIS': '强制 Shift-JIS',
        'No conversion': '不转换',
        'No Conversion': '不转换',
        'UTF-8 (Recommended)': 'UTF-8 (推荐)',
        'Force GBK (CP936)': '强制 GBK (CP936)',
        'Default': '默认',
        'Copy (Store)': '复制 (存储)',
        'Wordlist': '字典',
        'Incremental (Brute Force)': '增量 (暴力破解)',
        'Single Crack': '单字破解',
        'Mask Attack': '掩码攻击',
        'Digits': '数字',
        'Alpha': '字母',
        'Alnum': '字母数字',
        'Auto': '自动',
        'PKZIP': 'PKZIP',
        'ZIP (AES)': 'ZIP (AES)',
        'RAR': 'RAR',

        # ==================== 占位符 | Placeholders ====================
        'Open an archive file...': '打开一个压缩包文件...',
        'Enter password if required (supports Chinese)': '如需密码请输入 (支持中文)',
        'Leave empty for no encryption (supports Chinese)': '留空则不加密 (支持中文)',
        'Confirm password': '确认密码',
        'Additional john arguments': '额外的john参数',
        'No comment in this archive.': '该压缩包无注释。',
        'Search files... (Ctrl+F)': '搜索文件... (Ctrl+F)',
        'Volume size (e.g., 100m, 1g)': '分卷大小 (如 100m, 1g)',

        # ==================== 状态消息 | Status messages ====================
        'Ready': '就绪',
        'Extracting...': '正在解压...',
        'Extraction complete.': '解压完成。',
        'Extraction failed.': '解压失败。',
        'Creating archive...': '正在创建压缩包...',
        'Archive created.': '压缩包已创建。',
        'Compression failed.': '压缩失败。',
        'Testing archive...': '正在测试压缩包...',
        'Adding files...': '正在添加文件...',
        'Analyzing...': '正在分析...',
        'No hash extracted yet': '尚未提取哈希',
        'Extracting hash...': '正在提取哈希...',
        'Calculating...': '正在计算...',
        'No archive opened.': '未打开压缩包。',
        'An operation is already in progress.': '有操作正在进行中。',
        'Password not found with current settings.': '使用当前设置未找到密码。',
        'Filename encoding for preview': '文件名编码预览',

        # ==================== 对话框消息 | Dialog messages ====================
        'Error': '错误',
        'Success': '成功',
        'Info': '信息',
        'Warning': '警告',
        'Password Required': '需要密码',
        'Test Result': '测试结果',
        'Extraction Failed': '解压失败',
        'Compression Failed': '压缩失败',
        'Please specify output file path.': '请指定输出文件路径。',
        'Passwords do not match.': '密码不匹配。',
        'Please select a target file.': '请选择目标文件。',
        'Extract hash first.': '请先提取哈希。',
        'Fake encryption detection only works with ZIP files.': '伪加密检测仅适用于ZIP文件。',
        'No fake encryption detected.': '未检测到伪加密。',
        'Failed to patch archive.': '修复压缩包失败。',
        'Files added to archive.': '文件已添加到压缩包。',

        # ==================== 树形列 | Tree columns ====================
        'Name': '名称',
        'Size': '大小',
        'Compressed': '压缩后',
        'Modified': '修改时间',
        'CRC': 'CRC',
        'Encrypted': '已加密',
        'Method': '方法',
        'Path': '路径',
        'Yes': '是',
        'No': '否',

        # ==================== 文件对话框标题 | File dialog titles ====================
        'Select Destination': '选择目标目录',
        'Save Archive As': '另存压缩包为',
        'Open Archive': '打开压缩包',
        'Select Archive': '选择压缩包',
        'Select Wordlist': '选择字典文件',
        'Select Files to Compress': '选择要压缩的文件',
        'Add Files to Archive': '添加文件到压缩包',
        'Save Patched Archive': '保存已修复的压缩包',
        'Select Files': '选择文件',
        'Export Checksums': '导出校验和',
        'Save Log': '保存日志',

        # ==================== 新增功能 | New features ====================
        # 哈希/校验和 | Hash/Checksum
        'MD5': 'MD5',
        'SHA-1': 'SHA-1',
        'SHA-256': 'SHA-256',
        'SHA-512': 'SHA-512',
        'CRC32': 'CRC32',
        'Select algorithms:': '选择算法：',
        'Results': '结果',
        'Copied to clipboard.': '已复制到剪贴板。',
        'No results to export.': '没有结果可导出。',
        'Checksums exported to {path}': '校验和已导出到 {path}',

        # 统计信息 | Statistics
        '{count} files, {size} total, {ratio} compression ratio':
        '{count} 个文件, 总大小 {size}, 压缩率 {ratio}',
        'Flat view: {count} files': '平铺视图: {count} 个文件',
        '{matched} of {total} files': '{matched} / {total} 个文件',

        # 预览 | Preview
        'Preview not available for this file type.': '该文件类型不支持预览。',
        'File too large for preview ({size}).': '文件过大，无法预览 ({size})。',
        'Binary file - showing hex dump:': '二进制文件 - 显示十六进制：',

        # 右键菜单 | Context menu
        'Extract Selected': '解压所选文件',
        'Calculate Hash': '计算哈希',
        'Copy Filename': '复制文件名',
        'Copy Path': '复制路径',
        'Select All': '全选',

        # 桌面集成 | Desktop integration
        'Desktop integration installed successfully.': '桌面集成安装成功。',
        'Desktop integration removed.': '桌面集成已移除。',

        # 其他消息 | Other messages
        'This archive has only one top-level folder. '
        'No extra folder will be created.': '该压缩包只有一个顶级文件夹，不会创建额外文件夹。',
        'Language changed. Some changes may require restart.':
        '语言已更改。部分更改可能需要重启。',

        # 批量解压 | Batch extract
        'Select Archives to Extract': '选择要解压的压缩包',
        'Extracting {current}/{total}: {name}': '正在解压 {current}/{total}: {name}',
        'Batch extraction complete. {success}/{total} succeeded.':
        '批量解压完成。{success}/{total} 成功。',

        # ==================== 格式化字符串 | Format strings ====================
        'Hash: {hash}': '哈希: {hash}',
        'Found password: {password}': '找到密码: {password}',
        'Hash extracted: {format}': '已提取哈希: {format}',
        'Hash extraction failed: {error}': '哈希提取失败: {error}',

        # ==================== 关于对话框 | About dialog ====================
        'about_text': '''<h2>ArkManager</h2>
<p><b>版本:</b> 1.0.0</p>
<p><b>基于 PyQt6 的现代压缩包管理器</b></p>
<p>ArkManager 是一款功能强大的压缩包管理工具，支持多种格式和高级功能。</p>
<h3>主要特性:</h3>
<ul>
<li>支持 7z, ZIP, RAR, TAR, GZ, BZ2 等多种格式</li>
<li>中文编码智能处理 (GBK/GB18030/Big5)</li>
<li>伪加密检测与修复</li>
<li>密码恢复 (John the Ripper 集成)</li>
<li>文件哈希计算与校验</li>
<li>压缩包注释查看</li>
<li>批量解压</li>
<li>文件预览</li>
</ul>
<p><b>作者:</b> ArkManager Team</p>
<p><b>许可证:</b> MIT License</p>
<p><b>GitHub:</b> <a href="https://github.com/ai2master/ark-manager">https://github.com/ai2master/ark-manager</a></p>
'''
    }
}


def tr(text: str) -> str:
    """
    翻译文本 | Translate text

    Args:
        text: 要翻译的英文文本 | English text to translate

    Returns:
        翻译后的文本，如果没有翻译则返回原文 | Translated text, or original if not found
    """
    if _current_lang == 'en_US':
        return text

    return _TRANSLATIONS.get(_current_lang, {}).get(text, text)


def set_language(code: str) -> None:
    """
    设置当前语言 | Set current language

    Args:
        code: 语言代码 (如 'zh_CN', 'en_US') | Language code (e.g., 'zh_CN', 'en_US')
    """
    global _current_lang
    if code in ['en_US', 'zh_CN']:
        _current_lang = code
        # 保存到设置 | Save to settings
        settings = QSettings('ArkManager', 'ArkManager')
        settings.setValue('language', code)


def get_language() -> str:
    """
    获取当前语言代码 | Get current language code

    Returns:
        当前语言代码 | Current language code
    """
    return _current_lang


def get_available_languages() -> dict:
    """
    获取可用的语言列表 | Get available languages

    Returns:
        语言代码到显示名称的字典 | Dictionary mapping language codes to display names
    """
    return {
        'en_US': 'English',
        'zh_CN': '简体中文'
    }


def init_language() -> None:
    """
    初始化语言设置 | Initialize language settings

    从 QSettings 加载保存的语言偏好，如果没有则自动检测系统语言。
    Load saved language preference from QSettings, or auto-detect from system if not found.
    """
    global _current_lang

    # 尝试从设置加载 | Try to load from settings
    settings = QSettings('ArkManager', 'ArkManager')
    saved_lang = settings.value('language', None)

    if saved_lang and saved_lang in ['en_US', 'zh_CN']:
        _current_lang = saved_lang
    else:
        # 自动检测系统语言 | Auto-detect system language
        system_locale = QLocale.system()
        locale_name = system_locale.name()  # 例如 | e.g., 'zh_CN', 'en_US'

        # 如果是中文相关的locale，使用中文 | Use Chinese for Chinese-related locales
        if locale_name.startswith('zh'):
            _current_lang = 'zh_CN'
        else:
            _current_lang = 'en_US'

        # 保存检测到的语言 | Save detected language
        settings.setValue('language', _current_lang)
