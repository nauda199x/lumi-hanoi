#!/usr/bin/env python3
"""Static acceptance checks for issue #22 / Prestige V8.1A."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/media/prestige/manifest.v8.json"
PAGE = ROOT / "lumi-prestige/index.html"
EXPECTED = {
    ("P1", "Tầng 2–19, 21–22, 24–28"): ("p1-t02-19-21-22-24-28.webp", "p1-tang-2-19-21-22-24-28", 2400, 3200),
    ("P1", "Tầng 20"): ("p1-t20.webp", "p1-tang-20", 2400, 3200),
    ("P1", "Tầng 23"): ("p1-t23.webp", "p1-tang-23", 2400, 3200),
    ("P1", "Tầng 29"): ("p1-t29.webp", "p1-tang-29", 2400, 3200),
    ("P2", "Tầng 2–12, 14–19, 21–28"): ("p2-t02-12-14-19-21-28.webp", "p2-tang-2-12-14-19-21-28", 2400, 3201),
    ("P2", "Tầng 13"): ("p2-t13.webp", "p2-tang-13", 2400, 3200),
    ("P2", "Tầng 20"): ("p2-t20.webp", "p2-tang-20", 2400, 3200),
    ("P2", "Tầng 29"): ("p2-t29.webp", "p2-tang-29", 2400, 3200),
}

class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self.sections = {}; self.stack = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.stack.append((tag, a))
        if tag == "section" and "floor-plan-section" in a.get("class", "").split():
            self.sections[a["id"]] = {"section": a, "h2": [], "img": [], "link": [], "caption": []}
        if not self.sections: return
        current = next((x for x in reversed(self.stack) if x[0] == "section" and x[1].get("id") in self.sections), None)
        if current and tag in {"h2", "img", "a", "figcaption"}:
            if tag == "img": self.sections[current[1]["id"]]["img"].append(a)
            elif tag == "a": self.sections[current[1]["id"]]["link"].append(a)
    def handle_data(self, data):
        current = next((x for x in reversed(self.stack) if x[0] == "section" and x[1].get("id") in self.sections), None)
        if current:
            active = self.stack[-1][0] if self.stack else ""
            if active in {"h2", "figcaption"}: self.sections[current[1]["id"]]["h2" if active == "h2" else "caption"].append(data.strip())
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag: del self.stack[i:]; break

def fail(message): print(f"FAIL: {message}", file=sys.stderr); raise SystemExit(1)

data = json.loads(MANIFEST.read_text())
assets = data.get("assets", [])
if data.get("version") != "8.1A" or len(assets) != 8: fail("manifest must contain exactly eight V8.1A assets")
ids = [x["source"]["drive_file_id"] for x in assets]
if len(set(ids)) != 8 or not all(re.fullmatch(r"[A-Za-z0-9_-]{20,}", x) for x in ids): fail("eight distinct Drive IDs are required")
paths = [x["local_file"] for x in assets]
if len(set(paths)) != 8: fail("each Drive ID must map to a distinct local file")
if len({hashlib.sha256((ROOT / x).read_bytes()).hexdigest() for x in paths}) != 8: fail("the eight local drawings must have distinct contents")
actual = {(x["tower"], x["floor_group"]): (Path(x["local_file"]).name, x["anchor"], x["width"], x["height"]) for x in assets}
if actual != EXPECTED: fail("manifest tower/floor mapping differs from the approved eight groups")
parser = AuditParser(); html = PAGE.read_text(); parser.feed(html)
if set(parser.sections) != {x[1] for x in EXPECTED.values()}: fail("rendered floor-group sections do not match manifest anchors")
for asset in assets:
    section = parser.sections[asset["anchor"]]; images = section["img"]; links = section["link"]
    if section["section"].get("data-tower") != asset["tower"] or section["section"].get("data-floor-group") != asset["floor_group"]: fail(f"wrong rendered group metadata: {asset['anchor']}")
    if len(images) != 1 or len(links) != 1: fail(f"section must render one linked drawing: {asset['anchor']}")
    image, link = images[0], links[0]; url = "/" + asset["local_file"]
    required_alt = ("mã căn", "loại phòng ngủ", "NFA", "GFA", "chú giải")
    if image.get("src") != url or link.get("href") != url or "data-lightbox" not in link: fail(f"full-resolution lightbox mismatch: {asset['anchor']}")
    if (image.get("width"), image.get("height")) != (str(asset["width"]), str(asset["height"])): fail(f"intrinsic dimensions mismatch: {asset['anchor']}")
    if image.get("loading") != "lazy" or image.get("decoding") != "async" or not all(x in image.get("alt", "") for x in required_alt): fail(f"image accessibility/performance mismatch: {asset['anchor']}")
    if not "".join(section["h2"]).strip() or not "".join(section["caption"]).strip(): fail(f"missing H2 or caption: {asset['anchor']}")
if "lumi-prestige-typical-floor.webp" in html: fail("old generic Prestige plan must not render")
print("PASS: 8 Drive IDs → 8 distinct files → approved P1/P2 groups → 8 rendered anchored sections")
