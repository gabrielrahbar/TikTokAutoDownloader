#!/usr/bin/env python3
"""
Quick management of monitored users
"""

import argparse
import sys
from datetime import datetime
from tiktok_monitor import TikTokMonitor

def main():
    parser = argparse.ArgumentParser(
        description='Manage monitored TikTok users',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List users
  %(prog)s --list
  
  # Add user
  %(prog)s --add charlidamelio
  
  # Remove user (disable)
  %(prog)s --remove charlidamelio
  
  # Delete permanently
  %(prog)s --delete charlidamelio
  
  # Re-enable user
  %(prog)s --enable charlidamelio
  
  # Show all (including disabled)
  %(prog)s --list --all
        """
    )
    
    parser.add_argument('--list', '-l', action='store_true',
                        help='List monitored users')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Show disabled users too')
    parser.add_argument('--add', metavar='USERNAME',
                        help='Add user to monitoring')
    parser.add_argument('--remove', metavar='USERNAME',
                        help='Remove user from monitoring')
    parser.add_argument('--delete', metavar='USERNAME',
                        help='Permanently delete user and videos')
    parser.add_argument('--enable', metavar='USERNAME',
                        help='Re-enable disabled user')
    
    args = parser.parse_args()
    
    monitor = TikTokMonitor()
    
    if args.list:
        users = monitor.list_monitored_users(show_disabled=args.all)
        
        if not users:
            print("📋 No monitored users")
            return
        
        print(f"\n{'='*80}")
        print(f"{'Username':<20} {'Status':<12} {'Last Check':<20} {'Total Videos':<10} {'In DB':<10}")
        print(f"{'='*80}")
        
        for username, last_check, total, enabled, db_videos in users:
            status = "🟢 Active" if enabled else "🔴 Disabled"
            last_check_str = datetime.fromisoformat(last_check).strftime('%Y-%m-%d %H:%M') if last_check else 'Never'
            print(f"@{username:<19} {status:<12} {last_check_str:<20} {total:<13} {db_videos:<10}")
        
        print(f"{'='*80}")
        print(f"Total: {len(users)} users")
    
    elif args.add:
        username = args.add.lstrip('@')
        monitor.add_user_to_monitor(username)
    
    elif args.remove:
        username = args.remove.lstrip('@')
        monitor.remove_user_from_monitor(username)
    
    elif args.delete:
        username = args.delete.lstrip('@')
        monitor.delete_user_permanently(username)
    
    elif args.enable:
        username = args.enable.lstrip('@')
        monitor.enable_user(username)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()