#!/usr/bin/env python3
"""
Daemon Manager for TikTok Monitor
Cross-platform background process management (Windows, macOS, Linux)
"""

import os
import sys
import signal
import time
import subprocess
import psutil
from pathlib import Path
from logger_manager import logger


class DaemonManager:
    """
    Manages daemon/background process for TikTok Monitor
    Cross-platform compatible (Windows, macOS, Linux)
    """
    
    def __init__(self, pid_file='tiktok-monitor.pid'):
        """
        Initialize daemon manager
        
        Args:
            pid_file: Path to PID file (default: ./tiktok-monitor.pid)
        """
        self.pid_file = Path(pid_file)
        
    def start_daemon(self, args):
        """
        Start monitor as background daemon/process
        
        Args:
            args: Arguments to pass to tiktok_monitor.py
            
        Returns:
            int: PID of daemon process, or None if failed
        """
        # Check if already running
        if self.is_running():
            pid = self.read_pid()
            print(f"⚠️  Daemon already running (PID {pid})")
            print(f"   Stop it first with: python tiktok_monitor.py --stop")
            return None
        
        print("🚀 Starting daemon in background...")
        
        # Prepare command
        cmd = [sys.executable, 'tiktok_monitor.py'] + args
        
        try:
            if os.name == 'nt':  # Windows
                # Windows: Use subprocess with detached process
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                process = subprocess.Popen(
                    cmd,
                    creationflags=creationflags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True
                )
                pid = process.pid
                
            else:  # Unix (Linux, macOS)
                # Fork process to create daemon
                pid = os.fork()
                
                if pid > 0:
                    # Parent process
                    time.sleep(0.5)  # Give child time to start
                    self.write_pid(pid)
                    print(f"✅ Daemon started successfully!")
                    print(f"   PID: {pid}")
                    print(f"   Check logs: tail -f logs/tiktok_monitor_*.log")
                    print(f"   Status: python tiktok_monitor.py --status")
                    print(f"   Stop: python tiktok_monitor.py --stop")
                    return pid
                else:
                    # Child process - become daemon
                    # Detach from parent
                    os.setsid()
                    
                    # Second fork to prevent zombie
                    pid = os.fork()
                    if pid > 0:
                        sys.exit(0)
                    
                    # Redirect standard file descriptors
                    sys.stdout.flush()
                    sys.stderr.flush()
                    
                    # Close stdin/stdout/stderr
                    with open(os.devnull, 'r') as f:
                        os.dup2(f.fileno(), sys.stdin.fileno())
                    with open(os.devnull, 'a+') as f:
                        os.dup2(f.fileno(), sys.stdout.fileno())
                        os.dup2(f.fileno(), sys.stderr.fileno())
                    
                    # Write PID
                    self.write_pid(os.getpid())
                    
                    # Execute the actual monitoring
                    # This happens in the child process
                    return None  # Child doesn't return
            
            # Windows continues here
            self.write_pid(pid)
            print(f"✅ Daemon started successfully!")
            print(f"   PID: {pid}")
            print(f"   Check logs: logs\\tiktok_monitor_*.log")
            print(f"   Status: python tiktok_monitor.py --status")
            print(f"   Stop: python tiktok_monitor.py --stop")
            return pid
            
        except Exception as e:
            print(f"❌ Failed to start daemon: {e}")
            logger.error(f"Daemon start failed: {e}", exc_info=True)
            return None
    
    def stop_daemon(self):
        """
        Stop running daemon gracefully
        
        Returns:
            bool: True if stopped successfully
        """
        if not self.is_running():
            print("⚠️  Daemon is not running")
            return False
        
        pid = self.read_pid()
        print(f"⏹️  Stopping daemon (PID {pid})...")
        
        try:
            process = psutil.Process(pid)
            
            # Send SIGTERM for graceful shutdown
            if os.name == 'nt':
                process.terminate()
            else:
                os.kill(pid, signal.SIGTERM)
            
            # Wait up to 10 seconds for process to stop
            for i in range(10):
                if not process.is_running():
                    break
                time.sleep(1)
                if i == 0:
                    print("   Waiting for graceful shutdown...")
            
            # If still running, force kill
            if process.is_running():
                print("   Force killing process...")
                process.kill()
                time.sleep(1)
            
            # Remove PID file
            self.remove_pid()
            
            print("✅ Daemon stopped successfully")
            return True
            
        except psutil.NoSuchProcess:
            print("⚠️  Process not found (already stopped?)")
            self.remove_pid()
            return False
        except Exception as e:
            print(f"❌ Failed to stop daemon: {e}")
            logger.error(f"Daemon stop failed: {e}", exc_info=True)
            return False
    
    def get_status(self):
        """
        Get daemon status
        
        Returns:
            dict: Status information
        """
        if not self.pid_file.exists():
            return {
                'running': False,
                'message': '🔴 Daemon is NOT running'
            }
        
        pid = self.read_pid()
        
        try:
            process = psutil.Process(pid)
            
            if process.is_running():
                # Get process info
                create_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                          time.localtime(process.create_time()))
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                return {
                    'running': True,
                    'pid': pid,
                    'started': create_time,
                    'cpu': cpu_percent,
                    'memory': memory_mb,
                    'message': f'🟢 Daemon is RUNNING (PID {pid})'
                }
            else:
                # PID exists but process not running
                self.remove_pid()
                return {
                    'running': False,
                    'message': '🔴 Daemon is NOT running (stale PID file removed)'
                }
                
        except psutil.NoSuchProcess:
            # PID file exists but process doesn't
            self.remove_pid()
            return {
                'running': False,
                'message': '🔴 Daemon is NOT running (stale PID file removed)'
            }
    
    def is_running(self):
        """
        Check if daemon is currently running
        
        Returns:
            bool: True if running
        """
        if not self.pid_file.exists():
            return False
        
        pid = self.read_pid()
        
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, ValueError):
            return False
    
    def write_pid(self, pid):
        """Write PID to file"""
        try:
            self.pid_file.write_text(str(pid))
            logger.debug(f"PID file written: {self.pid_file}")
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")
    
    def read_pid(self):
        """
        Read PID from file
        
        Returns:
            int: PID or None if error
        """
        try:
            return int(self.pid_file.read_text().strip())
        except Exception as e:
            logger.error(f"Failed to read PID file: {e}")
            return None
    
    def remove_pid(self):
        """Remove PID file"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.debug(f"PID file removed: {self.pid_file}")
        except Exception as e:
            logger.error(f"Failed to remove PID file: {e}")


# Global instance
daemon = DaemonManager()


# Convenience functions
def start_daemon(args):
    """Start daemon (convenience function)"""
    return daemon.start_daemon(args)


def stop_daemon():
    """Stop daemon (convenience function)"""
    return daemon.stop_daemon()


def get_status():
    """Get daemon status (convenience function)"""
    return daemon.get_status()


def is_running():
    """Check if daemon is running (convenience function)"""
    return daemon.is_running()
