"""
Modern UI Styles for TikTok Auto Downloader
Clean, professional design with rounded corners and smooth colors
Version: 2.3 - FORCED colors with !important to override system themes
"""

# Color palette
COLORS = {
    'primary':    '#3498db',      # Blue
    'success':  '#2ecc71',      # Green
    'danger':  '#e74c3c',       # Red
    'warning':   '#f39c12',      # Orange
    'info':  '#1abc9c',         # Teal
    'dark':  '#2c3e50',         # Dark blue
    'light': '#ecf0f1',        # Light gray
    'background': '#f5f6fa',   # Very light gray
    'card': '#ffffff',         # White
    'text': '#000000',         # BLACK
    'text_secondary': '#555555',  # Dark gray
    'border': '#dfe6e9',       # Light border
}

# Modern stylesheet with FORCED colors
MODERN_STYLE = f"""
/* === GLOBAL === */
QWidget {{
    font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    color: #000000;
}}

QMainWindow {{
    background-color:    {COLORS['background']};
}}

/* === GROUP BOXES (Cards) === */
QGroupBox {{
    background-color: {COLORS['card']} !important;
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 12px;
    padding: 20px;
    font-weight: 600;
    font-size: 14px;
    color: #000000 !important;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 5px 10px;
    background-color: {COLORS['card']} !important;
    border-radius: 6px;
    color: #000000 !important;
}}

/* === BUTTONS === */
QPushButton {{
    background-color: {COLORS['primary']};
    color: white ! important;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 14px;
}}

QPushButton:hover {{
    background-color: #2980b9;
}}

QPushButton:pressed {{
    background-color: #21618c;
}}

QPushButton:  disabled {{
    background-color:   {COLORS['border']};
    color: #999999 !important;
}}

/* Button variants */
QPushButton[class="btn-success"] {{
    background-color:  {COLORS['success']} !important;
    color:  white !important;
}}

QPushButton[class="btn-success"]:hover {{
    background-color: #27ae60 !important;
}}

QPushButton[class="btn-danger"] {{
    background-color:  {COLORS['danger']} ! important;
    color: white ! important;
}}

QPushButton[class="btn-danger"]: hover {{
    background-color:  #c0392b !important;
}}

QPushButton[class="btn-warning"] {{
    background-color: {COLORS['warning']} !important;
    color: white !important;
}}

QPushButton[class="btn-warning"]:hover {{
    background-color: #e67e22 !important;
}}

QPushButton[class="btn-secondary"] {{
    background-color:  {COLORS['light']} !important;
    color: #000000 !important;
    font-weight: 600;
}}

QPushButton[class="btn-secondary"]:hover {{
    background-color: #d5d8dc !important;
}}

/* === INPUTS - FORCED WHITE BACKGROUND === */
QLineEdit {{
    background-color: white ! important;
    border:   2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 15px;
    font-size:  15px;
    color: #000000 !important;
    font-weight:   600;
}}

QLineEdit:focus {{
    border:  2px solid {COLORS['primary']};
    background-color: #ffffff !important;
    color: #000000 !important;
}}

QLineEdit: disabled {{
    background-color: #f5f5f5 !important;
    color: #666666 !important;
}}

QLineEdit:: placeholder {{
    color:   #999999;
}}

QSpinBox {{
    background-color: white !important;
    border:  2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 15px;
    padding-right: 30px;
    font-size: 15px;
    color: #000000 !important;
    font-weight:  600;
}}

QSpinBox:focus {{
    border: 2px solid {COLORS['primary']};
    background-color: #ffffff !important;
}}

QSpinBox:: up-button, QSpinBox::down-button {{
    background-color: {COLORS['light']} !important;
    border: none;
    width: 20px;
}}

QSpinBox::up-button:  hover, QSpinBox::down-button: hover {{
    background-color:  {COLORS['primary']} !important;
}}

QSpinBox::up-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 5px solid #000000;
}}

QSpinBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #000000;
}}

QComboBox {{
    background-color: white !important;
    border:  2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 15px;
    font-size: 15px;
    color: #000000 !important;
    font-weight:  600;
}}

QComboBox:focus {{
    border: 2px solid {COLORS['primary']};
}}

QComboBox::  drop-down {{
    border: none;
    padding-right: 10px;
    background-color: {COLORS['light']} !important;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #000000;
    margin-right: 5px;
}}

QComboBox QAbstractItemView {{
    background-color: white ! important;
    border:  2px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['primary']};
    selection-color: white !important;
    color: #000000 !important;
    font-size: 14px;
    font-weight:  500;
    padding: 5px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px;
    color: #000000 !important;
    background-color: white !important;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: #e8f4f8 !important;
    color: #000000 !important;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS['primary']} !important;
    color: white !important;
}}

/* === LABELS === */
QLabel {{
    color: #000000 !important;
    font-size: 14px;
}}

/* === TABLES - FORCED WHITE BACKGROUND === */
QTableWidget {{
    background-color: white !important;
    alternate-background-color: #f9f9f9 !important;
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['primary']};
    color:   #000000 !important;
    font-size: 14px;
}}

QTableWidget::item {{
    padding: 8px;
    color: #000000 !important;
    background-color: white !important;
    font-weight: 500;
}}

QTableWidget::item:alternate {{
    background-color: #f9f9f9 ! important;
}}

QTableWidget::item:  selected {{
    background-color:   {COLORS['primary']} !important;
    color: white !important;
}}

QTableWidget::item: hover {{
    background-color: #e8f4f8 ! important;
}}

QHeaderView::  section {{
    background-color:   {COLORS['light']} !important;
    color: #000000 !important;
    padding: 10px;
    border:   none;
    border-bottom: 2px solid {COLORS['border']};
    font-weight: 700;
    font-size: 13px;
}}

/* === TEXT EDIT === */
QTextEdit {{
    background-color:   white !important;
    border: 1px solid {COLORS['border']};
    border-radius:  10px;
    padding: 15px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 13px;
    color: #000000 !important;
}}

QTextEdit:focus {{
    border: 2px solid {COLORS['primary']};
}}

/* === CHECKBOXES === */
QCheckBox {{
    spacing: 8px;
    color: #000000 !important;
    font-size: 14px;
    font-weight: 500;
}}

QCheckBox::  indicator {{
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background-color:   white !important;
}}

QCheckBox::indicator:hover {{
    border:   2px solid {COLORS['primary']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['success']} !important;
    border-color: {COLORS['success']};
}}

/* === TABS === */
QTabWidget::  pane {{
    border: none;
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: {COLORS['card']} !important;
    color: #555555 !important;
    padding: 12px 24px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 600;
    font-size: 14px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['primary']} !important;
    color: white !important;
}}

QTabBar:: tab:hover:  !  selected {{
    background-color:   {COLORS['light']} !important;
    color: #000000 !important;
}}

/* === SCROLLBAR === */
QScrollBar:  vertical {{
    background-color: {COLORS['background']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:  vertical {{
    background-color:   #999999;
    border-radius:   6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #666666;
}}

QScrollBar::add-line:  vertical, QScrollBar::sub-line: vertical {{
    height: 0px;
}}

QScrollBar:  horizontal {{
    background-color:   {COLORS['background']};
    height: 12px;
    border-radius:   6px;
}}

QScrollBar::handle: horizontal {{
    background-color:  #999999;
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:  hover {{
    background-color:   #666666;
}}

QScrollBar::add-line: horizontal, QScrollBar::sub-line:horizontal {{
    width:  0px;
}}

/* === STATUS BAR === */
QStatusBar {{
    background-color: {COLORS['card']} !important;
    color: #000000 !important;
    border-top: 1px solid {COLORS['border']};
    padding:   5px;
    font-weight: 500;
}}

/* === TOOLTIP === */
QToolTip {{
    background-color: #2c3e50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 5px;
    font-size:   12px;
}}
"""

# Dark theme (optional)
DARK_STYLE = """
/* Dark theme - Modern dark mode */
QWidget {
    background-color: #1e1e1e ! important;
    color: #e0e0e0 !important;
}

QMainWindow {
    background-color: #121212 !important;
}

QGroupBox {
    background-color: #2d2d2d !important;
    border: 1px solid #3d3d3d;
    color: #e0e0e0 !important;
}

QPushButton {
    background-color: #3498db !important;
    color:  white !important;
}

QLineEdit, QSpinBox, QComboBox {
    background-color:  #2d2d2d !important;
    border: 2px solid #3d3d3d;
    color: #ffffff !important;
    font-weight: 600;
}

QTableWidget {
    background-color:   #2d2d2d !important;
    border: 1px solid #3d3d3d;
    color: #e0e0e0 !important;
    gridline-color: #3d3d3d;
}

QTableWidget::item {
    color: #e0e0e0 !important;
    background-color: #2d2d2d !important;
}

QHeaderView:: section {
    background-color:  #1e1e1e !important;
    color: #e0e0e0 !important;
}

QTextEdit {
    background-color: #2d2d2d !important;
    border: 1px solid #3d3d3d;
    color: #e0e0e0 !important;
}

QTabBar::tab {
    background-color: #2d2d2d !important;
    color: #909090 !important;
}

QTabBar::tab:selected {
    background-color: #3498db !important;
    color:  white !important;
}

QLabel {
    color: #e0e0e0 !important;
}

QCheckBox {
    color: #e0e0e0 !important;
}
"""