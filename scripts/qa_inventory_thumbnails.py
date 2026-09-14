"""Offline thumbnail tests; synthetic photos, no live listing or storage writes."""
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image
import generate_marketplace_seo as gen
import marketplace_inventory as inv
import marketplace_thumbnails as thumbs


def photo(size=(1200,900), orientation=None):
    image = Image.effect_noise(size, 80).convert("RGB")
    output = io.BytesIO()
    options = {}
    if orientation:
        exif = image.getexif()
        exif[274] = orientation
        options["exif"] = exif
    image.save(output, format="JPEG", quality=92, **options)
    return output.getvalue()


def rows():
    return [dict(id="sample", slug="sample", listing_type="rent", title="Căn mẫu", unit_type="1PN",
                 phase="Signature", tower="S1", area_sqm=42, price_vnd=10000000,
                 listing_images=[dict(storage_path="other.jpg", sort_order=1),
                                 dict(storage_path="cover.jpg", sort_order=0)])]


class Thumbnails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = photo()

    def test_dimensions_bytes_and_no_metadata(self):
        encoded, size = thumbs.encode_cover(self.payload)
        self.assertEqual(size, (800,600))
        self.assertLess(len(encoded), len(self.payload))
        with Image.open(io.BytesIO(encoded)) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertFalse(image.getexif())

    def test_exif_orientation_and_no_upscaling(self):
        _, size = thumbs.encode_cover(photo(orientation=6))
        self.assertEqual(size, (600,800))
        _, size = thumbs.encode_cover(photo((80,60)))
        self.assertEqual(size, (80,60))

    def test_byte_and_pixel_limits(self):
        with patch.object(thumbs, "MAX_BYTES", 10):
            with self.assertRaises(ValueError):
                thumbs.encode_cover(self.payload)
        with patch.object(thumbs, "MAX_PIXELS", 10):
            with self.assertRaises(ValueError):
                thumbs.encode_cover(self.payload)

    def test_only_public_storage_urls_and_no_redirects(self):
        for url in ["http://x.supabase.co/storage/v1/object/public/b/a.jpg", "file:///etc/passwd",
                    "https://example.com/a.jpg", "https://x.supabase.co.evil.test/a.jpg",
                    "https://x.supabase.co/storage/v1/object/sign/a.jpg",
                    "https://name:pass@x.supabase.co/storage/v1/object/public/b/a.jpg"]:
            with self.assertRaises(ValueError):
                thumbs.download_public(url)
        with self.assertRaises(ValueError):
            thumbs.NoRedirect().redirect_request(None,None,302,"Found",{},"https://example.com/")

    def test_first_cover_only_and_reuses_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            download = Mock(return_value=self.payload)
            mapping = thumbs.sync_thumbnails(root, rows(), gen.storage_url, download=download)
            original = gen.storage_url("cover.jpg")
            self.assertEqual(download.call_args.args, (original,))
            self.assertEqual(len(mapping),1)
            target = root / mapping[original].lstrip("/")
            self.assertTrue(target.is_file())
            cache = root / thumbs.CACHE
            before = cache.read_bytes()
            with patch.object(thumbs, "encode_cover", side_effect=AssertionError("cache should be reused")):
                self.assertEqual(thumbs.sync_thumbnails(root, rows(), gen.storage_url, download=download),mapping)
            self.assertEqual(download.call_count,1)
            self.assertEqual(cache.read_bytes(),before)
            entry = json.loads(before)["items"][original]
            self.assertEqual(entry["bytes"],target.stat().st_size)

    def test_missing_cached_file_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            download = Mock(return_value=self.payload)
            mapping = thumbs.sync_thumbnails(root, rows(), gen.storage_url, download=download)
            target = root / next(iter(mapping.values())).lstrip("/")
            target.unlink()
            thumbs.sync_thumbnails(root, rows(), gen.storage_url, download=download)
            self.assertTrue(target.is_file())
            self.assertEqual(download.call_count,2)

    def test_failures_do_not_break_inventory_and_can_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            for download in [Mock(side_effect=TimeoutError()),Mock(return_value=b"not an image")]:
                self.assertEqual(thumbs.sync_thumbnails(tmp,rows(),gen.storage_url,download=download),{})
            self.assertEqual(len(thumbs.sync_thumbnails(tmp,rows(),gen.storage_url,download=lambda _:self.payload)),1)

    def test_larger_encoded_image_keeps_original_without_repeat_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            download = Mock(return_value=b"tiny")
            with patch.object(thumbs,"encode_cover",return_value=(b"much larger",(1,1))):
                self.assertEqual(thumbs.sync_thumbnails(tmp,rows(),gen.storage_url,download=download),{})
                self.assertEqual(thumbs.sync_thumbnails(tmp,rows(),gen.storage_url,download=download),{})
            self.assertEqual(download.call_count,1)

    def test_budget_and_limit_leave_new_covers_on_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            download = Mock(side_effect=AssertionError("must not download"))
            self.assertEqual(thumbs.sync_thumbnails(tmp,rows(),gen.storage_url,download=download,budget=0),{})
            self.assertEqual(thumbs.sync_thumbnails(tmp,rows(),gen.storage_url,download=download,limit=0),{})
            download.assert_not_called()

    def test_cleanup_only_removes_owned_unused_thumbnails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping = thumbs.sync_thumbnails(root,rows(),gen.storage_url,download=lambda _:self.payload)
            target = root / next(iter(mapping.values())).lstrip("/")
            other = target.parent / "manual-note.txt"
            other.write_text("keep")
            thumbs.sync_thumbnails(root,[],gen.storage_url)
            self.assertFalse(target.exists())
            self.assertTrue(other.exists())

    def test_static_and_live_manifest_preserve_detail_originals_and_canonicals(self):
        row = rows()[0]
        original = gen.storage_url("cover.jpg")
        mapping = {original:thumbs.PREFIX + thumbs.filename(original),"</script>":"escaped"}
        with patch.object(gen,"INVENTORY_THUMBNAILS",mapping):
            for kind,segment in [("sale","mua-ban-lumi-hanoi"),("rent","cho-thue-lumi-hanoi")]:
                row = dict(row,listing_type=kind)
                template = (gen.ROOT / segment / "index.html").read_text()
                raw = inv.render_inventory_page(gen,template,[row],1,1,kind)
                self.assertIn(f'src="{mapping[original]}"',raw)
                self.assertIn(f'data-inventory-original="{original}"',raw)
                self.assertIn(f'href="{gen.SITE}/{segment}/"',raw)
                manifest = re.search(r'<script type="application/json" data-inventory-thumbnails>(.*?)</script>',raw,re.S)[1]
                self.assertNotIn("</script>",manifest)
                self.assertEqual(json.loads(manifest),mapping)
                self.assertEqual(inv.render_inventory_page(gen,raw,[row],1,1,kind),raw)
                self.assertIn(original,gen.render_gallery(row))
                self.assertNotIn(thumbs.PREFIX,gen.render_gallery(row))


if __name__ == "__main__":
    unittest.main(verbosity=2)
