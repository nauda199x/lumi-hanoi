"""Cache small, public listing covers during SEO sync; never modify originals.

Only covers are downloaded, with bounded time/bytes/pixels. New or failed covers
keep their original URL. Uploaded source paths contain UUIDs and are immutable.
"""
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

VERSION = 1
PREFIX = "/assets/media/listing-thumbnails/"
CACHE = "assets/data/inventory-thumbnail-cache.json"
MAX_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 25_000_000
MAX_EDGE = 800


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Thumbnail source redirects are not followed")


def download_public(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or not (parsed.hostname or "").endswith(".supabase.co")
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or not parsed.path.startswith("/storage/v1/object/public/")):
        raise ValueError("Expected a public Supabase Storage image")
    request = urllib.request.Request(url, headers={"User-Agent": "lumi-inventory-thumbnails/1.0"})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=8) as response:
        if int(response.headers.get("Content-Length") or 0) > MAX_BYTES:
            raise ValueError("Cover exceeds byte limit")
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError("Cover exceeds byte limit")
    return payload


def encode_cover(payload):
    from PIL import Image, ImageOps
    if len(payload) > MAX_BYTES:
        raise ValueError("Cover exceeds byte limit")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(payload)) as source:
            if source.width * source.height > MAX_PIXELS:
                raise ValueError("Cover exceeds pixel limit")
            image = ImageOps.exif_transpose(source)
            image.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
            image = image.convert("RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB")
            output = io.BytesIO()
            image.save(output, format="WEBP", quality=82, method=4)
            return output.getvalue(), image.size


def filename(url):
    digest = hashlib.sha256(f"v{VERSION}:{url}".encode()).hexdigest()[:32]
    return digest + ".webp"


def sync_thumbnails(root, rows, storage_url, *, download=download_public, limit=40, budget=45):
    root = Path(root)
    cache_path = root / CACHE
    try:
        cache = json.loads(cache_path.read_text())
        previous = cache.get("items", {}) if cache.get("version") == VERSION else {}
    except (OSError, ValueError):
        previous = {}
    covers = set()
    for row in rows:
        images = sorted((item for item in (row.get("listing_images") or []) if item.get("storage_path")),
                        key=lambda item: int(item.get("sort_order") or 0))
        if images:
            covers.add(storage_url(images[0]["storage_path"]))
    directory = root / PREFIX.lstrip("/")
    directory.mkdir(parents=True, exist_ok=True)
    entries, pending = {}, []
    for url in sorted(covers):
        cached = previous.get(url, {})
        expected = PREFIX + filename(url)
        if cached.get("src") == url or (cached.get("src") == expected and (root / expected.lstrip("/")).is_file()):
            entries[url] = cached
        else:
            pending.append(url)
    started = time.monotonic()

    def build(url):
        if time.monotonic() - started >= budget:
            return url, None
        try:
            payload = download(url)
            encoded, (width, height) = encode_cover(payload)
            entry = {"source_bytes": len(payload), "bytes": len(payload), "src": url}
            # A tiny original should not become a larger thumbnail.
            if len(encoded) < len(payload):
                target = directory / filename(url)
                temporary = target.with_suffix(".tmp")
                temporary.write_bytes(encoded)
                temporary.replace(target)
                entry.update(src=PREFIX + target.name, bytes=len(encoded), width=width, height=height)
            return url, entry
        except Exception:
            # Image/network errors must not interrupt listing or sitemap sync.
            return url, None

    with ThreadPoolExecutor(max_workers=4) as pool:
        for url, entry in pool.map(build, pending[:max(0, limit)]):
            if entry:
                entries[url] = entry
    active_names = {filename(url) for url in covers}
    for path in directory.iterdir():
        if re.fullmatch(r"[a-f0-9]{32}\.webp", path.name) and path.name not in active_names:
            path.unlink()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({"version": VERSION, "items": entries}, ensure_ascii=False,
                                     sort_keys=True, indent=2) + "\n", encoding="utf-8")
    optimized = {url: entry["src"] for url, entry in entries.items() if entry["src"] != url}
    before = sum(entry["source_bytes"] for entry in entries.values())
    after = sum(entry["bytes"] for entry in entries.values())
    print(f"Inventory covers: {len(optimized)}/{len(covers)} optimized; {before} -> {after} bytes; {len(covers)-len(entries)} deferred")
    return optimized
