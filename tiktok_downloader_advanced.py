#!/usr/bin/env python3
"""
TikTok Video Downloader - Advanced Version with geo-restriction support
Download videos from TikTok bypassing geographical restrictions
Version: 2.4 - Added user-friendly error handling
"""

import argparse
import yt_dlp
import os
from pathlib import Path
from logger_manager import logger
from retry_utils import retry_on_network_error, retry_on_api_error, RetryContext
from config_manager import get_config
from error_handler import ErrorHandler, handle_error, is_retryable_error, get_retry_wait_time
import time


class TikTokDownloader:
    def __init__(self, output_dir=None, use_cookies=False, cookies_file=None, geo_bypass=None):
        # Use config if not specified
        if output_dir is None:
            output_dir = get_config('monitor.output_dir', './tiktok_downloads')
        if geo_bypass is None:
            geo_bypass = get_config('download.geo_bypass', True)

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_cookies = use_cookies
        self.cookies_file = cookies_file
        self.geo_bypass = geo_bypass

        logger.info(f"Downloader initialized: {output_dir}")
        if geo_bypass:
            logger.debug("Geo-bypass enabled (USA)")
        if use_cookies and cookies_file:
            logger.debug(f"Using cookies: {cookies_file}")

    def download(self, url, quality=None, with_audio=None, max_retries=3):
        """
        Download a TikTok video with user-friendly error handling and automatic retry

        Args:
            url: Video URL
            quality: Video quality ('best', 'worst', or specific resolution)
            with_audio: Include audio in download
            max_retries: Maximum number of retry attempts
            
        Returns:
            str: Path to downloaded file, or None if failed
        """
        # Use config if not specified
        if quality is None:
            quality = get_config('download.quality', 'best')
        if with_audio is None:
            with_audio = get_config('download.with_audio', True)

        format_string = 'best' if quality == 'best' else f'best[height<={quality}]'

        ydl_opts = {
            'format': format_string,
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,

            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },

            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }] if with_audio else [],

            'ignoreerrors': False,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
        }

        if self.geo_bypass:
            ydl_opts['geo_bypass'] = True
            geo_country = get_config('download.geo_bypass_country', 'US')
            ydl_opts['geo_bypass_country'] = geo_country

        if self.use_cookies and self.cookies_file:
            if os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                logger.debug(f"Cookies loaded: {self.cookies_file}")
            else:
                logger.warning(f"Cookie file not found: {self.cookies_file}")

        # Retry loop with user-friendly error handling
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"📥 Downloading: {url}")
                if attempt > 1:
                    logger.info(f"🔄 Retry attempt {attempt}/{max_retries}")
                
                logger.debug(f"Output: {self.output_dir}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                    # Success!
                    logger.success("Download completed!")
                    logger.info(f"📄 File: {filename}")
                    logger.info(f"🎬 Title: {info.get('title', 'N/A')}")
                    logger.info(f"👤 Author: {info.get('uploader', 'Unknown')}")
                    logger.info(f"👁️  Views: {info.get('view_count', 0):,}")
                    logger.info(f"❤️  Likes: {info.get('like_count', 0):,}")
                    logger.info(f"💬 Comments: {info.get('comment_count', 0):,}")

                    return filename

            except Exception as e:
                # Analyze error with user-friendly handler
                user_error = handle_error(e, url, show_technical=(attempt == max_retries))
                
                # Check if should retry
                if attempt < max_retries and is_retryable_error(user_error):
                    wait_time = get_retry_wait_time(user_error)
                    logger.warning(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Max retries reached or non-retryable error
                    if not is_retryable_error(user_error):
                        logger.error("❌ This error cannot be automatically resolved")
                    else:
                        logger.error(f"❌ Max retries ({max_retries}) reached")
                    
                    return None
        
        return None

    def download_multiple(self, urls):
        """Download multiple videos with user-friendly error handling"""
        results = []
        successful = 0
        failed = 0
        skipped = 0

        logger.info(f"Starting batch download: {len(urls)} videos")

        for i, url in enumerate(urls, 1):
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"Video {i}/{len(urls)}")
            logger.info("=" * 60)

            result = self.download(url)
            
            if result:
                results.append(result)
                successful += 1
            else:
                results.append(None)
                failed += 1

        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("BATCH DOWNLOAD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successful: {successful}/{len(urls)}")
        logger.info(f"❌ Failed: {failed}/{len(urls)}")
        logger.info("=" * 60)

        return results


def export_cookies_instructions():
    """Show instructions for exporting cookies"""
    instructions = """
╔═══════════════════════════════════════════════════════════════════════╗
║          HOW TO EXPORT COOKIES FROM TIKTOK                            ║
╚═══════════════════════════════════════════════════════════════════════╝

To download videos with geographical restrictions or that require login:

METHOD 1 - Browser Extension (Recommended):
  1. Install the "Get cookies.txt LOCALLY" extension on Chrome/Firefox
     Chrome: https://chrome.google.com/webstore (search "get cookies.txt locally")
     Firefox: https://addons.mozilla.org (search "cookies.txt")

  2. Go to https://www.tiktok.com and login

  3. Click on the extension icon

  4. Click "Export" and save as "tiktok_cookies.txt"

  5. Use the command:
     python tiktok_downloader_advanced.py --cookies tiktok_cookies.txt <URL>

METHOD 2 - Use a VPN:
  1. Connect to a VPN (USA or UK work well)

  2. Run the download normally

  3. The automatic geo-bypass should work

NOTE: Cookies expire periodically, you may need to update them.
"""
    print(instructions)


def main():
    parser = argparse.ArgumentParser(
        description='TikTok Video Downloader v2.4 - With user-friendly error handling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic download (uses config.yaml if available)
  %(prog)s https://www.tiktok.com/@user/video/123456789

  # With cookies (for geo-restrictions)
  %(prog)s --cookies tiktok_cookies.txt https://www.tiktok.com/@user/video/123456789

  # Multiple downloads
  %(prog)s -f urls.txt --cookies tiktok_cookies.txt

  # Specific quality (overrides config)
  %(prog)s --quality 720 https://www.tiktok.com/@user/video/123456789

  # Show cookie instructions
  %(prog)s --help-cookies

  # Show technical details on errors
  %(prog)s --debug https://www.tiktok.com/@user/video/123456789
        """
    )

    parser.add_argument('url', nargs='?', help='TikTok video URL')
    parser.add_argument('-o', '--output', default=None,
                        help='Output folder (overrides config)')
    parser.add_argument('-f', '--file', help='File with URL list (one per line)')
    parser.add_argument('-q', '--quality', default=None,
                        help='Video quality: best, 720, 480, etc. (overrides config)')
    parser.add_argument('--no-audio', action='store_true',
                        help='Download video only without audio (overrides config)')
    parser.add_argument('--cookies', metavar='FILE',
                        help='cookies.txt file for authentication (resolves geo-restrictions)')
    parser.add_argument('--no-geo-bypass', action='store_true',
                        help='Disable automatic geo-bypass (overrides config)')
    parser.add_argument('--help-cookies', action='store_true',
                        help='Show instructions for exporting cookies')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='Maximum retry attempts (default: 3)')
    parser.add_argument('--debug', action='store_true',
                        help='Show technical error details')

    args = parser.parse_args()

    if args.help_cookies:
        export_cookies_instructions()
        return

    # Use config values if not specified in command line
    output_dir = args.output if args.output is not None else get_config('monitor.output_dir', './tiktok_downloads')
    geo_bypass = not args.no_geo_bypass if args.no_geo_bypass else get_config('download.geo_bypass', True)

    downloader = TikTokDownloader(
        output_dir,
        use_cookies=bool(args.cookies),
        cookies_file=args.cookies,
        geo_bypass=geo_bypass
    )

    try:
        if args.file:
            logger.info(f"Reading URLs from file: {args.file}")
            with open(args.file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"Found {len(urls)} URLs")
            downloader.download_multiple(urls)

        elif args.url:
            quality = args.quality if args.quality is not None else get_config('download.quality', 'best')
            with_audio = not args.no_audio if args.no_audio else get_config('download.with_audio', True)

            result = downloader.download(args.url, quality, with_audio, max_retries=args.max_retries)
            
            if not result:
                return 1  # Exit with error code

        else:
            logger.info("╔═══════════════════════════════════════════════════════════╗")
            logger.info("║             TikTok Video Downloader v2.4                  ║")
            logger.info("║                                                           ║")
            logger.info("╚═══════════════════════════════════════════════════════════╝")
            logger.info("")
            logger.info("💡 Using settings from config.yaml (if available)")
            logger.info("For videos with geo-restrictions, use: --cookies tiktok_cookies.txt")
            logger.info("For cookie instructions: --help-cookies")
            logger.info("For technical error details: --debug")
            logger.info("")
            url = input("Enter TikTok video URL: ").strip()
            if url:
                quality = args.quality if args.quality is not None else get_config('download.quality', 'best')
                with_audio = not args.no_audio if args.no_audio else get_config('download.with_audio', True)
                result = downloader.download(url, quality, with_audio, max_retries=args.max_retries)
                
                if not result:
                    return 1
            else:
                parser.print_help()

    except KeyboardInterrupt:
        logger.info("\n❌ Download interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
