#!/usr/bin/env python3

# Allow direct execution
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from test.helper import FakeYDL
from yt_dlp.extractor.vimeo import VHXEmbedIE
from yt_dlp.utils import smuggle_url, unsmuggle_url


class TestVHXEmbedIE(unittest.TestCase):
    def setUp(self):
        self.ie = VHXEmbedIE(FakeYDL({
            'quiet': True,
            'verbose': False,
            'writeinfojson': False,
        }))

    def _stub_player(self, title='Untitled'):
        self.ie._download_webpage = (
            lambda *args, **kwargs: 'window.OTTData = {"config_url": "https://player.vimeo.com/config"}')
        self.ie._download_json = lambda *args, **kwargs: {}
        self.ie._parse_config = lambda config, video_id: {'title': title}

    def test_extract_from_webpage_smuggles_og_title(self):
        webpage = '''<html><head>
        <meta property="og:title" content="Fixture Hard Work Title">
        </head><body>
        <iframe src="https://embed.vhx.tv/videos/2251259?api=1"></iframe>
        </body></html>'''
        results = list(self.ie._extract_from_webpage(
            'http://example.test/with-title', webpage))
        self.assertEqual(len(results), 1)
        _, data = unsmuggle_url(results[0]['url'], {})
        self.assertEqual(data.get('title'), 'Fixture Hard Work Title')
        self.assertEqual(data.get('referer'), 'http://example.test/with-title')

    def test_extract_from_webpage_twitter_player(self):
        webpage = '''<html><head>
        <meta property="og:title" content="Hard Work">
        <meta name="twitter:player" content="https://embed.vhx.tv/videos/2251259">
        </head></html>'''
        results = list(self.ie._extract_from_webpage(
            'https://demo.vhx.tv/video', webpage))
        self.assertEqual(len(results), 1)
        _, data = unsmuggle_url(results[0]['url'], {})
        self.assertEqual(data.get('title'), 'Hard Work')
        self.assertEqual(data.get('referer'), 'https://demo.vhx.tv/video')
        self.assertTrue(VHXEmbedIE.suitable(unsmuggle_url(results[0]['url'])[0]))

    def test_real_extract_uses_smuggled_title_without_parent_fetch(self):
        downloaded = []

        def fake_download_webpage(url_or_request, video_id, *args, **kwargs):
            downloaded.append(str(url_or_request))
            return 'window.OTTData = {"config_url": "https://player.vimeo.com/config"}'

        self.ie._download_webpage = fake_download_webpage
        self.ie._download_json = lambda *args, **kwargs: {}
        self.ie._parse_config = lambda config, video_id: {'title': 'Untitled'}

        url = smuggle_url('https://embed.vhx.tv/videos/2251259', {
            'referer': 'http://parent.test/page',
            'title': 'Recovered Title',
        })
        info = self.ie._real_extract(url)
        self.assertEqual(info['title'], 'Recovered Title')
        self.assertTrue(all('parent.test' not in u for u in downloaded))

    def test_real_extract_keeps_untitled_without_smuggled_title(self):
        self._stub_player()
        info = self.ie._real_extract('https://embed.vhx.tv/videos/2251259')
        self.assertEqual(info['title'], 'Untitled')

    def test_real_extract_does_not_override_real_title(self):
        self._stub_player(title='Actual Video Name')
        url = smuggle_url(
            'https://embed.vhx.tv/videos/2251259', {'title': 'Page Title'})
        info = self.ie._real_extract(url)
        self.assertEqual(info['title'], 'Actual Video Name')


if __name__ == '__main__':
    unittest.main()
