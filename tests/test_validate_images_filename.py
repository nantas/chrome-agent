"""Unit tests for L6 image availability filename parsing.

Spec: close-mediawiki-quality-followups — pipeline/l6-image-filename-parsing.
Fandom CDN transform suffixes must resolve to the real file name, not the
size parameter (previously 17k+ api_missing false positives per site).
"""

from __future__ import annotations

import os
import tempfile
import unittest

from scripts.pipeline.strategies import _image_file_title, validate_images


class FakeImageinfoClient:
    """ApiClient stub: everything queried exists (no missing pages)."""

    def query(self, titles, prop, iiprop):
        pages = {
            str(i): {"title": t, "imageinfo": [{"url": "https://x"}]}
            for i, t in enumerate(titles.split("|"))
        }
        return {"query": {"pages": pages}}


class TestImageFileTitle(unittest.TestCase):
    def test_revision_url_resolves_real_filename(self):
        url = ("https://static.wikia.nocookie.net/growagarden/images/0/08/"
               "DivineIcon.png/revision/latest/scale-to-width-down/111?cb=20260427163904")
        self.assertEqual(_image_file_title(url), "File:DivineIcon.png")

    def test_special_redirect_branch_preserved(self):
        self.assertEqual(
            _image_file_title("https://x.fandom.com/Special:Redirect/file/Beee.png"),
            "File:Beee.png")
        self.assertEqual(
            _image_file_title("https://x.fandom.com/wiki/Special:Redirect/file/Big%20Apple.png?debug"),
            "File:Big%20Apple.png")

    def test_plain_url_last_segment(self):
        self.assertEqual(
            _image_file_title("https://example.com/images/a/Ac.png"),
            "File:Ac.png")

    def test_mediawiki_thumb_url_resolves_real_filename(self):
        url = ("https://slaythespire.wiki.gg/images/thumb/5/5c/Red-Bash.png"
               "/150px-Red-Bash.png?57867c")
        self.assertEqual(_image_file_title(url), "File:Red-Bash.png")


class TestValidateImagesNoFalsePositive(unittest.TestCase):
    def test_cdn_revision_url_not_reported_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "page.md"), "w", encoding="utf-8") as f:
                f.write("![Divine](https://static.wikia.nocookie.net/growagarden"
                        "/images/0/08/DivineIcon.png/revision/latest"
                        "/scale-to-width-down/111?cb=20260427163904)\n")
            unavailable = validate_images(d, client=FakeImageinfoClient())
        self.assertEqual(unavailable, [])


if __name__ == "__main__":
    unittest.main()
