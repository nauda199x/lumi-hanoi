#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
css_path = ROOT / 'assets/css/responsive-v9.css'
js_path = ROOT / 'assets/js/site.js'

errors = []

if not css_path.exists():
    errors.append('missing assets/css/responsive-v9.css')
else:
    css = css_path.read_text(encoding='utf-8')
    required = {
        'mobile section-head collapse': r'@media\s*\(max-width:700px\)[\s\S]*?\.section-head\s*\{[\s\S]*?display:block!important',
        'mobile article one-column': r'\.editorial-shell\.article-layout--with-sidebar\s*\{[\s\S]*?grid-template-columns:minmax\(0,1fr\)!important',
        'heading wrapping guard': r'word-break:normal',
        'mobile visual grid collapse': r'\.visual-grid,[\s\S]*?grid-template-columns:minmax\(0,1fr\)!important',
        'desktop editorial width': r'@media\s*\(min-width:1025px\)[\s\S]*?\.editorial-shell\.article-layout--with-sidebar',
    }
    for label, pattern in required.items():
        if not re.search(pattern, css):
            errors.append(f'missing responsive rule: {label}')

if not js_path.exists():
    errors.append('missing assets/js/site.js')
else:
    js = js_path.read_text(encoding='utf-8')
    if '/assets/css/responsive-v9.css?v=20260824' not in js:
        errors.append('site.js does not load responsive-v9.css')
    if "responsiveStyles.rel='stylesheet'" not in js:
        errors.append('responsive stylesheet link is not configured as stylesheet')

# The shared JS loader must be present on public HTML pages for the global CSS fix to apply.
ignored = {ROOT / '404.html'}
html_files = [p for p in ROOT.rglob('*.html') if p not in ignored and '.git' not in p.parts]
missing_loader = []
for path in html_files:
    text = path.read_text(encoding='utf-8', errors='ignore')
    # Only check normal public documents; tiny redirect/utility documents may omit full chrome.
    if '<html' not in text.lower() or '<body' not in text.lower():
        continue
    if '/assets/css/site.css' in text and '/assets/js/site.js' not in text:
        missing_loader.append(str(path.relative_to(ROOT)))

if missing_loader:
    errors.append('pages using site.css but missing site.js loader: ' + ', '.join(missing_loader[:12]))

if errors:
    print(f'Responsive V9 QA FAILED ({len(errors)} issue(s))')
    for error in errors:
        print('- ' + error)
    sys.exit(1)

print(f'Responsive V9 QA passed for {len(html_files)} HTML files.')
