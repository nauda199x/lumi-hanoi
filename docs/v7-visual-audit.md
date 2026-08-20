# V7 visual and media audit

**Audit date:** 20 August 2026  
**Scope:** `assets/media/`, `docs/media-map.md`, `docs/source-map.md`, every public HTML page, and the existing V4/V6 media integrations.

## Conclusions before implementation

The repository already contained a compact, approved local package of 14 WebP files. It was sufficient for an image-led V7 without downloading or hotlinking anything. The strongest imagery is consistently 985 × 633 (a useful editorial 1.56:1 ratio); the masterplan and technical plans use their own document proportions. V7 therefore reuses verified files and adds **no new media**.

## Current inventory and intended use

| Local file | Intrinsic dimensions | Approx. size | V7 role |
|---|---:|---:|---|
| `home/lumi-hanoi-hero.webp` | 985 × 633 | 303 KB | Homepage LCP/cinematic hero; general project-page hero |
| `home/lumi-hanoi-streetscape.webp` | 985 × 633 | 442 KB | Design story and editorial/article hero |
| `signature/lumi-signature-landscape.webp` | 985 × 633 | 322 KB | Signature hero and collection panel |
| `signature/lumi-signature-water-garden.webp` | 985 × 633 | 325 KB | Amenities story |
| `signature/lumi-signature-pool.webp` | 985 × 633 | 259 KB | Signature supporting gallery |
| `prestige/lumi-prestige-hero.webp` | 985 × 633 | 337 KB | Prestige hero and collection panel |
| `prestige/lumi-prestige-aurora-pool.webp` | 985 × 633 | 247 KB | Prestige supporting gallery |
| `prestige/lumi-prestige-garden.webp` | 985 × 633 | 255 KB | Amenities/pillar hero |
| `elite/lumi-elite-facade.webp` | 985 × 633 | 218 KB | Elite hero and collection panel |
| `elite/lumi-elite-aurora-pool.webp` | 985 × 633 | 301 KB | Amenities story |
| `elite/lumi-elite-lobby-e1.webp` | 985 × 633 | 164 KB | Handover/interior editorial hero |
| `masterplan/lumi-hanoi-masterplan.webp` | 893 × 649 | 220 KB | Homepage plan story and plan/product heroes |
| `layouts/lumi-prestige-typical-floor.webp` | 985 × 633 | 291 KB | Prestige technical plan |
| `layouts/lumi-elite-masterplan.webp` | 985 × 633 | 354 KB | Elite technical plan |
| `og/lumi-hanoi-og.webp` | 1200 × 630 | 138 KB | Social sharing only |

Dimensions above are the existing intrinsic dimensions recorded in page markup/media documentation; byte sizes were audited from the local files. Provenance remains recorded in `docs/media-map.md` and the verified source package.

## Strongest hero candidates

1. **Project/home:** `home/lumi-hanoi-hero.webp` — broad architecture and street composition supports overlay copy and remains the only homepage high-priority image.
2. **Signature:** `signature/lumi-signature-landscape.webp` — phase-specific and spatially layered.
3. **Prestige:** `prestige/lumi-prestige-hero.webp` — the clearest phase-specific establishing visual.
4. **Elite:** `elite/lumi-elite-facade.webp` — strongest identifiable architectural elevation.
5. **Design/editorial:** `home/lumi-hanoi-streetscape.webp` — works well with restrained crops and long-form headings.
6. **Technical story:** `masterplan/lumi-hanoi-masterplan.webp` — should remain uncropped and framed on a white surface.

## Weak, duplicate, or constrained material

- Most renderings share the same 985 × 633 delivery size. Repeated use is acceptable across related templates, but pages should not load the whole library.
- The two Aurora pool files depict phase-specific contexts; they are not interchangeable proof of a project-wide contractual amenity.
- `lumi-hanoi-og.webp` is a derivative for social cards and should not be enlarged as an inline editorial image.
- Technical plans require uncropped presentation/lightbox treatment; using them as decorative `object-fit: cover` imagery would hide labels.
- There are no verified unit-layout images for every bedroom type, no dated construction photographs in `progress/`, and no article-specific images in `news/`.
- Empty category `.gitkeep` files are not content and are excluded from the visual inventory.

## Visually thin areas found

- Homepage collection cards had no imagery and apartment types were only text links.
- Pillar, bedroom, transaction, news, and long-article heroes were text-only despite the verified media package.
- The amenities introduction had hierarchy but lacked a strong visual narrative.
- News cards were structurally uniform, so featured and supporting stories had equal visual weight.
- The footer was useful but read as one flat link row rather than a calm navigation index.
- Long articles had sound content structure but needed stronger hero contrast, source panels, tables, reading rhythm, and section separation.

## Recommended page-to-image mapping implemented

| Page family | Primary local visual |
|---|---|
| Homepage | Home hero; phase-specific collection images; masterplan; water garden/pool; streetscape |
| Overview, location, progress | Home hero or streetscape as atmospheric project context |
| Masterplan and bedroom guides | Masterplan, clearly used as project-level context rather than a unit-specific layout |
| Amenities | Prestige garden plus phase-specific water imagery |
| Design | Streetscape |
| Handover | Elite lobby as architectural context, not evidence of contractual specification |
| Signature / Prestige / Elite | Corresponding verified phase image |
| Legal, buying, rental, consignment | Prestige project rendering as neutral project context |
| News hub and articles | Streetscape as a consistent editorial masthead; article substance remains unchanged |

## Performance and rights decisions

- No external image requests, competitor assets, new downloads, or uncertain-rights assets were introduced.
- The homepage hero alone uses `fetchpriority="high"`; every below-the-fold homepage image is lazy-loaded and asynchronously decoded.
- All inline content images retain intrinsic dimensions and useful alt text. Decorative editorial hero images use empty alt text so headings are not repeated by assistive technology.
- Page families reuse one relevant hero rather than downloading several large images above the fold.
- No claim is made about Lighthouse or field Core Web Vitals because those measurements are outside this static audit.
