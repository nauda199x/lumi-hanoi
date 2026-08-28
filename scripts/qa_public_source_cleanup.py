#!/usr/bin/env python3
"""Prevent editorial source credits and source-file links from reaching public files."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TEXT = (
    "nguồn và ngày",
    "ngày xác minh",
    "nguồn tham khảo",
    "nguồn kiểm chứng",
    "bản nguồn",
)
FORBIDDEN_MARKUP = (
    'class="source-list"',
    'class="figure-source"',
    'class="source-mini"',
)
DRIVE_FILE_LINK = re.compile(r'href=["\']https://drive\.google\.com/file/', re.I)


def main() -> None:
    failures: list[str] = []
    html_files = sorted(ROOT.rglob("*.html"))
    public_files = html_files + sorted((ROOT / "assets/js").glob("*.js"))

    for path in public_files:
        content = path.read_text(encoding="utf-8")
        folded = content.casefold()
        for token in (*FORBIDDEN_TEXT, *FORBIDDEN_MARKUP):
            if token.casefold() in folded:
                failures.append(f"{path.relative_to(ROOT)}: contains {token!r}")
        if DRIVE_FILE_LINK.search(content):
            failures.append(
                f"{path.relative_to(ROOT)}: contains a public Google Drive source-file link"
            )

    if failures:
        print("Public source cleanup QA: FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print(
        "Public source cleanup QA: PASS "
        f"({len(html_files)} HTML and {len(public_files) - len(html_files)} JavaScript files checked)"
    )


if __name__ == "__main__":
    main()
