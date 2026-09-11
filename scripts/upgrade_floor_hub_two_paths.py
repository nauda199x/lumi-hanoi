from __future__ import annotations

import re
from pathlib import Path

PAGE = Path("mat-bang-lumi-hanoi/index.html")


def main() -> None:
    html = PAGE.read_text(encoding="utf-8")
    gateway_re = re.compile(
        r'<!-- TWO-PATH-GATEWAY:START -->.*?<!-- TWO-PATH-GATEWAY:END -->',
        re.S,
    )
    gateway_match = gateway_re.search(html)
    if not gateway_match:
        raise SystemExit("Two-path gateway block not found; nothing to normalize")

    gateway = gateway_match.group(0)
    html = html[: gateway_match.start()] + html[gateway_match.end() :]

    hero_re = re.compile(
        r'(<header class="article-hero floor-hub-hero">.*?</nav></div></header>)',
        re.S,
    )
    hero_match = hero_re.search(html)
    if not hero_match:
        raise SystemExit("Floor hub hero not found")

    html = html[: hero_match.end()] + gateway + html[hero_match.end() :]

    main_pos = html.index('<main id="main">')
    hero_pos = html.index('<header class="article-hero floor-hub-hero">')
    gateway_pos = html.index('<!-- TWO-PATH-GATEWAY:START -->')
    phase_pos = html.index('<!-- PHASE-UNIT-LAYOUTS:START -->')
    if not (main_pos < hero_pos < gateway_pos < phase_pos):
        raise SystemExit("Unexpected floor-hub ordering after normalization")
    if html.count('id="layout-all"') != 1 or html.count('id="tower-all"') != 1:
        raise SystemExit("Two-path gateway IDs must remain unique")

    PAGE.write_text(html, encoding="utf-8")
    print("Floor hub ordering normalized: hero -> two paths -> deeper content.")


if __name__ == "__main__":
    main()
