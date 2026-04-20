#!/usr/bin/env python3
"""
build_book.py — 全书构建脚本

功能：
1. 按固定顺序合并所有章节与附录为 dist/全书.md
2. 在关键篇界插入篇间过渡段落
3. 合并稿最前加入封面（含作者 Austin）与阅读导航
4. 渲染 dist/全书.html（PDF 向，对齐"花叔 Claude Code 橙皮书"风格）
5. 调用本机 Chrome/Chromium/Edge headless --print-to-pdf 生成 dist/全书.pdf
6. 生成 dist/全书.epub（ePub 向，针对微信读书排版优化）
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import markdown
from markdown.extensions.toc import TocExtension
from pygments.formatters import HtmlFormatter

# ── 路径配置 ──────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = ROOT / "chapters"
APPENDIX_DIR = ROOT / "appendix"
ASSETS_DIR = ROOT / "assets"
DIST_DIR = ROOT / "dist"

# ── 图书元信息 ────────────────────────────────────────────────────

BOOK_TITLE = "AI Coding 工程化"
BOOK_SUBTITLE_CN = "从 Prompt 到 Harness 的团队实战手册"
BOOK_SUBTITLE_EN = "Prompt · Context · Harness"
BOOK_AUTHOR = "Austin"
BOOK_VERSION = "2026 春 · v1.0"
BOOK_LANG = "zh-CN"

# ── 章节顺序 ──────────────────────────────────────────────────────

CHAPTER_ORDER = [
    "00-前言.md",
    "01-地图-三代杠杆.md",
    "02-能力边界-任务分类.md",
    "03-prompt-骨架模板.md",
    "04-prompt-反模式与资产化.md",
    "05-context-包裹顺序.md",
    "06-context-rag纪律.md",
    "07-context-代码场景.md",
    "08-harness-最小五要素.md",
    "09-harness-团队规范即缰绳.md",
    "10-harness-评测与黄金用例集.md",
    "11-模型-能力地图.md",
    "12-模型-组合使用.md",
    "13-token-花在哪与省钱矩阵.md",
    "14-token-风险边界与总成本.md",
    "15-结语.md",
]

APPENDIX_ORDER = [
    "A-检查清单.md",
    "B-延伸阅读.md",
    "C-术语扩展.md",
]

# ── 章节末尾装饰：极简回纹 ─────────────────────────────────────
# 3 个嵌套方块 (回 字纹) + 两侧橙色细线，纯 inline SVG，PDF 矢量 / ePub 兼容

ORNAMENT = """
<div class="ornament">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 22" width="180" height="22">
  <g stroke="#E67E22" stroke-width="0.9" fill="none" stroke-linecap="round">
    <line x1="0" y1="11" x2="55" y2="11"/>
    <line x1="125" y1="11" x2="180" y2="11"/>
  </g>
  <g stroke="#E67E22" stroke-width="0.9" fill="none" stroke-linejoin="miter">
    <rect x="65" y="2" width="14" height="18"/>
    <rect x="69" y="6" width="6" height="10"/>
    <rect x="83" y="2" width="14" height="18"/>
    <rect x="87" y="6" width="6" height="10"/>
    <rect x="101" y="2" width="14" height="18"/>
    <rect x="105" y="6" width="6" height="10"/>
  </g>
</svg>
</div>
"""

# ── 篇间过渡 ──────────────────────────────────────────────────────

TRANSITIONS: dict[str, str] = {
    # 02 之后进入 Prompt 篇（03~04）
    "02-能力边界-任务分类.md": """
---

> **【篇间过渡：从"知道档位"到"会写 Prompt"】**
>
> 你现在能 60 秒把任务分到 A / B / C / D 四档，知道"这件事该用几代杠杆"。
> 接下来 2 章进入 **Prompt 篇**——把"写 Prompt"从个人手艺沉淀为团队资产：
> 先把骨架搭起来（03），再把它版本化、A/B 化、团队化（04）。

---
""",
    # 04 之后进入 Context 篇（05~07）
    "04-prompt-反模式与资产化.md": """
---

> **【篇间过渡：从"一句 Prompt"到"一份上下文"】**
>
> Prompt 的上限由"你把信息组织得多清楚"决定。
> 接下来 3 章进入 **Context 篇**：6 段包裹顺序（05）、RAG 纪律（06）、代码场景的特殊处理（07）。
> 这是从第一代到第二代的跨越——从"写好话"到"摆好场景"。

---
""",
    # 07 之后进入 Harness 篇（08~10）
    "07-context-代码场景.md": """
---

> **【篇间过渡：从"摆好场景"到"搭好流水线"】**
>
> 你已经会组织一次对话的完整 Context。
> 但团队的 AI 使用不能"每次重来一遍"——接下来 3 章进入 **Harness 篇**：
> 最小五件套（08）、把团队规范变成缰绳（09）、用黄金集评测护住质量（10）。
> 这是从第二代到第三代的跨越——从"摆场景"到"建制度"。

---
""",
    # 10 之后进入 模型篇（11~12）
    "10-harness-评测与黄金用例集.md": """
---

> **【篇间过渡：从"会用 AI"到"会选 AI"】**
>
> 你现在有了一套"能跑、能评、能护"的 AI 工作台。
> 接下来 2 章进入 **模型篇**：2026 年的能力地图（11）+ 组合使用（12）。
> 一个团队同时用 3~5 个模型才是默认状态——"统一用一个"已经过时。

---
""",
    # 12 之后进入 Token 篇（13~14）
    "12-模型-组合使用.md": """
---

> **【篇间过渡：从"选对模型"到"算对总账"】**
>
> 你已经知道怎么为每个阶段挑合适的模型。
> 最后 2 章进入 **Token 篇**：token 花在哪 + Cache 怎么省钱（13）、"省了反而更贵"的 3 个陷阱 + 总成本公式（14）。
> 这一篇讲的不是"抠钱"，是"把钱花得值"。

---
""",
    # 14 之后进入 结语
    "14-token-风险边界与总成本.md": """
---

> **【篇间过渡：从"所有技巧"到"三年之后"】**
>
> 你已走完三代杠杆 + 模型 + Token 的全部地图。
> 最后一章回答一个更远的问题：**如果三年后出现"下一代杠杆"，这本书的哪些东西还能用？**

---
""",
}

# ── 封面 + 阅读导航 ───────────────────────────────────────────────

COVER_MD = f"""# {BOOK_TITLE}

> **{BOOK_SUBTITLE_CN}**
>
> {BOOK_SUBTITLE_EN}

**作者**：{BOOK_AUTHOR}  
**版本**：{BOOK_VERSION}

---

"""

READING_GUIDE_MD = """# 阅读导航

本书围绕**三代杠杆**展开：

> **Prompt Engineering → Context Engineering → Harness Engineering**

再配合**能力边界、模型篇、Token 篇、评测**4 个横向专题——帮你不只"用好 AI"，还能**用得准、用得稳、用得划算**。

## 全书结构

| 篇 | 章节 | 核心问题 |
| --- | --- | --- |
| **开篇** | 前言、第一章、第二章 | 你是谁？这本书解决什么问题？任务该分几档？ |
| **Prompt** | 第三章、第四章 | 怎么写好一条指令？怎么把 Prompt 沉淀为团队资产？ |
| **Context** | 第五章 ~ 第七章 | 怎么组织一次对话里模型看到的所有信息？ |
| **Harness** | 第八章 ~ 第十章 | 怎么让 AI 的输入输出都有制度保障？ |
| **模型** | 第十一章 ~ 第十二章 | 2026 年怎么选模型？怎么让 5 个模型分工？ |
| **Token** | 第十三章 ~ 第十四章 | 钱花在哪？怎么省？什么时候不能省？ |
| **结语 & 附录** | 结语、附录 A/B/C | 总结回顾、速查工具、延伸阅读、术语 |

## 3 种读法

- **顺序读**：篇间有过渡段，一气呵成。
- **跳读**：每章开头有"一句话交付"，判断是否需要读。
  - 已经熟悉 Prompt？直接从**第五章**起读。
  - 最关心成本？直接从**第十三章**起读。
  - 想搭工程化流程？直接从**第八章**起读。
- **当工具书**：附录 A 的 7 张检查清单可以**打印贴在工位**。

## 贯穿案例：mini-library

全书使用一个虚构项目 `mini-library`（Java 17 + Spring Boot 3 + MyBatis）演示所有示例。
具体技术栈、硬约束、用例定义、seed 数据见 `meta/CASESPEC.md`。

---

"""

# ── HTML 模板（PDF 向 · 对齐"花叔橙皮书"风格） ──────────────────

PDF_CSS = """
:root {
    --orange: #E67E22;
    --orange-light: #FDF2E9;
    --text: #222;
    --muted: #555;
    --border: #E5E5E5;
    --code-bg: #F7F7F7;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html { font-size: 15px; }
body {
    font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC",
                 "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", serif;
    color: var(--text);
    line-height: 1.85;
    max-width: 760px;
    margin: 0 auto;
    padding: 2.5rem 1.75rem 4rem;
    background: #fff;
}
h1, h2, h3, h4 {
    font-family: "Noto Sans SC", "Source Han Sans SC", "PingFang SC",
                 "Microsoft YaHei", sans-serif;
    color: #111;
    line-height: 1.3;
}
h1 {
    font-size: 1.9rem;
    margin: 3rem 0 1.2rem;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid var(--orange);
    page-break-before: always;
}
h1:first-of-type { page-break-before: avoid; }
h2 {
    font-size: 1.35rem;
    margin: 2rem 0 0.7rem;
    color: var(--orange);
    border-left: 4px solid var(--orange);
    padding-left: 0.8rem;
}
h3 { font-size: 1.12rem; margin: 1.3rem 0 0.5rem; }
h4 { font-size: 1rem; margin: 1rem 0 0.4rem; color: var(--muted); }
p { margin-bottom: 0.75rem; text-align: justify; }
ul, ol { margin: 0.3rem 0 0.8rem 1.6rem; }
li { margin-bottom: 0.25rem; }
strong { color: #000; font-weight: 700; }
em { color: var(--muted); }
hr {
    border: none;
    border-top: 1px dashed var(--border);
    margin: 1.8rem 0;
}
blockquote {
    border-left: 4px solid var(--orange);
    background: var(--orange-light);
    padding: 0.8rem 1rem;
    margin: 1rem 0;
    border-radius: 0 6px 6px 0;
    color: #5A3E1B;
}
blockquote p { margin-bottom: 0.3rem; }
code {
    font-family: "JetBrains Mono", "Fira Code", "SF Mono", Consolas, monospace;
    font-size: 0.88em;
    background: var(--code-bg);
    padding: 0.1em 0.4em;
    border-radius: 3px;
    color: #C7254E;
}
pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-left: 4px solid var(--orange);
    border-radius: 4px;
    padding: 0.9rem 1rem;
    overflow-x: auto;
    margin: 0.8rem 0 1rem;
    font-size: 0.85em;
    line-height: 1.55;
    page-break-inside: avoid;
}
pre code {
    background: none;
    padding: 0;
    color: #333;
    font-size: inherit;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.8rem 0 1rem;
    font-size: 0.92em;
    page-break-inside: avoid;
}
th, td {
    border: 1px solid var(--border);
    padding: 0.45rem 0.65rem;
    vertical-align: top;
}
th {
    background: var(--orange-light);
    font-weight: 600;
    color: #111;
}
tr:nth-child(even) { background: #FAFAFA; }
img {
    max-width: 100%;
    margin: 1rem auto;
    display: block;
    border: 1px solid var(--border);
    border-radius: 4px;
}
.toc {
    background: var(--orange-light);
    border: 1px solid var(--orange);
    border-radius: 8px;
    padding: 1.2rem 1.8rem;
    margin: 2rem 0;
    page-break-after: always;
}
.toc h2 {
    border: none;
    padding: 0;
    margin: 0 0 0.8rem;
    color: var(--orange);
}
.toc ul { list-style: none; padding-left: 0; margin: 0; }
.toc ul ul { padding-left: 1.3rem; }
.toc li { margin-bottom: 0.3rem; }
.toc a { color: var(--text); text-decoration: none; }
.toc a:hover { color: var(--orange); }

/* 封面样式 · 真书排版 */
.cover {
    text-align: center;
    min-height: 95vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0;
    page-break-after: always;
}
.cover-top { flex: 1.2; }
.cover-spacer { flex: 1.6; }
.cover-title {
    font-size: 3.6rem;
    font-weight: 700;
    letter-spacing: 0.3rem;
    color: #111;
    border: none;
    padding: 0;
    margin: 0;
    line-height: 1.2;
    page-break-before: avoid;
}
.cover-rule {
    width: 120px;
    height: 2px;
    background: var(--orange);
    margin: 1.4rem auto 1.4rem;
}
.cover-subtitle-cn {
    font-size: 1.15rem;
    color: #444;
    letter-spacing: 0.08rem;
    margin-bottom: 0.5rem;
}
.cover-subtitle-en {
    font-size: 1rem;
    color: var(--orange);
    letter-spacing: 0.15rem;
    font-style: italic;
    font-family: "Georgia", "Times New Roman", serif;
}
.cover-author {
    font-size: 1.15rem;
    color: #111;
    letter-spacing: 0.2rem;
    margin-bottom: 0.4rem;
}
.cover-version {
    font-size: 0.85rem;
    color: var(--muted);
    letter-spacing: 0.1rem;
}

/* 流程图容器 */
.figure {
    text-align: center;
    margin: 1.4rem auto 1.2rem;
    page-break-inside: avoid;
}
.figure svg {
    max-width: 100%;
    height: auto;
}
.figure-caption {
    font-size: 0.86em;
    color: var(--muted);
    margin-top: 0.3rem;
}

/* 章末极简回纹（不单独触发分页，让下一章的 h1 去触发） */
.ornament {
    text-align: center;
    margin: 2.8rem auto 2rem;
    page-break-inside: avoid;
}
.ornament svg {
    width: 180px;
    height: 22px;
    display: inline-block;
}

@media print {
    body { padding: 0 2rem; max-width: 100%; font-size: 11.5pt; }
    h1 { font-size: 17pt; page-break-before: always; }
    h1:first-of-type { page-break-before: avoid; }
    pre, table, blockquote { page-break-inside: avoid; }
    a { color: var(--text); text-decoration: none; }
}
"""

# Pygments friendly 主题 CSS，用于 .highlight 代码块着色
PYGMENTS_CSS = HtmlFormatter(style="friendly").get_style_defs(".highlight")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{content}
</body>
</html>
"""

# ── 工具函数 ──────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    if not path.exists():
        print(f"[warn] 文件不存在：{path}")
        return ""
    return path.read_text(encoding="utf-8")


def find_browser() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        found = shutil.which(c)
        if found:
            return found
        if os.path.isfile(c):
            return c
    return None


def rewrite_image_paths(md: str) -> str:
    """把相对 ../assets/ 的引用重写成 dist/ 下可见的 assets/"""
    return md.replace("](../assets/", "](assets/")


# ── 合并 ──────────────────────────────────────────────────────────

def merge_markdown() -> str:
    parts: list[str] = [COVER_MD, READING_GUIDE_MD]
    for filename in CHAPTER_ORDER:
        content = read_file(CHAPTERS_DIR / filename)
        if content:
            parts.append(content)
            parts.append(ORNAMENT)
        if filename in TRANSITIONS:
            parts.append(TRANSITIONS[filename])
    parts.append("\n---\n\n# 附录\n\n")
    for filename in APPENDIX_ORDER:
        content = read_file(APPENDIX_DIR / filename)
        if content:
            parts.append(content)
            parts.append(ORNAMENT)
    return "\n\n".join(parts)


# ── HTML 渲染 ────────────────────────────────────────────────────

def markdown_to_html(md_text: str) -> tuple[str, str]:
    md_text = rewrite_image_paths(md_text)
    extensions = [
        "tables",
        "fenced_code",
        "codehilite",
        TocExtension(title="目录", toc_depth="1-2", anchorlink=True),
    ]
    extension_configs = {
        "codehilite": {"css_class": "highlight", "guess_lang": False},
    }
    md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
    html_body = md.convert(md_text)
    toc_html = getattr(md, "toc", "")
    return html_body, toc_html


def wrap_pdf_html(body: str, toc: str) -> str:
    """PDF 向：加封面 + TOC"""
    cover_html = f"""
<div class="cover">
  <div class="cover-top"></div>
  <h1 class="cover-title">{BOOK_TITLE}</h1>
  <div class="cover-rule"></div>
  <div class="cover-subtitle-cn">{BOOK_SUBTITLE_CN}</div>
  <div class="cover-subtitle-en">{BOOK_SUBTITLE_EN}</div>
  <div class="cover-spacer"></div>
  <div class="cover-author">{BOOK_AUTHOR}　著</div>
  <div class="cover-version">{BOOK_VERSION}</div>
</div>
"""
    toc_section = f'<div class="toc"><h2>目录</h2>{toc}</div>' if toc else ""
    # body 开头是 COVER_MD 渲染出来的"封面段"：h1(书名) + blockquote(副标) + p(作者/版本) + hr。
    # 定位到含书名字面的首个 h1，非贪婪匹配到这一段的首个 <hr/>，精确剥离，避免误伤前言的 h1 + blockquote + hr。
    body_after_cover = re.sub(
        r'^<h1[^>]*>.*?' + re.escape(BOOK_TITLE) + r'.*?</h1>.*?<hr\s*/?>\s*',
        '',
        body,
        count=1,
        flags=re.DOTALL,
    )
    content = cover_html + toc_section + body_after_cover
    return HTML_TEMPLATE.format(
        lang=BOOK_LANG,
        title=BOOK_TITLE,
        css=PDF_CSS + "\n" + PYGMENTS_CSS,
        content=content,
    )


# ── PDF 生成 ──────────────────────────────────────────────────────

def generate_pdf(html_path: Path, pdf_path: Path) -> bool:
    browser = find_browser()
    if not browser:
        print("[warn] 未找到 Chrome/Chromium/Edge，跳过 PDF 生成")
        return False
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path.resolve()}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
            return True
        print(f"[warn] PDF 生成失败：{result.stderr[:400]}")
        return False
    except Exception as e:
        print(f"[warn] PDF 生成异常：{e}")
        return False


# ── ePub 生成（微信读书友好） ──────────────────────────────────

EPUB_CSS = """
body { font-family: "Noto Serif SC", "Songti SC", "PingFang SC", serif; line-height: 1.8; padding: 1em; }
h1 { font-size: 1.5em; margin-top: 1.5em; margin-bottom: 0.8em;
     border-bottom: 2px solid #E67E22; padding-bottom: 0.3em; }
h2 { font-size: 1.25em; margin-top: 1.2em; color: #E67E22; }
h3 { font-size: 1.1em; margin-top: 1em; }
h4 { font-size: 1em; margin-top: 0.8em; color: #666; }
p  { margin: 0.5em 0; text-align: justify; }
blockquote { border-left: 4px solid #E67E22; background: #FDF2E9;
             padding: 0.6em 0.9em; margin: 0.8em 0;
             border-radius: 0 4px 4px 0; color: #5A3E1B; }
code { font-family: "JetBrains Mono", monospace; background: #F5F5F5;
       padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.9em;
       color: #C7254E; word-break: break-all; }
pre { background: #F7F7F7; border-left: 4px solid #E67E22;
      padding: 0.7em 0.9em; margin: 0.7em 0;
      font-size: 0.85em; overflow-x: auto;
      white-space: pre-wrap; word-wrap: break-word; }
pre code { background: none; color: #333; padding: 0; }
table { width: 100%; border-collapse: collapse; margin: 0.7em 0;
        font-size: 0.9em; display: block; overflow-x: auto; }
th, td { border: 1px solid #DDD; padding: 0.3em 0.5em; }
th { background: #FDF2E9; }
img { max-width: 100%; margin: 0.8em auto; display: block; }
strong { color: #000; }
hr { border: none; border-top: 1px dashed #CCC; margin: 1.5em 0; }
ul, ol { margin: 0.3em 0 0.5em 1.5em; }
li { margin: 0.2em 0; }
.ornament { text-align: center; margin: 2em auto 1em; }
.ornament svg { width: 160px; height: 20px; }
.figure { text-align: center; margin: 1.2em auto 1em; }
.figure svg { max-width: 100%; height: auto; }
.figure-caption { font-size: 0.85em; color: #666; margin-top: 0.3em; }
"""


def generate_epub(md_chapters: list[tuple[str, str]], epub_path: Path) -> bool:
    """生成 ePub（每个 md 片段一章）"""
    try:
        from ebooklib import epub
    except ImportError:
        print("[warn] 未安装 ebooklib（`pip install EbookLib`），跳过 ePub")
        return False

    book = epub.EpubBook()
    book.set_identifier(f"ai-coding-engineering-{uuid.uuid4().hex[:8]}")
    book.set_title(BOOK_TITLE)
    book.set_language(BOOK_LANG)
    book.add_author(BOOK_AUTHOR)
    book.add_metadata("DC", "description", BOOK_SUBTITLE_CN + " · " + BOOK_SUBTITLE_EN)
    book.add_metadata("DC", "publisher", "自出版")

    # 内嵌 CSS
    css = epub.EpubItem(
        uid="style",
        file_name="style/book.css",
        media_type="text/css",
        content=(EPUB_CSS + "\n" + PYGMENTS_CSS).encode("utf-8"),
    )
    book.add_item(css)

    # 内嵌图片（assets/images/*.png）
    images_added = set()
    images_dir = ASSETS_DIR / "images"
    if images_dir.exists():
        for img in images_dir.glob("*"):
            if img.is_file() and img.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
                rel_name = f"assets/images/{img.name}"
                media = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                }[img.suffix.lower()]
                book.add_item(epub.EpubImage(
                    uid=f"img_{img.stem}",
                    file_name=rel_name,
                    media_type=media,
                    content=img.read_bytes(),
                ))
                images_added.add(rel_name)

    spine: list = ["nav"]
    toc_list: list = []

    for idx, (title, md_text) in enumerate(md_chapters):
        html_body, _ = markdown_to_html(md_text)
        chap_html = (
            f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{BOOK_LANG}"><head>'
            f'<meta charset="UTF-8"/><title>{title}</title>'
            f'<link rel="stylesheet" type="text/css" href="style/book.css"/></head>'
            f'<body>{html_body}</body></html>'
        )
        chap = epub.EpubHtml(
            title=title,
            file_name=f"chapter_{idx:02d}.xhtml",
            lang=BOOK_LANG,
        )
        chap.content = chap_html
        chap.add_item(css)
        book.add_item(chap)
        spine.append(chap)
        toc_list.append(chap)

    book.toc = tuple(toc_list)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    epub.write_epub(str(epub_path), book)
    return True


def split_for_epub() -> list[tuple[str, str]]:
    """按章节拆分，用于 ePub 每章独立。封面 + 导航 作为第 0 章。"""
    chapters: list[tuple[str, str]] = []
    # 封面 + 导航合并为第一章
    chapters.append(("封面与阅读导航", COVER_MD + "\n\n" + READING_GUIDE_MD))

    for fn in CHAPTER_ORDER:
        content = read_file(CHAPTERS_DIR / fn)
        if not content:
            continue
        # 从 md 里提取 # 开头的第一行作为标题
        m = re.search(r"^# (.+)$", content, re.M)
        title = m.group(1).strip() if m else fn
        # 重写图片路径 + 追加回纹
        content = rewrite_image_paths(content) + "\n\n" + ORNAMENT
        chapters.append((title, content))

    # 附录
    for fn in APPENDIX_ORDER:
        content = read_file(APPENDIX_DIR / fn)
        if not content:
            continue
        m = re.search(r"^# (.+)$", content, re.M)
        title = m.group(1).strip() if m else fn
        content = rewrite_image_paths(content) + "\n\n" + ORNAMENT
        chapters.append((title, content))
    return chapters


# ── 拷贝静态资源到 dist ────────────────────────────────────

def copy_assets() -> None:
    src = ASSETS_DIR
    dst = DIST_DIR / "assets"
    if src.exists():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


# ── main ──────────────────────────────────────────────────────────

def main() -> None:
    html_only = "--html-only" in sys.argv
    no_epub = "--no-epub" in sys.argv
    no_pdf = "--no-pdf" in sys.argv or html_only

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()

    # 1) 合并 Markdown
    print("[1/4] 合并 Markdown ...")
    full_md = merge_markdown()
    md_path = DIST_DIR / "全书.md"
    md_path.write_text(full_md, encoding="utf-8")
    zh = sum(1 for c in full_md if "\u4e00" <= c <= "\u9fff")
    print(f"      -> {md_path}  汉字 {zh:,}")

    # 2) 渲染 HTML
    print("[2/4] 渲染 HTML（PDF 向）...")
    body, toc = markdown_to_html(full_md)
    full_html = wrap_pdf_html(body, toc)
    html_path = DIST_DIR / "全书.html"
    html_path.write_text(full_html, encoding="utf-8")
    print(f"      -> {html_path}")

    # 3) PDF
    if no_pdf:
        print("[3/4] 跳过 PDF（--no-pdf / --html-only）")
    else:
        print("[3/4] 生成 PDF ...")
        pdf_path = DIST_DIR / "全书.pdf"
        if generate_pdf(html_path, pdf_path):
            print(f"      -> {pdf_path}  {pdf_path.stat().st_size/1024:.1f} KB")
        else:
            print("      (未生成)")

    # 4) ePub
    if no_epub:
        print("[4/4] 跳过 ePub（--no-epub）")
    else:
        print("[4/4] 生成 ePub（微信读书向）...")
        epub_path = DIST_DIR / "全书.epub"
        md_chapters = split_for_epub()
        if generate_epub(md_chapters, epub_path):
            print(f"      -> {epub_path}  {epub_path.stat().st_size/1024:.1f} KB")

    print("\n构建完成。")


if __name__ == "__main__":
    main()
