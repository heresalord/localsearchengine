"""
Modern stylesheet and design system for the application.
"""

# Color Palette - Modern, Professional
COLORS = {
    # Primary
    'primary': '#667eea',  # Purple-blue
    'primary_hover': '#7c3aed',
    'primary_light': '#a5b4fc',
    'primary_dark': '#4c1d95',
    
    # Accent
    'accent': '#f59e0b',  # Amber
    'accent_hover': '#d97706',
    
    # Neutral
    'bg_main': '#f8fafc',  # Very light gray
    'bg_secondary': '#ffffff',
    'bg_hover': '#f1f5f9',
    'bg_active': '#e2e8f0',
    
    # Sidebar
    'sidebar_bg': '#1e293b',  # Dark slate
    'sidebar_item': '#334155',
    'sidebar_hover': '#475569',
    'sidebar_active': '#667eea',
    'sidebar_text': '#f1f5f9',
    
    # Text
    'text_primary': '#0f172a',
    'text_secondary': '#64748b',
    'text_muted': '#94a3b8',
    
    # Borders
    'border': '#e2e8f0',
    'border_focus': '#667eea',
    
    # Status
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'info': '#3b82f6',
    
    # File type colors
    'pdf': '#ef4444',
    'docx': '#3b82f6',
    'txt': '#64748b',
    'md': '#8b5cf6',
    'image': '#ec4899',
}

# Modern Stylesheet
MODERN_STYLESHEET = f"""
/* ==================== GLOBAL STYLES ==================== */
QMainWindow {{
    background-color: {COLORS['bg_main']};
}}

QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    color: {COLORS['text_primary']};
}}

/* ==================== SIDEBAR ==================== */
#sidebar {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['sidebar_bg']},
        stop:1 #0f172a
    );
    border-right: 1px solid #334155;
}}

#appTitle {{
    color: white;
    padding: 15px 10px;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.5px;
}}

#navList {{
    background-color: transparent;
    border: none;
    outline: none;
    font-size: 15px;
    color: {COLORS['sidebar_text']};
    padding: 10px;
}}

#navList::item {{
    padding: 14px 16px;
    border-radius: 10px;
    margin: 4px 0;
    font-weight: 500;
}}

#navList::item:hover {{
    background-color: {COLORS['sidebar_hover']};
}}

#navList::item:selected {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['sidebar_active']},
        stop:1 #7c3aed
    );
    color: white;
    font-weight: 600;
}}

#navList::item:disabled {{
    color: #475569;
    background-color: transparent;
}}

#settingsButton, #aboutButton {{
    background-color: {COLORS['sidebar_item']};
    color: {COLORS['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    text-align: left;
}}

#settingsButton:hover, #aboutButton:hover {{
    background-color: {COLORS['sidebar_hover']};
}}

#settingsButton:pressed, #aboutButton:pressed {{
    background-color: {COLORS['sidebar_bg']};
}}

/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: white;
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    padding: 8px 16px;
    font-size: 13px;
}}

/* ==================== SEARCH TAB ==================== */
#searchContainer {{
    background-color: {COLORS['bg_secondary']};
    border-radius: 16px;
    padding: 24px;
}}

#searchInput {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 12px;
    padding: 14px 20px 14px 50px;
    font-size: 15px;
    color: {COLORS['text_primary']};
}}

#searchInput:focus {{
    border-color: {COLORS['border_focus']};
    background-color: white;
}}

#searchButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']},
        stop:1 {COLORS['primary_hover']}
    );
    color: white;
    border: none;
    border-radius: 12px;
    padding: 14px 28px;
    font-size: 15px;
    font-weight: 600;
}}

#searchButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary_hover']},
        stop:1 #6d28d9
    );
}}

#searchButton:pressed {{
    background-color: {COLORS['primary_dark']};
}}

#searchButton:disabled {{
    background-color: {COLORS['bg_active']};
    color: {COLORS['text_muted']};
}}

/* ==================== COMBO BOXES & INPUTS ==================== */
QComboBox {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {COLORS['primary_light']};
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 4px;
}}

QComboBox QAbstractItemView {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['primary_light']};
    padding: 4px;
}}

/* ==================== CHECKBOXES ==================== */
QCheckBox {{
    spacing: 8px;
    color: {COLORS['text_primary']};
    font-size: 14px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    background-color: white;
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary_light']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNC42NjY2N0w2IDEyTDIuNjY2NjcgOC42NjY2NyIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}}

/* ==================== GROUP BOXES ==================== */
QGroupBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 12px;
    padding: 20px;
    font-weight: 600;
    font-size: 15px;
    color: {COLORS['text_primary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    top: -8px;
    padding: 0 8px;
    background-color: {COLORS['bg_secondary']};
}}

/* ==================== LISTS ==================== */
QListWidget {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 8px;
    outline: none;
}}

QListWidget::item {{
    border-radius: 8px;
    padding: 4px;
    margin: 2px;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['primary_light']};
    color: {COLORS['text_primary']};
}}

/* ==================== TEXT EDITS ==================== */
QTextEdit, QPlainTextEdit {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    line-height: 1.6;
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['border_focus']};
}}

/* ==================== LINE EDITS ==================== */
QLineEdit {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border-color: {COLORS['border_focus']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_muted']};
}}

/* ==================== SCROLL AREAS ==================== */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_hover']};
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['text_muted']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_hover']};
    height: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['text_muted']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_secondary']};
}}

/* ==================== LABELS ==================== */
QLabel {{
    color: {COLORS['text_primary']};
}}

#sectionLabel {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS['text_primary']};
    padding: 8px 0;
}}

#infoLabel {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
    line-height: 1.5;
}}

/* ==================== BUTTONS (General) ==================== */
QPushButton {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['text_primary']};
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['primary_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_active']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}

/* ==================== DIALOG BUTTONS ==================== */
QDialogButtonBox QPushButton {{
    min-width: 80px;
    padding: 10px 24px;
}}

/* ==================== TABS ==================== */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_secondary']};
    padding: 8px;
}}

QTabBar::tab {{
    background-color: {COLORS['bg_hover']};
    border: none;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['primary']};
}}

QTabBar::tab:hover {{
    background-color: {COLORS['bg_active']};
}}

/* ==================== SPIN BOXES ==================== */
QSpinBox {{
    background-color: white;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
}}

QSpinBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: transparent;
    border: none;
    width: 20px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {COLORS['bg_hover']};
}}

/* ==================== MESSAGE BOXES ==================== */
QMessageBox {{
    background-color: {COLORS['bg_secondary']};
}}

QMessageBox QPushButton {{
    min-width: 80px;
}}
"""

def get_file_type_color(file_type: str) -> str:
    """Get color for file type badge."""
    return COLORS.get(file_type.lower(), COLORS['text_muted'])

def get_score_color(score: float) -> str:
    """Get color based on relevance score."""
    if score >= 0.8:
        return COLORS['success']
    elif score >= 0.6:
        return COLORS['info']
    elif score >= 0.4:
        return COLORS['warning']
    else:
        return COLORS['error']
