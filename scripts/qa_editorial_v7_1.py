#!/usr/bin/env python3
"""V7.1 responsive editorial layout regression checks."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
HTML = sorted(ROOT.glob("**/index.html"))
OVERVIEW = {
    "tong-quan-lumi-hanoi/index.html", "lumi-signature/index.html",
    "lumi-prestige/index.html", "lumi-elite/index.html",
    "tien-ich-lumi-hanoi/index.html", "tien-do-lumi-hanoi/index.html",
    "mat-bang-lumi-hanoi/index.html", "layout-can-ho-lumi-prestige/index.html",
}
errors: list[str] = []

def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)

# Every article composition declares exactly one reusable width mode and its real sidebar state.
for path in HTML:
    text = path.read_text(encoding="utf-8")
    if 'article-layout' not in text:
        continue
    rel = path.relative_to(ROOT).as_posix()
    has_sidebar = '<aside class="side-nav"' in text
    require(('reading-shell' in text) ^ ('editorial-shell' in text),
            f"{rel}: article layout needs exactly one page-type shell")
    require(('article-layout--with-sidebar' in text) == has_sidebar,
            f"{rel}: sidebar modifier does not match actual sidebar markup")
    if rel in OVERVIEW:
        require('editorial-shell' in text and 'editorial-wide' in text,
                f"{rel}: overview/reference page is constrained to reading width")
    if rel.startswith('tin-tuc/'):
        require('reading-shell' in text,
                f"{rel}: long-form news page lacks a reading shell")

# The shared CSS must center each composition and collapse actual sidebars, without global wide H2s.
for token in (".reading-shell.article-layout--centered", ".editorial-shell.article-layout--with-sidebar",
              ".article-layout--with-sidebar", "--reading: 780px", "--editorial: 1080px"):
    require(token in CSS, f"site.css: missing shared layout rule {token}")
require(re.search(r"@media\s*\(max-width:\s*760px\)", CSS) is not None,
        "site.css: missing 760px editorial breakpoint")
require(re.search(r"\.article-layout--with-sidebar[\s\S]{0,500}grid-template-columns:\s*minmax\(0,\s*1fr\)",
                  CSS[CSS.rfind("/* V7.1"):]) is not None,
        "site.css: sidebar composition does not collapse to one column")
require("position: static" in CSS[CSS.rfind("/* V7.1"):],
        "site.css: mobile side navigation may remain sticky")
require("overflow-x: clip" in CSS[CSS.rfind("/* V7.1"):],
        "site.css: mobile overflow safeguard is missing")
require(re.search(r"\.article h2\s*\{[^}]*font-size:\s*clamp\(2\.25rem,\s*3vw,\s*2\.75rem\)", CSS) is not None,
        "site.css: article H2 must use the controlled 36–44px fluid scale")

# Preserve canonical values from the branch base and forbid query-bearing internal links.
for path in HTML:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"]+)"', text):
        require(not (href.startswith('/') and '?' in href), f"{rel}: query parameter on internal link: {href}")
    try:
        base = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout
    except subprocess.CalledProcessError:
        continue
    canonical = re.findall(r'<link rel="canonical" href="([^"]+)"', text)
    base_canonical = re.findall(r'<link rel="canonical" href="([^"]+)"', base)
    require(canonical == base_canonical, f"{rel}: canonical changed from branch base")

# Protect V8.1D catalogue architecture and fit-first lightbox behavior.
prestige = (ROOT / "layout-can-ho-lumi-prestige/index.html").read_text(encoding="utf-8")
js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
for token in ("prestige-layout-page", "layout-card-grid", "layout-preview", "layout-view-action"):
    require(token in prestige, f"Prestige catalogue markup lost {token}")
for token in ("lightbox-stage", "is-fit", "is-zoomed"):
    require(token in CSS, f"Prestige fit-first lightbox CSS lost {token}")
require("data-layout-filter" in prestige and "data-lightbox" in prestige,
        "Prestige catalogue filtering/lightbox hooks are missing")
require("lightbox" in js and "is-fit" in js, "Prestige lightbox JavaScript behavior is missing")

if errors:
    print("V7.1 editorial responsive QA: FAIL")
    print("\n".join(f"- {error}" for error in errors))
    sys.exit(1)
print(f"V7.1 editorial responsive QA: PASS ({len(HTML)} pages checked)")
