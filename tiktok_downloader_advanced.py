#!/usr/bin/env python3
"""
TikTok Video Downloader - Advanced Version with geo-restriction support
Download videos from TikTok bypassing geographical restrictions
"""

import argparse
import yt_dlp
import os
from pathlib import Path

class TikTokDownloader:
    def __init__(self, output_dir="./tiktok_downloads", use_cookies=False, cookies_file=None, geo_bypass=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_cookies = use_cookies
        self.cookies_file = cookies_file
        self.geo_bypass = geo_bypass
    
    def download(self, url, quality='best', with_audio=True):
        """
        Download a TikTok video with geo-restriction support
        
        Args:
            url: Video URL
            quality: Video quality ('best', 'worst', or specific resolution)
            with_audio: Include audio in download
        """
        format_string = 'best' if quality == 'best' else f'best[height<={quality}]'
        
        ydl_opts = {
            'format': format_string,
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
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
        }
        
        if self.geo_bypass:
            ydl_opts['geo_bypass'] = True
            ydl_opts['geo_bypass_country'] = 'US'
        
        if self.use_cookies and self.cookies_file:
            if os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file
                print(f"🍪 Using cookies from: {self.cookies_file}")
            else:
                print(f"⚠️  Cookie file not found: {self.cookies_file}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"\n📥 Downloading from: {url}")
                print(f"📁 Output folder: {self.output_dir}")
                print(f"🌍 Geo-bypass: {'Enabled (USA)' if self.geo_bypass else 'Disabled'}\n")
                
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                print(f"\n✓ Download completed!")
                print(f"📄 File: {filename}")
                print(f"📝 Title: {info.get('title', 'N/A')}")
                print(f"👤 Author: {info.get('uploader', 'Unknown')}")
                print(f"👁️  Views: {info.get('view_count', 0):,}")
                print(f"❤️  Likes: {info.get('like_count', 0):,}")
                print(f"💬 Comments: {info.get('comment_count', 0):,}")
                
                return filename
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'geo' in error_msg.lower() or 'not available' in error_msg.lower():
                print(f"\n✗ Geo-restriction error detected!")
                print(f"💡 Suggestions:")
                print(f"   1. Use --cookies option to import your TikTok cookies")
                print(f"   2. Try with an active VPN")
                print(f"   3. Some videos might be private or removed")
            else:
                print(f"\n✗ Download error: {error_msg}")
            return None
        except Exception as e:
            print(f"\n✗ Unexpected error: {str(e)}")
            return None
    
    def download_multiple(self, urls):
        """Download multiple videos"""
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"Video {i}/{len(urls)}")
            print(f"{'='*60}")
            result = self.download(url)
            results.append(result)
        
        successful = sum(1 for r in results if r is not None)
        print(f"\n{'='*60}")
        print(f"Completed downloads: {successful}/{len(urls)}")
        print(f"{'='*60}")
        
        return results


def export_cookies_instructions():
    """Show instructions for exporting cookies"""
    instructions = """
╔════════════════════════════════════════════════════════════════════════╗
║          HOW TO EXPORT COOKIES FROM TIKTOK                             ║
╚════════════════════════════════════════════════════════════════════════╝

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
        description='TikTok Video Downloader with geo-restriction support',
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
    
    if args.file:
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        downloader.download_multiple(urls)
    elif args.url:
        downloader.download(args.url, args.quality, not args.no_audio)
    else:
        print("╔════════════════════════════════════════════════════════════╗")
        print("║        TikTok Video Downloader - by gabrielrahbar          ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("\nFor videos with geo-restrictions, use: --cookies tiktok_cookies.txt")
        print("For cookie instructions: --help-cookies\n")
        url = input("Enter TikTok video URL: ").strip()
        if url:
            downloader.download(url, args.quality, not args.no_audio)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()