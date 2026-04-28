#!/usr/bin/env python3
"""从 assets/images/fig-1-1-harness.svg 导出 fig-1-1-harness.png（2× 栅格，供 PDF/ePub 使用）。

依赖本机 Chrome/Chromium（与 build_book.py 相同路径探测）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "assets" / "images" / "fig-1-1-harness.svg"
OUT_PNG = ROOT / "assets" / "images" / "fig-1-1-harness.png"
# 与 viewBox 760×360 同比例，2× 分辨率
VIEW_W, VIEW_H = 1520, 720


def find_browser() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "google-chrome",
        "chromium",
    ]
    for c in candidates:
        w = shutil.which(c)
        if w:
            return w
        if os.path.isfile(c):
            return c
    return None


def main() -> int:
    if not SVG_PATH.is_file():
        print(f"[err] 缺少 {SVG_PATH}", file=sys.stderr)
        return 1
    chrome = find_browser()
    if not chrome:
        print("[err] 未找到 Chrome/Chromium，无法导出 PNG", file=sys.stderr)
        return 1

    svg = SVG_PATH.read_text(encoding="utf-8")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"/>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{VIEW_W}px;height:{VIEW_H}px;background:#fff;overflow:hidden}}
svg{{display:block;width:{VIEW_W}px;height:{VIEW_H}px}}
</style></head><body>
{svg}
</body></html>"""

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".html",
        delete=False,
        dir=ROOT / "scripts",
    ) as f:
        f.write(html)
        tmp_html = Path(f.name)

    try:
        url = tmp_html.as_uri()
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            f"--window-size={VIEW_W},{VIEW_H}",
            f"--screenshot={OUT_PNG}",
            url,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not OUT_PNG.is_file() or OUT_PNG.stat().st_size == 0:
            print(r.stderr or r.stdout or "screenshot failed", file=sys.stderr)
            return 1
        print(f"OK -> {OUT_PNG} ({OUT_PNG.stat().st_size} bytes)")
        return 0
    finally:
        tmp_html.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
