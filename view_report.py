#!/usr/bin/env python3
"""
Display detailed download report
"""

import sqlite3
from datetime import datetime

def generate_report(db_file="tiktok_monitor.db"):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # General report
    cursor.execute('SELECT COUNT(*), SUM(views), SUM(likes) FROM videos')
    total_videos, total_views, total_likes = cursor.fetchone()
    
    # Videos by author
    cursor.execute('''
        SELECT author, COUNT(*), SUM(views), SUM(likes)
        FROM videos
        GROUP BY author
        ORDER BY COUNT(*) DESC
    ''')
    by_author = cursor.fetchall()
    
    # Last 10 downloaded videos
    cursor.execute('''
        SELECT title, author, download_date, views, likes
        FROM videos
        ORDER BY download_date DESC
        LIMIT 10
    ''')
    recent = cursor.fetchall()
    
    # Videos by day
    cursor.execute('''
        SELECT DATE(download_date) as day, COUNT(*)
        FROM videos
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    ''')
    by_day = cursor.fetchall()
    
    conn.close()
    
    # Print report
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║                  TikTok Monitor Report                      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    print(f"\n📊 GENERAL STATISTICS")
    print(f"{'─'*60}")
    print(f"Downloaded videos:  {total_videos:,}")
    print(f"Total views:        {total_views:,}" if total_views else "Total views:        N/A")
    print(f"Total likes:        {total_likes:,}" if total_likes else "Total likes:        N/A")
    
    print(f"\n👥 BY AUTHOR")
    print(f"{'─'*60}")
    for author, count, views, likes in by_author[:10]:
        print(f"@{author:<20} {count:>3} videos  |  {views or 0:>10,} views  |  {likes or 0:>8,} likes")
    
    print(f"\n📅 LAST 7 DAYS")
    print(f"{'─'*60}")
    for day, count in by_day:
        print(f"{day}  →  {count} videos")
    
    print(f"\n🆕 LAST 10 VIDEOS")
    print(f"{'─'*60}")
    for title, author, date, views, likes in recent:
        date_obj = datetime.fromisoformat(date)
        print(f"@{author:<15} | {title[:35]:<35} | {date_obj.strftime('%Y-%m-%d %H:%M')}")
    
    print()


if __name__ == "__main__":
    generate_report()