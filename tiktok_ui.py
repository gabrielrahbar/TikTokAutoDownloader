#!/usr/bin/env python3
"""
TikTok Auto Downloader - Modern GUI Interface
Built with PySide6 (Qt6) for professional desktop experience
Integrates seamlessly with existing TikTokMonitor backend
"""

import sys
import sqlite3
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QSpinBox, QCheckBox, QTextEdit, QFileDialog,
    QMessageBox, QHeaderView, QSystemTrayIcon, QMenu, QFrame,
    QGroupBox, QGridLayout, QComboBox, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QUrl
from PySide6.QtGui import QIcon, QAction, QFont, QColor, QDesktopServices, QPalette

# Import existing backend modules
from tiktok_monitor import TikTokMonitor
from daemon_manager import daemon
from notification_manager import notifier
from config_manager import get_config
from logger_manager import logger

# Import modern styles
from ui_styles import MODERN_STYLE, COLORS
from metric_card import MetricCard


class MonitorThread(QThread):
    """
    Background thread for running monitoring operations
    Prevents UI freezing during long operations
    """
    log_signal = Signal(str)  # Emit log messages to UI
    status_signal = Signal(str)  # Emit status updates
    
    def __init__(self, monitor, username=None):
        super().__init__()
        self.monitor = monitor
        self.username = username
        self.is_running = True
        
    def run(self):
        """Execute monitoring in background thread"""
        try: 
            if self.username:
                # Monitor single user
                self.log_signal.emit(f"🔍 Checking @{self.username}...")
                downloaded, error = self.monitor.monitor_user(self.username)
                if error:
                    self.log_signal.emit(f"❌ Error: {error. user_message}")
                else:
                    self.log_signal.emit(f"✅ {downloaded} new videos downloaded")
            else:
                # Monitor all users
                users = self.monitor.get_monitored_users()
                self.log_signal.emit(f"🔍 Checking {len(users)} users...")
                for user in users:
                    if not self.is_running:
                        break
                    downloaded, error = self.monitor.monitor_user(user)
                    self.log_signal.emit(f"@{user}: {downloaded} videos downloaded")
        except Exception as e:
            self.log_signal.emit(f"❌ Error: {str(e)}")
        finally:
            self.status_signal.emit("idle")
    
    def stop(self):
        """Stop monitoring thread gracefully"""
        self.is_running = False


class DashboardTab(QWidget):
    """
    Main dashboard with modern card-based design
    """
    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.parent_window = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize modern dashboard UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === HEADER ===
        header = QLabel("📊 Dashboard")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['dark']}; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # === METRICS CARDS (Grid) ===
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(15)
        
        self.videos_card = MetricCard("📥", "0", "Total Videos", COLORS['success'])
        self.users_card = MetricCard("👥", "0", "Monitored Users", COLORS['primary'])
        self.daemon_card = MetricCard("⚡", "Stopped", "Background Monitor", COLORS['danger'])
        
        metrics_layout.addWidget(self.videos_card)
        metrics_layout. addWidget(self.users_card)
        metrics_layout.addWidget(self.daemon_card)
        
        layout.addLayout(metrics_layout)
        
        # === BACKGROUND MONITORING CONTROL ===
        daemon_group = QGroupBox("🔧 Background Monitoring")
        daemon_layout = QHBoxLayout()
        daemon_layout.setSpacing(10)
        
        self.start_daemon_btn = QPushButton("🚀 Start Background Monitor")
        self.start_daemon_btn.clicked.connect(self.start_daemon)
        self.start_daemon_btn.setMinimumHeight(45)
        self.start_daemon_btn.setStyleSheet(f"background-color:  {COLORS['success']}; color: white; font-weight: bold;")
        
        self.stop_daemon_btn = QPushButton("⏹️ Stop Background Monitor")
        self.stop_daemon_btn.clicked. connect(self.stop_daemon)
        self.stop_daemon_btn.setEnabled(False)
        self.stop_daemon_btn.setMinimumHeight(45)
        self.stop_daemon_btn.setStyleSheet(f"background-color: {COLORS['danger']}; color: white; font-weight: bold;")
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_metrics)
        self.refresh_btn.setMinimumHeight(45)
        self.refresh_btn.setStyleSheet(f"background-color:  {COLORS['light']}; color: black; font-weight: bold;")
        
        daemon_layout.addWidget(self.start_daemon_btn, 2)
        daemon_layout.addWidget(self.stop_daemon_btn, 2)
        daemon_layout.addWidget(self.refresh_btn, 1)
        
        daemon_group.setLayout(daemon_layout)
        layout.addWidget(daemon_group)
        
        # === QUICK ACTIONS ===
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        self.check_now_btn = QPushButton("🔎 Check All Users Now")
        self.check_now_btn.clicked.connect(self.check_now)
        self.check_now_btn.setMinimumHeight(45)
        
        self.open_folder_btn = QPushButton("📁 Open Downloads")
        self.open_folder_btn.clicked.connect(self. open_downloads_folder)
        self.open_folder_btn. setMinimumHeight(45)
        self.open_folder_btn.setStyleSheet(f"background-color: {COLORS['light']}; color: black; font-weight: bold;")
        
        actions_layout.addWidget(self.check_now_btn, 2)
        actions_layout.addWidget(self.open_folder_btn, 1)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # === ACTIVITY LOG ===
        log_group = QGroupBox("📜 Activity Log")
        log_layout = QVBoxLayout()
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        self.info_text.setPlaceholderText("Activity logs will appear here...")
        
        log_layout.addWidget(self.info_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Timer for auto-refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_metrics)
        self.timer.start(5000)
        
        # Initial load
        self.refresh_metrics()
    
    def refresh_metrics(self):
        """Update dashboard metrics"""
        try:
            conn = sqlite3.connect(self.monitor.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM videos')
            total_videos = cursor.fetchone()[0]
            
            cursor. execute('SELECT COUNT(*) FROM monitored_users WHERE enabled = 1')
            total_users = cursor.fetchone()[0]
            
            conn.close()
            
            # Update cards
            self.videos_card.update_value(total_videos)
            self.users_card.update_value(total_users)
            
            # Update daemon status
            status = daemon.get_status()
            if status['running']:
                self.daemon_card.update_value("🟢 Running")
                self.daemon_card.color = COLORS['success']
                self.start_daemon_btn.setEnabled(False)
                self.stop_daemon_btn.setEnabled(True)
            else:
                self.daemon_card.update_value("🔴 Stopped")
                self.daemon_card. color = COLORS['danger']
                self.start_daemon_btn.setEnabled(True)
                self.stop_daemon_btn. setEnabled(False)
                
        except Exception as e:
            self.log_message(f"⚠️ Error:  {e}")
    
    def start_daemon(self):
        """Start daemon"""
        if daemon.is_running():
            QMessageBox.warning(self, "Already Running", "Background monitor is already running!")
            return
        
        try:
            import subprocess
            interval = get_config('monitor.interval_minutes', 30)
            cmd = [sys.executable, 'tiktok_monitor.py', '--daemon', '--interval', str(interval)]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess. DEVNULL, stdin=subprocess.DEVNULL)
            
            QTimer.singleShot(2000, self.refresh_metrics)
            self.log_message(f"✅ Background monitor started (interval: {interval} min)")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start background monitor:\n{e}")
    
    def stop_daemon(self):
        """Stop daemon"""
        try:
            daemon.stop_daemon()
            self.log_message("⏹️ Background monitor stopped")
            QTimer.singleShot(1000, self.refresh_metrics)
        except Exception as e: 
            QMessageBox.critical(self, "Error", f"Failed to stop background monitor:\n{e}")
    
    def check_now(self):
        """Check all users once"""
        users = self.monitor.get_monitored_users()
        if not users:
            QMessageBox. warning(self, "No Users", "Add users to monitor first!")
            return
        
        self.log_message("🔍 Starting check for all users...")
        self.check_now_btn.setEnabled(False)
        
        self.thread = MonitorThread(self. monitor)
        self.thread.log_signal.connect(self.log_message)
        self.thread. status_signal.connect(lambda: self.check_now_btn.setEnabled(True))
        self.thread. finished.connect(lambda: self.parent_window.users_tab.refresh_users())
        self.thread.start()
    
    def open_downloads_folder(self):
        """Open downloads folder"""
        import platform
        import subprocess
        
        folder = Path(self.monitor.output_dir)
        if not folder.exists():
            QMessageBox.warning(self, "Not Found", "Downloads folder doesn't exist yet!")
            return
        
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess. Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open folder:\n{e}")
    
    def log_message(self, message):
        """Add log message with timestamp"""
        timestamp = datetime. now().strftime('%H:%M:%S')
        self.info_text.append(f"<span style='color: #7f8c8d;'>[{timestamp}]</span> {message}")


class UsersTab(QWidget):
    """
    User management tab with table view and controls
    """
    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.init_ui()
        
    def init_ui(self):
        """Initialize users tab UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === HEADER ===
        header = QLabel("👥 User Management")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['dark']}; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # === ADD USER SECTION ===
        add_group = QGroupBox("➕ Add New User")
        add_layout = QHBoxLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter TikTok username (without @)...")
        self.username_input.returnPressed.connect(self.add_user)
        self.username_input.setMinimumHeight(45)
        
        self.add_btn = QPushButton("Add User")
        self.add_btn.clicked.connect(self. add_user)
        self.add_btn.setMinimumHeight(45)
        self.add_btn.setMinimumWidth(120)
        
        add_layout.addWidget(self.username_input, 4)
        add_layout.addWidget(self.add_btn, 1)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # === USERS TABLE ===
        table_label = QLabel("📋 Monitored Users")
        table_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        table_label.setStyleSheet(f"color: {COLORS['dark']}; margin-top: 10px;")
        layout.addWidget(table_label)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "Username", "Status", "Last Check", "Total Videos", "In Database", "Actions", ""
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setEditTriggers(QTableWidget. NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.users_table)
        
        # === CONTROLS ===
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self. refresh_users)
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setStyleSheet(f"background-color: {COLORS['light']}; color: black; font-weight: bold;")
        
        self.show_disabled_cb = QCheckBox("Show Disabled Users")
        self.show_disabled_cb.stateChanged.connect(self.refresh_users)
        
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.show_disabled_cb)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        self.refresh_users()
    
    def refresh_users(self):
        """Reload users table from database"""
        show_disabled = self.show_disabled_cb.isChecked()
        users = self.monitor.list_monitored_users(show_disabled=show_disabled)
        
        self.users_table.setRowCount(len(users))
        
        for row, (username, last_check, total, enabled, last_ts, db_videos) in enumerate(users):
            # Username
            username_item = QTableWidgetItem(f"@{username}")
            username_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.users_table.setItem(row, 0, username_item)
            
            # Status
            status_item = QTableWidgetItem("🟢 Active" if enabled else "🔴 Disabled")
            status_item.setForeground(QColor(COLORS['success'] if enabled else COLORS['danger']))
            status_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.users_table.setItem(row, 1, status_item)
            
            # Last check
            last_check_str = datetime.fromisoformat(last_check).strftime('%Y-%m-%d %H:%M') if last_check else 'Never'
            self.users_table.setItem(row, 2, QTableWidgetItem(last_check_str))
            
            # Total videos
            self.users_table.setItem(row, 3, QTableWidgetItem(str(total)))
            
            # In database
            self.users_table. setItem(row, 4, QTableWidgetItem(str(db_videos)))
            
            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(5)
            
            if enabled:
                disable_btn = QPushButton("❌")
                disable_btn.setToolTip("Disable user")
                disable_btn.setMaximumWidth(40)
                disable_btn.clicked.connect(lambda checked, u=username: self.disable_user(u))
                actions_layout.addWidget(disable_btn)
            else:
                enable_btn = QPushButton("♻️")
                enable_btn.setToolTip("Enable user")
                enable_btn.setMaximumWidth(40)
                enable_btn.clicked.connect(lambda checked, u=username:  self.enable_user(u))
                actions_layout.addWidget(enable_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Delete permanently")
            delete_btn.setMaximumWidth(40)
            delete_btn.setStyleSheet(f"background-color: {COLORS['danger']}; color: white;")
            delete_btn.clicked.connect(lambda checked, u=username: self.delete_user(u))
            actions_layout. addWidget(delete_btn)
            
            actions_widget.setLayout(actions_layout)
            self.users_table.setCellWidget(row, 5, actions_widget)
    
    def add_user(self):
        """Add new user to monitoring"""
        username = self.username_input.text().strip().lstrip('@')
        if not username:
            QMessageBox.warning(self, "Invalid Input", "Please enter a username!")
            return
        
        success = self.monitor.add_user_to_monitor(username)
        if success: 
            QMessageBox.information(self, "Success", f"User @{username} added to monitoring!")
            self.username_input.clear()
            self.refresh_users()
        else:
            QMessageBox.warning(self, "Error", f"Failed to add user @{username}")
    
    def disable_user(self, username):
        """Disable user monitoring"""
        reply = QMessageBox.question(self, "Confirm", f"Disable monitoring for @{username}?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.monitor.remove_user_from_monitor(username)
            self.refresh_users()
    
    def enable_user(self, username):
        """Re-enable user monitoring"""
        self.monitor.enable_user(username)
        self.refresh_users()
    
    def delete_user(self, username):
        """Permanently delete user"""
        reply = QMessageBox.warning(self, "Permanent Deletion",
                                     f"⚠️ Permanently delete @{username} and all associated videos from database?\n\n"
                                     f"Downloaded files will NOT be deleted.\n\nThis cannot be undone! ",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self. monitor.db_file)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM videos WHERE author = ?', (username,))
                cursor.execute('DELETE FROM monitored_users WHERE username = ?', (username,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Deleted", f"User @{username} deleted successfully!")
                self.refresh_users()
            except Exception as e: 
                QMessageBox.critical(self, "Error", f"Failed to delete user:  {e}")


class DownloadsTab(QWidget):
    """
    Downloaded videos browser with search and filtering
    """
    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.init_ui()
        
    def init_ui(self):
        """Initialize downloads tab UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === HEADER ===
        header = QLabel("📥 Downloads")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['dark']}; margin-bottom:  10px;")
        layout.addWidget(header)
        
        # === SEARCH/FILTER ===
        filter_group = QGroupBox("🔍 Search & Filter")
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, author, or video ID...")
        self.search_input.textChanged.connect(self.refresh_downloads)
        self.search_input.setMinimumHeight(40)
        
        self.author_filter = QComboBox()
        self.author_filter.addItem("All Authors")
        self.author_filter.currentTextChanged.connect(self.refresh_downloads)
        self.author_filter.setMinimumHeight(40)
        self.author_filter.setMinimumWidth(200)
        
        filter_layout.addWidget(self. search_input, 3)
        filter_layout.addWidget(self.author_filter, 1)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # === DOWNLOADS TABLE ===
        self.downloads_table = QTableWidget()
        self.downloads_table.setColumnCount(7)
        self.downloads_table.setHorizontalHeaderLabels([
            "Title", "Author", "Upload Date", "Download Date", "Views", "Likes", "File Path"
        ])
        self.downloads_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.downloads_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.downloads_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.downloads_table)
        
        # === CONTROLS ===
        controls_layout = QHBoxLayout()
        
        self.refresh_downloads_btn = QPushButton("🔄 Refresh")
        self.refresh_downloads_btn. clicked.connect(self.refresh_downloads)
        self.refresh_downloads_btn.setMinimumHeight(40)
        self.refresh_downloads_btn.setStyleSheet(f"background-color:  {COLORS['light']}; color: black; font-weight:  bold;")
        
        self.export_btn = QPushButton("📊 Export to CSV")
        self.export_btn.clicked.connect(self. export_to_csv)
        self.export_btn.setMinimumHeight(40)
        
        controls_layout.addWidget(self.refresh_downloads_btn)
        controls_layout.addWidget(self.export_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        self.refresh_downloads()
        self.load_authors()
    
    def load_authors(self):
        """Load unique authors for filter dropdown"""
        try:
            conn = sqlite3.connect(self.monitor.db_file)
            cursor = conn. cursor()
            cursor.execute('SELECT DISTINCT author FROM videos ORDER BY author')
            authors = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            self. author_filter.clear()
            self.author_filter.addItem("All Authors")
            self.author_filter.addItems([f"@{a}" for a in authors])
        except Exception as e:
            logger.error(f"Error loading authors: {e}")
    
    def refresh_downloads(self):
        """Reload downloads table with filters applied"""
        try:
            conn = sqlite3.connect(self. monitor.db_file)
            cursor = conn.cursor()
            
            # Build query with filters
            query = 'SELECT title, author, upload_date, download_date, views, likes, file_path FROM videos WHERE 1=1'
            params = []
            
            # Search filter
            search_text = self.search_input.text().strip()
            if search_text:
                query += ' AND (title LIKE ? OR author LIKE ? OR id LIKE ?)'
                search_pattern = f'%{search_text}%'
                params.extend([search_pattern, search_pattern, search_pattern])
            
            # Author filter
            author = self.author_filter.currentText()
            if author and author != "All Authors":
                query += ' AND author = ?'
                params.append(author. lstrip('@'))
            
            query += ' ORDER BY download_date DESC LIMIT 100'
            
            cursor.execute(query, params)
            videos = cursor.fetchall()
            conn.close()
            
            self.downloads_table.setRowCount(len(videos))
            
            for row, (title, author, upload_date, download_date, views, likes, file_path) in enumerate(videos):
                # Title
                title_item = QTableWidgetItem(title[: 60] + "..." if len(title) > 60 else title)
                title_item.setToolTip(title)
                self.downloads_table.setItem(row, 0, title_item)
                
                # Author
                author_item = QTableWidgetItem(f"@{author}")
                author_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.downloads_table.setItem(row, 1, author_item)
                
                # Upload date
                self.downloads_table.setItem(row, 2, QTableWidgetItem(upload_date or 'N/A'))
                
                # Download date
                download_str = datetime.fromisoformat(download_date).strftime('%Y-%m-%d %H:%M') if download_date else 'N/A'
                self.downloads_table.setItem(row, 3, QTableWidgetItem(download_str))
                
                # Views
                views_item = QTableWidgetItem(f"{views:,}" if views else '0')
                views_item. setForeground(QColor(COLORS['info']))
                self.downloads_table. setItem(row, 4, views_item)
                
                # Likes
                likes_item = QTableWidgetItem(f"{likes:,}" if likes else '0')
                likes_item.setForeground(QColor(COLORS['danger']))
                self.downloads_table.setItem(row, 5, likes_item)
                
                # File path
                path_item = QTableWidgetItem(str(file_path))
                path_item.setToolTip(str(file_path))
                self.downloads_table.setItem(row, 6, path_item)
                
        except Exception as e:
            logger.error(f"Error refreshing downloads: {e}")
    
    def export_to_csv(self):
        """Export downloads to CSV file"""
        filename, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "tiktok_downloads.csv", "CSV Files (*. csv)")
        if not filename:
            return
        
        try:
            import csv
            conn = sqlite3.connect(self. monitor.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM videos')
            videos = cursor.fetchall()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'URL', 'Title', 'Author', 'Upload Date', 'Timestamp',
                                 'Download Date', 'File Path', 'Likes', 'Views', 'Status'])
                writer.writerows(videos)
            
            conn.close()
            QMessageBox.information(self, "Success", f"Exported {len(videos)} videos to {filename}")
            
        except Exception as e: 
            QMessageBox.critical(self, "Error", f"Export failed: {e}")


class SettingsTab(QWidget):
    """
    Settings and configuration tab with scroll support
    """
    def __init__(self, monitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.init_ui()
        
    def init_ui(self):
        """Initialize settings tab UI with scroll area"""
        # Main layout (no scroll)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout. setSpacing(0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt. ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget inside scroll
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === HEADER ===
        header = QLabel("⚙️ Settings")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['dark']}; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # === MONITORING SETTINGS ===
        monitor_group = QGroupBox("⚙️ Monitoring Settings")
        monitor_layout = QGridLayout()
        monitor_layout.setSpacing(20)
        monitor_layout.setVerticalSpacing(20)
        
        # Interval
        interval_label = QLabel("Check Interval:")
        interval_label. setStyleSheet(f"color: {COLORS['dark']}; font-weight: 600; font-size: 14px;")
        interval_label.setMinimumWidth(180)
        
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox. setMinimum(5)
        self.interval_spinbox.setMaximum(1440)
        self.interval_spinbox.setValue(get_config('monitor. interval_minutes', 30))
        self.interval_spinbox.setSuffix(" minutes")
        self.interval_spinbox.setMinimumHeight(45)
        self.interval_spinbox.setMaximumWidth(300)
        
        # Max videos
        max_videos_label = QLabel("Max Videos Per Check:")
        max_videos_label.setStyleSheet(f"color: {COLORS['dark']}; font-weight: 600; font-size: 14px;")
        max_videos_label.setMinimumWidth(180)
        
        self.max_videos_spinbox = QSpinBox()
        self.max_videos_spinbox.setMinimum(1)
        self.max_videos_spinbox. setMaximum(50)
        self.max_videos_spinbox.setValue(get_config('monitor.max_videos_per_check', 5))
        self.max_videos_spinbox.setMinimumHeight(45)
        self.max_videos_spinbox.setMaximumWidth(300)
        
        monitor_layout.addWidget(interval_label, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        monitor_layout.addWidget(self.interval_spinbox, 0, 1, Qt.AlignLeft)
        monitor_layout.addWidget(max_videos_label, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        monitor_layout.addWidget(self.max_videos_spinbox, 1, 1, Qt.AlignLeft)
        monitor_layout.setColumnStretch(2, 1)
        
        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)
        
        # === DOWNLOAD SETTINGS ===
        download_group = QGroupBox("📥 Download Settings")
        download_layout = QGridLayout()
        download_layout.setSpacing(15)
        
        output_label = QLabel("Output Directory:")
        output_label.setStyleSheet(f"color: {COLORS['dark']}; font-weight: 600; font-size: 14px;")
        output_label.setMinimumWidth(180)
        
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText(str(self.monitor.output_dir))
        self.output_dir_input.setReadOnly(True)
        self.output_dir_input.setMinimumHeight(45)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn. clicked.connect(self.browse_output_dir)
        self.browse_btn.setMinimumHeight(45)
        self.browse_btn.setMaximumWidth(120)
        self.browse_btn.setStyleSheet(f"background-color: {COLORS['light']}; color: black; font-weight: bold;")
        
        download_layout.addWidget(output_label, 0, 0, Qt.AlignLeft)
        download_layout.addWidget(self.output_dir_input, 0, 1)
        download_layout.addWidget(self.browse_btn, 0, 2)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        # === VPN / RESTRICTED COUNTRIES INFO ===
        vpn_group = QGroupBox("🌍 Geographic Restrictions")
        vpn_layout = QVBoxLayout()
        vpn_layout.setSpacing(10)
        
        info_label = QLabel(
            "⚠️ <b>Important:</b> TikTok restricts access in certain countries (Italy 🇮🇹, UK 🇬🇧, Hong Kong 🇭🇰). <br><br>"
            "🔒 <b>To download videos from restricted regions, you MUST use a VPN</b> connected to an unrestricted country: <br><br>"
            "<b>Recommended VPN locations:</b><br>"
            "   • 🇺🇸 USA (Best compatibility)<br>"
            "   • 🇨🇦 Canada<br>"
            "   • 🇩🇪 Germany<br>"
            "   • 🇫🇷 France<br>"
            "   • 🇦🇺 Australia<br>"
            "   • 🇯🇵 Japan<br>"
            "   • 🇪🇸 Spain<br><br>"
            "📄 For a complete list of restricted countries, see <a href='#' style='color: #3498db; font-weight: bold;'>docs/restricted_countries.md</a>"
        )
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(False)
        info_label.linkActivated.connect(self.open_restricted_countries_doc)
        info_label.setStyleSheet(f"""
            QLabel {{
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius:  8px;
                padding: 20px;
                color: {COLORS['dark']};
                font-size: 13px;
                line-height: 1.6;
            }}
        """)
        
        vpn_layout. addWidget(info_label)
        vpn_group.setLayout(vpn_layout)
        layout.addWidget(vpn_group)
        
        # === NOTIFICATIONS ===
        notif_group = QGroupBox("🔔 Notifications")
        notif_layout = QHBoxLayout()
        notif_layout.setSpacing(15)
        
        self.notifications_cb = QCheckBox("Enable Desktop Notifications")
        self.notifications_cb.setChecked(notifier.enabled)
        self.notifications_cb.stateChanged.connect(self.toggle_notifications)
        
        self.test_notif_btn = QPushButton("Test Notification")
        self.test_notif_btn.clicked.connect(self.test_notification)
        self.test_notif_btn.setMinimumHeight(40)
        self.test_notif_btn.setMaximumWidth(180)
        self.test_notif_btn. setStyleSheet(f"background-color: {COLORS['light']}; color: black; font-weight: bold;")
        
        notif_layout.addWidget(self.notifications_cb)
        notif_layout.addWidget(self.test_notif_btn)
        notif_layout.addStretch()
        
        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)
        
        # === SAVE BUTTON ===
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setMinimumHeight(50)
        save_btn.setMaximumWidth(200)
        save_btn.setStyleSheet(f"background-color: {COLORS['success']}; color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(save_btn, 0, Qt.AlignLeft)
        
        # Add some bottom padding
        layout.addSpacing(30)
        
        # Set content layout
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        
        # Add scroll to main layout
        main_layout. addWidget(scroll)
        self.setLayout(main_layout)
    
    def open_restricted_countries_doc(self):
        """Open restricted_countries.md file"""
        doc_path = Path("docs/restricted_countries.md")
        if doc_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(doc_path. absolute())))
        else:
            QMessageBox.warning(self, "File Not Found",
                              f"The file 'docs/restricted_countries.md' was not found.\n\n"
                              f"Expected location: {doc_path. absolute()}")
    
    def browse_output_dir(self):
        """Open directory browser for output folder"""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", str(self.monitor.output_dir))
        if directory: 
            self.output_dir_input.setText(directory)
    
    def toggle_notifications(self, state):
        """Toggle notifications on/off"""
        if state == Qt.Checked:
            notifier.enable()
        else:
            notifier.disable()
        self.monitor._save_notification_preference()
    
    def test_notification(self):
        """Send test notification"""
        if not notifier.enabled:
            QMessageBox.warning(self, "Disabled", "Enable notifications first!")
            return
        
        notifier.send(
            title="🔔 Test Notification",
            message="Notifications are working correctly! ",
            timeout=5
        )
    
    def save_settings(self):
        """Save settings to config file"""
        try:
            from config_manager import ConfigManager
            config = ConfigManager()
            
            config.set('monitor. interval_minutes', self.interval_spinbox.value())
            config.set('monitor.max_videos_per_check', self.max_videos_spinbox.value())
            config.set('monitor. output_dir', self.output_dir_input.text())
            
            config.save_config()
            
            QMessageBox.information(self, "Success", "Settings saved successfully!\n\nRestart the application for all changes to take effect.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")


class MainWindow(QMainWindow):
    """
    Main application window with tabs and system tray
    """
    def __init__(self):
        super().__init__()
        
        # Apply modern stylesheet
        self.setStyleSheet(MODERN_STYLE)
        
        self.monitor = TikTokMonitor()
        self.init_ui()
        self.setup_system_tray()
        
    def init_ui(self):
        """Initialize main window UI"""
        self.setWindowTitle("TikTok Auto Downloader")
        self.setGeometry(100, 100, 1300, 850)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)
        
        # Create tab widget
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        
        # Add tabs
        self.dashboard_tab = DashboardTab(self.monitor, self)
        self.users_tab = UsersTab(self.monitor, self)
        self.downloads_tab = DownloadsTab(self.monitor, self)
        self.settings_tab = SettingsTab(self.monitor, self)
        
        tabs. addTab(self.dashboard_tab, "📊 Dashboard")
        tabs.addTab(self.users_tab, "👥 Users")
        tabs.addTab(self. downloads_tab, "📥 Downloads")
        tabs.addTab(self.settings_tab, "⚙️ Settings")
        
        layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready | TikTok Auto Downloader v2.6")
        self.statusBar().setStyleSheet("padding: 5px;")
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this system")
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to use an icon
        try:
            self.tray_icon.setIcon(QIcon. fromTheme("download"))
        except:
            pass
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Window", self)
        show_action.triggered. connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide Window", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        start_daemon_action = QAction("🚀 Start Background Monitor", self)
        start_daemon_action.triggered.connect(self.dashboard_tab.start_daemon)
        tray_menu.addAction(start_daemon_action)
        
        stop_daemon_action = QAction("⏹️ Stop Background Monitor", self)
        stop_daemon_action.triggered.connect(self.dashboard_tab.stop_daemon)
        tray_menu.addAction(stop_daemon_action)
        
        tray_menu. addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Tray icon click
        self.tray_icon. activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon. DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self. show()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "TikTok Auto Downloader",
                "Application minimized to tray.  Double-click icon to restore.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            event.accept()


def main():
    """Main entry point for GUI application"""
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    app.setApplicationName("TikTok Auto Downloader")
    app.setOrganizationName("TikTokMonitor")
    
    # === FORCE LIGHT COLOR PALETTE ===
    palette = QPalette()
    
    # White backgrounds
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(249, 249, 249))
    
    # Black text
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette. ButtonText, QColor(0, 0, 0))
    
    # Light gray buttons
    palette.setColor(QPalette.Button, QColor(236, 240, 241))
    
    # Blue selection
    palette.setColor(QPalette. Highlight, QColor(52, 152, 219))
    palette.setColor(QPalette. HighlightedText, QColor(255, 255, 255))
    
    # Disabled text
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 150))
    palette.setColor(QPalette. Disabled, QPalette.WindowText, QColor(150, 150, 150))
    
    # Apply palette
    app.setPalette(palette)
    app.setStyle("Fusion")
    app.setStyleSheet(MODERN_STYLE)
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)