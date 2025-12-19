"""
Custom metric card widget for dashboard
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MetricCard(QFrame):
    """
    Beautiful metric card with icon, value, and label
    """
    def __init__(self, icon, value, label, color="#3498db", parent=None):
        super().__init__(parent)
        self.color = color
        self.init_ui(icon, value, label)
        
    def init_ui(self, icon, value, label):
        """Initialize card UI"""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
            }}
            MetricCard: hover {{
                border:  1px solid {self.color};
                background-color: #fafafa;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 32))
        icon_label.setAlignment(Qt.AlignLeft)
        
        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont("Segoe UI", 36, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.color};")
        self.value_label.setAlignment(Qt.AlignLeft)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", 12))
        label_widget.setStyleSheet("color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px;")
        label_widget.setAlignment(Qt. AlignLeft)
        
        layout.addWidget(icon_label)
        layout.addWidget(self.value_label)
        layout.addWidget(label_widget)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setMinimumHeight(150)
    
    def update_value(self, value):
        """Update the metric value"""
        self.value_label.setText(str(value))