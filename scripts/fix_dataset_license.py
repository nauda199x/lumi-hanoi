#!/usr/bin/env python3
"""Ensure the Lumi Hanoi market Dataset schema declares its usage terms."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRICE_PAGE = ROOT / "gia-can-ho-lumi-hanoi" / "index.html"
LICENSE_URL = "https://lumi-hanoi.com/dieu-khoan-su-dung/"
SCHEMA_RE = re.compile(r'(<script\s+type="application/ld\+json">)(.*?)(</script>)', re.S | re.I)


def main() -> None:
    raw = PRICE_PAGE.read_text(encoding="utf-8")
    dataset_count = 0
    changed = False

    def rewrite(match: re.Match[str]) -> str:
        nonlocal dataset_count, changed
        try:
            payload = json.loads(match.group(2))
        except json.JSONDecodeError:
            return match.group(0)

        nodes = payload.get("@graph", []) if isinstance(payload, dict) else []
        for node in nodes:
            if not isinstance(node, dict) or node.get("@type") != "Dataset":
                continue
            dataset_count += 1
            if node.get("license") != LICENSE_URL:
                node["license"] = LICENSE_URL
                changed = True

        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        return match.group(1) + encoded + match.group(3)

    updated = SCHEMA_RE.sub(rewrite, raw)
    if dataset_count != 1:
        raise RuntimeError(f"Expected exactly one Dataset node on {PRICE_PAGE}, found {dataset_count}")
    if LICENSE_URL not in updated:
        raise RuntimeError("Dataset license URL was not written")

    if changed:
        PRICE_PAGE.write_text(updated, encoding="utf-8")
        print(f"Dataset license added: {LICENSE_URL}")
    else:
        print("Dataset license already correct; no change needed")


if __name__ == "__main__":
    main()
