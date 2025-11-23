#!/usr/bin/env python3
"""
Verify that all dependencies are installed correctly
"""

import sys
import os

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required!")
        return False
    
    print("✅ Python version OK")
    return True

def check_module(module_name, package_name=None):
    """Check if a module is installed"""
    if package_name is None:
        package_name = module_name
    
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'N/A')
        if hasattr(module, 'version'):
            version = getattr(module.version, '__version__', version)
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name} not installed!")
        print(f"   Install with: pip install {package_name}")
        return False

def check_files():
    """Check that necessary files exist"""
    files = [
        'requirements.txt',
        'tiktok_monitor.py',
        'tiktok_downloader_advanced.py',
    ]
    
    all_ok = True
    for file in files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"⚠️  {file} not found")
            all_ok = False
    
    return all_ok

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        TikTok Monitor Installation Check                  ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    results = []
    
    # Check Python
    print("📋 PYTHON VERSION")
    print("─" * 60)
    results.append(check_python_version())
    print()
    
    # Check modules
    print("📦 DEPENDENCIES")
    print("─" * 60)
    results.append(check_module('yt_dlp'))
    results.append(check_module('sqlite3'))
    results.append(check_module('requests'))
    print()
    
    # Check files
    print("📄 FILES")
    print("─" * 60)
    results.append(check_files())
    print()
    
    # Final result
    print("═" * 60)
    if all(results):
        print("✅ EVERYTHING OK! Installation completed successfully!")
        print()
        print("🚀 You can start the monitor with:")
        print("   python tiktok_monitor.py")
    else:
        print("❌ Some components are missing. Follow instructions above.")
        print()
        print("📖 Run:")
        print("   pip install -r requirements.txt")
    print("═" * 60)

if __name__ == "__main__":
    main()