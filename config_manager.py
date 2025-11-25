#!/usr/bin/env python3
"""
Configuration Manager for TikTok Auto Downloader
Handles loading settings from YAML config file with fallback to defaults
"""

import os
import yaml
from pathlib import Path


class ConfigManager:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_file="config.yaml"):
        if self._config is not None:
            return

        self.config_file = config_file
        self.default_config = {
            'monitor': {
                'interval_minutes': 30,
                'output_dir': './tiktok_downloads',
                'max_videos_per_check': 5,
                'anti_bot_delays': {
                    'between_downloads': [5, 15],
                    'between_users': [10, 30]
                }
            },
            'download': {
                'quality': 'best',
                'with_audio': True,
                'geo_bypass': True,
                'geo_bypass_country': 'US'
            },
            'notifications': {
                'enabled': False,
                'timeout': 5
            },
            'database': {
                'db_file': 'tiktok_monitor.db'
            },
            'logging': {
                'log_dir': 'logs',
                'log_level': 'INFO'
            }
        }
        self.load_config()

    def load_config(self):
        """Load configuration from YAML file or use defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self._config = self.merge_config(self.default_config, loaded_config)
                    else:
                        self._config = self.default_config
                print(f"✅ Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"❌ Error loading config file: {e}. Using defaults.")
                self._config = self.default_config
        else:
            print(f"⚠️  Config file {self.config_file} not found. Using defaults.")
            self._config = self.default_config

    def merge_config(self, default, user):
        """Recursively merge user config with defaults"""
        if not isinstance(user, dict):
            return user

        merged = default.copy()
        for key, value in user.items():
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = self.merge_config(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value
        return merged

    def get(self, key_path, default=None):
        """Get config value by dot-separated path (e.g., 'monitor.interval_minutes')"""
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path, value):
        """Set config value by dot-separated path"""
        keys = key_path.split('.')
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config file: {e}")


# Global instance
config_manager = ConfigManager()


# Convenience functions
def get_config(key_path, default=None):
    return config_manager.get(key_path, default)


def set_config(key_path, value):
    return config_manager.set(key_path, value)


def save_config():
    return config_manager.save_config()