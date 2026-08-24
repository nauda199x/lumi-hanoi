# Responsive V9 audit

Scope: site-wide layout stabilization after mobile screenshots exposed heading columns collapsing to single letters and desktop editorial pages under-using the viewport.

## Root cause

The legacy mobile `.section-head` one-column rule is declared earlier in `site.css`, while the later V7 desktop `.section-head` grid declaration overrides it in the cascade. On narrow screens the heading column is therefore squeezed beside a `minmax(280px, .7fr)` description column, producing letter-by-letter Vietnamese headings.

## V9 changes

- Add a final responsive stylesheet loaded after `site.css` on every page through the shared `site.js` loader.
- Force `.section-head` to a single readable column on tablet/phone widths.
- Explicitly prevent forced character-level wrapping in display and article headings.
- Collapse collection, split, visual, editorial, location and compact grids on phones.
- Normalize mobile header, buttons, cards, article typography, tables, captions and footer spacing.
- Widen long-form desktop editorial shells while keeping body copy within a readable measure and preserving the sticky related-content rail.
- Add `qa_responsive_v9.py` to guard the global loader and the critical responsive rules.

This patch is intentionally CSS/loader-only: it does not rewrite SEO copy, URLs, structured data, floor-plan data or media content.
