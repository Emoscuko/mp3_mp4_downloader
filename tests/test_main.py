import unittest

import main


class PlatformDetectionTests(unittest.TestCase):
    def test_detects_youtube_hosts(self):
        self.assertIsInstance(main.detect_platform("https://www.youtube.com/watch?v=abc"), main.YouTubeStrategy)
        self.assertIsInstance(main.detect_platform("youtu.be/abc"), main.YouTubeStrategy)

    def test_detects_instagram_hosts(self):
        self.assertIsInstance(main.detect_platform("https://www.instagram.com/reel/abc"), main.InstagramStrategy)
        self.assertIsInstance(main.detect_platform("instagram.com/p/abc"), main.InstagramStrategy)

    def test_detects_tiktok_hosts(self):
        self.assertIsInstance(main.detect_platform("https://www.tiktok.com/@user/video/123"), main.TikTokStrategy)
        self.assertIsInstance(main.detect_platform("https://vm.tiktok.com/abc"), main.TikTokStrategy)
        self.assertIsInstance(main.detect_platform("vt.tiktok.com/abc"), main.TikTokStrategy)

    def test_rejects_unsupported_hosts(self):
        self.assertIsNone(main.detect_platform("https://example.com/video"))
        self.assertIsNone(main.detect_platform("https://notinstagram.com/reel/abc"))


class StrategyModeTests(unittest.TestCase):
    def test_transcript_is_youtube_only(self):
        youtube = main.detect_platform("https://youtube.com/watch?v=abc")
        instagram = main.detect_platform("https://instagram.com/reel/abc")
        tiktok = main.detect_platform("https://tiktok.com/@user/video/123")

        self.assertTrue(youtube.supports_mode(main.MODE_TRANSCRIPT))
        self.assertFalse(instagram.supports_mode(main.MODE_TRANSCRIPT))
        self.assertFalse(tiktok.supports_mode(main.MODE_TRANSCRIPT))


class DownloadOptionTests(unittest.TestCase):
    def test_video_best_quality_options(self):
        options = main.build_download_options("/tmp", main.MODE_VIDEO, "En Yüksek")

        self.assertEqual(options["format"], "bv*+ba/b")
        self.assertEqual(options["merge_output_format"], "mp4")
        self.assertNotIn("format_sort", options)

    def test_video_limited_quality_options(self):
        options = main.build_download_options("/tmp", main.MODE_VIDEO, "720p")

        self.assertEqual(options["format"], "bv*+ba/b")
        self.assertEqual(options["merge_output_format"], "mp4")
        self.assertEqual(options["format_sort"][0], "res:720")

    def test_audio_best_quality_options(self):
        options = main.build_download_options("/tmp", main.MODE_AUDIO, "En Yüksek")
        postprocessor = options["postprocessors"][0]

        self.assertEqual(options["format"], "bestaudio/best")
        self.assertEqual(postprocessor["key"], "FFmpegExtractAudio")
        self.assertEqual(postprocessor["preferredcodec"], "mp3")
        self.assertEqual(postprocessor["preferredquality"], "0")

    def test_audio_selected_bitrate_options(self):
        options = main.build_download_options("/tmp", main.MODE_AUDIO, "192 kbps")
        postprocessor = options["postprocessors"][0]

        self.assertEqual(postprocessor["preferredquality"], "192")


if __name__ == "__main__":
    unittest.main()
