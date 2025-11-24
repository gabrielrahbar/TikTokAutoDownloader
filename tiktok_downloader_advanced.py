#!/usr/bin/env python3
"""
TikTok Video Downloader - Advanced Version with geo-restriction support
Download videos from TikTok bypassing geographical restrictions
"""

import argparse
import yt_dlp
import os
from pathlib import Path
from logger_manager import logger
from retry_utils import retry_on_network_error, retry_on_api_error, RetryContext


class TikTokDownloader:
    def __init__(self, output_dir="./tiktok_downloads", use_cookies=False, cookies_file=None, geo_bypass=True):
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
    
    @retry_on_network_error(max_retries=3)
    @retry_on_api_error(max_retries=5)
    def download(self, url, quality='best', with_audio=True):
        """
        Download a TikTok video with geo-restriction support and automatic retry
        
        Args:
            url: Video URL
            quality: Video quality ('best', 'worst', or specific resolution)
            with_audio: Include audio in download
        """
        format_string = 'best' if quality == 'best' else f'best[height<={quality}]'
        
        ydl_opts = {
            'format': format_string,
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': True,  # Suppress yt-dlp output (we use logging)
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
            
            # Network retry settings (yt-dlp internal)
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
        }
        
        if self.geo_bypass:
            ydl_opts['geo_bypass'] = True
            ydl_opts['geo_bypass_country'] = 'US'
        
        if self.use_cookies and self.cookies_file:
            if os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                logger.debug(f"Cookies loaded: {self.cookies_file}")
            else:
                logger.warning(f"Cookie file not found: {self.cookies_file}")
        
        try:
            logger.info(f"📥 Downloading: {url}")
            logger.debug(f"Output: {self.output_dir}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Log success with details
                logger.success("Download completed!")
                logger.info(f"📄 File: {filename}")
                logger.info(f"🎬 Title: {info.get('title', 'N/A')}")
                logger.info(f"👤 Author: {info.get('uploader', 'Unknown')}")
                logger.info(f"👁️  Views: {info.get('view_count', 0):,}")
                logger.info(f"❤️  Likes: {info.get('like_count', 0):,}")
                logger.info(f"💬 Comments: {info.get('comment_count', 0):,}")
                
                return filename
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            
            # Handle specific error types
            if 'geo' in error_msg.lower() or 'not available' in error_msg.lower():
                logger.error("❌ Geo-restriction error detected!")
                logger.geo_restriction_detected()
                raise ConnectionError("Geo-restriction detected")  # Will trigger retry
                
            elif 'private' in error_msg.lower():
                logger.error("❌ Video is private")
                raise ValueError("Video is private")  # Non-retryable
                
            elif 'removed' in error_msg.lower() or 'deleted' in error_msg.lower():
                logger.error("❌ Video has been removed")
                raise ValueError("Video removed")  # Non-retryable
                
            elif 'rate' in error_msg.lower() or '429' in error_msg:
                logger.error("❌ Rate limited by TikTok")
                raise ConnectionError("Rate limited")  # Will trigger retry with longer wait
                
            else:
                logger.error(f"❌ Download error: {error_msg}")
                raise  # Re-raise for retry logic
                
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
            raise
    
    def download_multiple(self, urls):
        """Download multiple videos with retry logic"""
        results = []
        successful = 0
        failed = 0
        
        logger.info(f"Starting batch download: {len(urls)} videos")
        
        for i, url in enumerate(urls, 1):
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"Video {i}/{len(urls)}")
            logger.info("=" * 60)
            
            try:
                result = self.download(url)
                results.append(result)
                successful += 1
                
            except Exception as e:
                logger.error(f"Failed to download video {i}: {str(e)}")
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
║          HOW TO EXPORT COOKIES FROM TIKTOK                             ║
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
        description='TikTok Video Downloader with geo-restriction support and auto-retry',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic download
  %(prog)s https://www.tiktok.com/@user/video/123456789
  
  # With cookies (for geo-restrictions)
  %(prog)s --cookies tiktok_cookies.txt https://www.tiktok.com/@user/video/123456789
  
  # Multiple downloads
  %(prog)s -f urls.txt --cookies tiktok_cookies.txt
  
  # Specific quality
  %(prog)s --quality 720 https://www.tiktok.com/@user/video/123456789
  
  # Show cookie instructions
  %(prog)s --help-cookies
        """
    )
    
    parser.add_argument('url', nargs='?', help='TikTok video URL')
    parser.add_argument('-o', '--output', default='./tiktok_downloads',
                        help='Output folder (default: ./tiktok_downloads)')
    parser.add_argument('-f', '--file', help='File with URL list (one per line)')
    parser.add_argument('-q', '--quality', default='best',
                        help='Video quality: best, 720, 480, etc. (default: best)')
    parser.add_argument('--no-audio', action='store_true',
                        help='Download video only without audio')
    parser.add_argument('--cookies', metavar='FILE',
                        help='cookies.txt file for authentication (resolves geo-restrictions)')
    parser.add_argument('--no-geo-bypass', action='store_true',
                        help='Disable automatic geo-bypass')
    parser.add_argument('--help-cookies', action='store_true',
                        help='Show instructions for exporting cookies')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='Maximum retry attempts (default: 3)')
    
    args = parser.parse_args()
    
    if args.help_cookies:
        export_cookies_instructions()
        return
    
    downloader = TikTokDownloader(
        args.output,
        use_cookies=bool(args.cookies),
        cookies_file=args.cookies,
        geo_bypass=not args.no_geo_bypass
    )
    
    # Override retry config if specified
    if args.max_retries:
        from retry_utils import RetryConfig
        RetryConfig.MAX_DOWNLOAD_RETRIES = args.max_retries
    
    try:
        if args.file:
            logger.info(f"Reading URLs from file: {args.file}")
            with open(args.file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"Found {len(urls)} URLs")
            downloader.download_multiple(urls)
            
        elif args.url:
            downloader.download(args.url, args.quality, not args.no_audio)
            
        else:
            logger.info("╔═══════════════════════════════════════════════════════════╗")
            logger.info("║        TikTok Video Downloader - by gabrielrahbar          ║")
            logger.info("╚═══════════════════════════════════════════════════════════╝")
            logger.info("")
            logger.info("For videos with geo-restrictions, use: --cookies tiktok_cookies.txt")
            logger.info("For cookie instructions: --help-cookies")
            logger.info("")
            url = input("Enter TikTok video URL: ").strip()
            if url:
                downloader.download(url, args.quality, not args.no_audio)
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
