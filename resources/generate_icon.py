"""生成ArkManager应用图标 | Generate a simple SVG icon for ArkManager.

此脚本生成一个SVG格式的应用图标，包含：
- 蓝色渐变背景，象征专业工具
- 白色档案盒，代表压缩包容器
- 金色拉链图案，象征压缩与解压操作
- 锁图标，代表加密功能
- "ARK"文字标识

This script generates an SVG application icon containing:
- Blue gradient background symbolizing professional tools
- White archive box representing archive container
- Gold zipper pattern symbolizing compression/extraction operations
- Lock icon representing encryption functionality
- "ARK" text branding
"""

# SVG图标源代码，包含完整的矢量图形定义 | SVG icon source code with complete vector graphics definition
SVG_ICON = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <!-- 背景蓝色渐变 | Background blue gradient -->
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2196F3;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1565C0;stop-opacity:1" />
    </linearGradient>
    <!-- 拉链金色渐变 | Zipper gold gradient -->
    <linearGradient id="zip" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFC107;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#FF8F00;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- 圆角矩形背景 | Background rounded rect -->
  <rect x="8" y="8" width="112" height="112" rx="20" ry="20" fill="url(#bg)" />
  <!-- 档案盒主体 | Archive box -->
  <rect x="28" y="35" width="72" height="60" rx="6" ry="6" fill="#fff" opacity="0.95" />
  <!-- 拉链图案（5个齿） | Zipper pattern (5 teeth) -->
  <rect x="58" y="35" width="12" height="8" fill="url(#zip)" />
  <rect x="58" y="47" width="12" height="8" fill="url(#zip)" />
  <rect x="58" y="59" width="12" height="8" fill="url(#zip)" />
  <rect x="58" y="71" width="12" height="8" fill="url(#zip)" />
  <rect x="58" y="83" width="12" height="8" fill="url(#zip)" />
  <!-- 加密锁符号 | Lock symbol for encryption -->
  <circle cx="64" cy="28" r="9" fill="none" stroke="#fff" stroke-width="3" />
  <rect x="56" y="25" width="16" height="12" rx="2" ry="2" fill="#fff" />
  <!-- 应用名称文字 | Text ARK -->
  <text x="64" y="108" font-family="sans-serif" font-size="16" font-weight="bold"
        fill="#fff" text-anchor="middle" opacity="0.9">ARK</text>
</svg>'''

if __name__ == "__main__":
    import os
    # 获取当前脚本所在目录 | Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建输出文件路径 | Build output file path
    svg_path = os.path.join(script_dir, "arkmanager.svg")
    # 写入SVG内容到文件 | Write SVG content to file
    with open(svg_path, "w") as f:
        f.write(SVG_ICON)
    print(f"Icon saved to: {svg_path}")
