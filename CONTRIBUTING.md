# 🤝 Contributing to TikTok Auto Downloader

Thank you for your interest in contributing! All contributions are welcome.

## 🐛 Reporting Bugs

Use the [Issues](https://github.com/gabrielrahbar/TikTokAutoDownloader/issues) section and include:

- 🐍 Python version (`python --version`)
- 💻 Operating system
- 📋 Steps to reproduce the bug
- 📸 Screenshots if applicable
- 📝 Complete error log

## 💡 Suggesting Features

1. Check that the feature doesn't already exist in Issues
2. Open a new Issue with `enhancement` tag
3. Describe the use case and benefit

## 🔧 Pull Requests

1. Fork the repository
2. Create a branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test everything: `python check_installation.py`
5. Commit: `git commit -m "Clear description"`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 Coding Style

- Use **Python 3.7+** syntax
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Comments in English
- Docstrings for public functions

## ✅ Testing

Before submitting a PR, verify:
```bash
python check_installation.py
python tiktok_monitor.py --check-once --users test_user