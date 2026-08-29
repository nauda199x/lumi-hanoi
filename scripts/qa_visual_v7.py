#!/usr/bin/env python3
"""Static, standard-library V7 visual/SEO safety checks."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse, parse_qs
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "lumi-hanoi.com"
IMPORTANT = ["", "tong-quan-lumi-hanoi", "vi-tri-lumi-hanoi", "mat-bang-lumi-hanoi",
 "tien-ich-lumi-hanoi", "phap-ly-lumi-hanoi", "thiet-ke-lumi-hanoi", "tien-do-lumi-hanoi",
 "noi-that-ban-giao-lumi-hanoi", "lumi-signature", "lumi-prestige", "lumi-elite",
 "mua-ban-lumi-hanoi", "cho-thue-lumi-hanoi", "can-ho-1-phong-ngu-lumi-hanoi",
 "can-ho-2-phong-ngu-lumi-hanoi", "can-ho-3-phong-ngu-lumi-hanoi",
 "can-ho-4-phong-ngu-lumi-hanoi", "duplex-penthouse-lumi-hanoi", "tin-tuc"]
COMPETITORS = ("vinhomes.vn", "batdongsan.com.vn", "onehousing.vn")
PROHIBITED = ("đăng ký ngay", "nhận bảng giá sốc", "chỉ còn ")
INTENTIONAL_NOINDEX = {Path("admin/index.html"), Path("tin-dang-lumi-hanoi/index.html")}


def trusted_drive_ids() -> set[str]:
    """Return only Drive IDs explicitly recorded in verified source manifests."""
    ids: set[str] = set()

    floor_manifest = ROOT / "assets/data/floor-plans.json"
    if floor_manifest.is_file():
        data = json.loads(floor_manifest.read_text(encoding="utf-8"))
        for tower in data.get("towers", {}).values():
            for plan in tower.get("plans", []):
                if plan.get("driveId"):
                    ids.add(plan["driveId"])
        for record in data.get("supplemental", []):
            if record.get("sourceDriveId"):
                ids.add(record["sourceDriveId"])

    gallery_manifest = ROOT / "assets/data/signature-3d-gallery.json"
    if gallery_manifest.is_file():
        data = json.loads(gallery_manifest.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            if item.get("driveId"):
                ids.add(item["driveId"])

    return ids


TRUSTED_DRIVE_IDS = trusted_drive_ids()


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True); self.h1=0; self.ids=[]; self.links=[]; self.images=[]; self.assets=[]; self.canonicals=[]; self.noindex=False; self.legacy_redirect=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag == "body" and "data-legacy-redirect" in a: self.legacy_redirect=True
        if tag == "h1": self.h1 += 1
        if "id" in a: self.ids.append(a["id"])
        if tag == "a" and "href" in a: self.links.append((a["href"], a.get("target"), a.get("rel", "")))
        if tag == "img": self.images.append(a)
        if tag == "link" and a.get("rel") == "canonical": self.canonicals.append(a.get("href", ""))
        if tag == "link" and a.get("rel") == "stylesheet": self.assets.append(a.get("href", ""))
        if tag == "script" and a.get("src"): self.assets.append(a["src"])
        if tag == "meta" and a.get("name", "").lower() == "robots" and "noindex" in a.get("content", "").lower(): self.noindex=True


def local_file(url: str) -> Path | None:
    parsed=urlparse(url)
    if parsed.scheme in ("http", "https") or url.startswith(("mailto:", "tel:", "javascript:", "#")): return None
    path=unquote(parsed.path)
    if not path: return None
    candidate=ROOT / path.lstrip("/") if path.startswith("/") else None
    if candidate is None: return None
    if path.endswith("/"): candidate /= "index.html"
    return candidate


def is_verified_drive_thumbnail(src: str) -> bool:
    parsed = urlparse(src)
    if parsed.scheme not in ("http", "https") or parsed.netloc != "drive.google.com" or parsed.path != "/thumbnail":
        return False
    file_id = parse_qs(parsed.query).get("id", [""])[0]
    return bool(file_id and file_id in TRUSTED_DRIVE_IDS)


def is_marketplace_storage_image(src: str) -> bool:
    """Allow only the project's public listing-images bucket as first-party media."""
    parsed = urlparse(src)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "salsyqatlzapnzbcnnsr.supabase.co"
        and parsed.path.startswith("/storage/v1/object/public/listing-images/")
    )


def main() -> int:
    errors=[]; pages={}
    html_files=sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    for path in html_files:
        text=path.read_text(encoding="utf-8"); parser=PageParser(); parser.feed(text); pages[path]=parser
        relative=path.relative_to(ROOT)
        intentional_noindex=relative in INTENTIONAL_NOINDEX or (path.parent / ".marketplace-generated").is_file()
        if path.name != "404.html" and parser.noindex and not intentional_noindex: errors.append(f"noindex found: {relative}")
        if intentional_noindex and not parser.noindex: errors.append(f"expected noindex missing: {relative}")
        if parser.legacy_redirect: continue
        if path.name == "404.html" or intentional_noindex: pass
        elif len(parser.canonicals) != 1: errors.append(f"canonical count {len(parser.canonicals)}: {path.relative_to(ROOT)}")
        elif path.name == "index.html":
            rel=path.parent.relative_to(ROOT).as_posix(); expected=f"https://{HOST}/" + (f"{rel}/" if rel != "." else "")
            if parser.canonicals[0] != expected: errors.append(f"canonical changed: {path.relative_to(ROOT)} -> {parser.canonicals[0]}")
        dup={item for item in parser.ids if parser.ids.count(item)>1}
        if dup: errors.append(f"duplicate IDs {sorted(dup)}: {path.relative_to(ROOT)}")
        lower=text.lower()
        if any(domain in lower for domain in COMPETITORS): errors.append(f"competitor domain: {path.relative_to(ROOT)}")
        if any(term in lower for term in PROHIBITED): errors.append(f"prohibited sales wording: {path.relative_to(ROOT)}")
        for img in parser.images:
            src=img.get("src", "")
            verified_drive = is_verified_drive_thumbnail(src)
            marketplace_storage = is_marketplace_storage_image(src)
            if "alt" not in img: errors.append(f"image missing alt: {path.relative_to(ROOT)} {src}")
            # Verified Drive thumbnails are manifest-gated delivery exceptions.
            # Local media still requires intrinsic dimensions.
            if (not img.get("width") or not img.get("height")) and not verified_drive:
                errors.append(f"image missing dimensions: {path.relative_to(ROOT)} {src}")
            parsed=urlparse(src)
            if parsed.scheme in ("http", "https"):
                if not verified_drive and not marketplace_storage:
                    errors.append(f"external image hotlink: {path.relative_to(ROOT)} {src}")
            elif src:
                target=ROOT/src.lstrip("/") if src.startswith("/") else path.parent/src
                try: target.resolve().relative_to((ROOT/"assets/media").resolve())
                except ValueError: errors.append(f"image outside valid local media: {path.relative_to(ROOT)} {src}")
                if not target.is_file(): errors.append(f"missing image: {path.relative_to(ROOT)} {src}")
        for href,target,rel in parser.links:
            if target == "_blank" and not {"noopener","noreferrer"}.intersection(rel.split()): errors.append(f"unsafe target=_blank: {path.relative_to(ROOT)} {href}")
            parsed=urlparse(href)
            if parsed.scheme or href.startswith(("#","mailto:","tel:")): continue
            target_path=(ROOT/parsed.path.lstrip("/")) if parsed.path.startswith("/") else (path.parent/parsed.path)
            if parsed.path.endswith("/"): target_path /= "index.html"
            if parsed.path and not target_path.is_file(): errors.append(f"broken internal link: {path.relative_to(ROOT)} {href}")
        for asset in parser.assets:
            asset_path=unquote(urlparse(asset).path)
            target_path=ROOT/asset_path.lstrip("/") if asset_path.startswith("/") else path.parent/asset_path
            if not target_path.is_file(): errors.append(f"missing CSS/JS: {path.relative_to(ROOT)} {asset}")
    for slug in IMPORTANT:
        p=ROOT/(slug or ".")/"index.html"
        if not p.is_file(): errors.append(f"important page missing: /{slug}/")
        elif pages[p].h1 != 1: errors.append(f"important page H1 count {pages[p].h1}: /{slug}/")
    home=(ROOT/"index.html").read_text(encoding="utf-8")
    for required in ("/vi-tri-lumi-hanoi/", "/tien-do-lumi-hanoi/", "/mua-ban-lumi-hanoi/", "/cho-thue-lumi-hanoi/", "/ky-gui-lumi-hanoi/", "https://kuula.co/post/5y19m"):
        if required not in home: errors.append(f"homepage V7 module link missing: {required}")
    if home.count('fetchpriority="high"') != 1: errors.append("homepage must contain exactly one high-priority image")
    sitemap=ET.parse(ROOT/"sitemap.xml")
    for loc in sitemap.findall(".//{*}loc"):
        parsed=urlparse(loc.text or "")
        if parsed.netloc != HOST: errors.append(f"unexpected sitemap host: {loc.text}")
        target=ROOT/parsed.path.lstrip("/")
        if parsed.path.endswith("/"): target /= "index.html"
        if not target.is_file(): errors.append(f"sitemap URL missing locally: {loc.text}")
    for script in ("qa_seo_v5.py", "qa_seo_v5_1.py", "qa_seo_v6.py"):
        result=subprocess.run([sys.executable, str(ROOT/"scripts"/script)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode: errors.append(f"existing QA failed: {script}\n{result.stdout}{result.stderr}")
    if errors:
        print(f"V7 visual QA FAILED ({len(errors)} issue(s))")
        print("\n".join(f"- {e}" for e in errors)); return 1
    print(f"V7 visual QA passed: {len(html_files)} HTML files, {len(IMPORTANT)} important pages, sitemap and existing V5/V5.1/V6 suites checked.")
    return 0
if __name__ == "__main__": raise SystemExit(main())
