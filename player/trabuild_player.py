"""
================================================================================
  TRABUILD SECURE CLOUD PLAYER - CLIENT APPLICATION
  Features:
  - HWID Machine-Locking (Motherboard & GUID Fingerprint)
  - Anti-Screen Capture (Win32 SetWindowDisplayAffinity - WDA_EXCLUDEFROMCAPTURE)
  - Dynamic Floating Watermark (Student Name + Phone + License Key)
  - Session Persistence (Auto-login with saved license)
  - Fluid Adaptive Layout with Multi-line Lesson Cards (No horizontal scrollbars)
  - Process Detection & Antitamper Security Engine
  - Real-time Cloud Synchronization with Backend Server
================================================================================
"""

import sys
import os
import json
import time
import uuid
import random
import ctypes
import hashlib
import requests
import threading

from PySide6.QtCore import Qt, QUrl, QTimer, QTime, Signal, QObject, QEvent, QPoint
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSlider, QFrame, QScrollArea,
    QStackedWidget, QMessageBox, QStyle, QSplitter, QSizePolicy, QComboBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

# Production Cloud Server API Endpoint (Render.com)
API_DEFAULT = "https://trabuild-server.onrender.com"

def get_asset_path(filename: str) -> str:
    """Safely retrieves asset path in both local dev and PyInstaller bundle modes."""
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        p1 = os.path.join(base_dir, "assets", filename)
        if os.path.exists(p1):
            return p1
        p2 = os.path.join(os.path.dirname(sys.executable), "assets", filename)
        if os.path.exists(p2):
            return p2
    dev_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", filename))
    if os.path.exists(dev_path):
        return dev_path
    return ""

def get_session_file_path() -> str:
    """Returns local path for stored session."""
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(appdata, "TRABUILD")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "session.json")

# ----------------------------------------------------
# Thread-safe API Communication Workers
# ----------------------------------------------------
class ActivationWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, api_url, key, hwid):
        super().__init__()
        self.api_url = api_url
        self.key = key
        self.hwid = hwid

    def run(self):
        try:
            res = requests.post(f"{self.api_url}/api/auth/activate", json={
                "license_key": self.key,
                "hwid": self.hwid
            }, timeout=8)
            data = res.json()
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))

class HeartbeatWorker(QObject):
    ban_detected = Signal(str)
    courses_synced = Signal(list)

    def __init__(self, api_url, key, hwid):
        super().__init__()
        self.api_url = api_url
        self.key = key
        self.hwid = hwid

    def run(self):
        try:
            res = requests.post(f"{self.api_url}/api/auth/heartbeat", json={
                "license_key": self.key,
                "hwid": self.hwid
            }, timeout=4)
            data = res.json()
            if not data.get("valid"):
                msg = data.get("message", "تم إيقاف الجلسة من قبل الإدارة.")
                self.ban_detected.emit(msg)
                return

            # Fetch fresh courses info to keep title and lessons in sync live
            c_res = requests.get(f"{self.api_url}/api/courses", timeout=4)
            c_data = c_res.json()
            if c_data.get("success"):
                self.courses_synced.emit(c_data.get("courses", []))
        except Exception:
            pass


# ----------------------------------------------------
# 1. Hardware Fingerprinting (HWID Generator)
# ----------------------------------------------------
def get_hardware_fingerprint() -> str:
    """Generates a stable, unique Hardware ID (HWID) based on machine GUID and CPU."""
    hw_components = []
    
    # 1. Windows Machine GUID (Permanent & Unique per Windows Installation)
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            hw_components.append(str(guid).strip().lower())
        except Exception:
            pass
            
    # 2. Processor & Computer Identifiers (Permanent hardware identifiers)
    proc_id = os.environ.get("PROCESSOR_IDENTIFIER", "")
    comp_name = os.environ.get("COMPUTERNAME", "")
    user_domain = os.environ.get("USERDOMAIN", "")
    hw_components.append(str(proc_id).strip())
    hw_components.append(str(comp_name).strip())
    hw_components.append(str(user_domain).strip())
    
    combined = "_".join([c for c in hw_components if c]).encode("utf-8")
    hash_digest = hashlib.sha256(combined).hexdigest().upper()
    return f"HWID-WIN-{hash_digest[:12]}"


# ----------------------------------------------------
# Custom Clickable Lesson Card (Wrap-Friendly)
# ----------------------------------------------------
class LessonCardWidget(QFrame):
    clicked = Signal(int)

    def __init__(self, index, lesson, parent=None):
        super().__init__(parent)
        self.index = index
        self.lesson = lesson
        self.is_selected = False
        
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        
        # Header Row: Lesson Number Pill + Title
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)
        
        self.badge_lbl = QLabel(f"#{index + 1:02d}")
        self.badge_lbl.setAlignment(Qt.AlignCenter)
        self.badge_lbl.setFixedSize(36, 24)
        header_row.addWidget(self.badge_lbl)
        
        # Title Label with WordWrap
        self.title_lbl = QLabel(lesson.get('title', ''))
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_row.addWidget(self.title_lbl, 1)
        
        layout.addLayout(header_row)
        
        # Footer Row (Duration + Action Status)
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        
        self.dur_lbl = QLabel(f"⏱ {lesson.get('duration', 'ساعة ونصف')}")
        footer.addWidget(self.dur_lbl)
        
        footer.addStretch()
        
        self.status_lbl = QLabel("عرض ▶")
        footer.addWidget(self.status_lbl)
        
        layout.addLayout(footer)
        self.update_style()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #eff6ff;
                    border: 2px solid #0284c7;
                    border-radius: 12px;
                }
            """)
            self.badge_lbl.setStyleSheet("""
                background-color: #0284c7;
                color: #ffffff;
                font-size: 11px;
                font-weight: 800;
                border-radius: 6px;
            """)
            self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #0369a1;")
            self.dur_lbl.setStyleSheet("font-size: 11px; color: #0284c7; font-weight: 600;")
            self.status_lbl.setText("● قيد التشغيل")
            self.status_lbl.setStyleSheet("font-size: 10px; color: #ffffff; font-weight: bold; background: #0284c7; padding: 3px 8px; border-radius: 6px;")
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                }
                QFrame:hover {
                    background-color: #f8fafc;
                    border-color: #38bdf8;
                }
            """)
            self.badge_lbl.setStyleSheet("""
                background-color: #f1f5f9;
                color: #64748b;
                font-size: 11px;
                font-weight: 800;
                border-radius: 6px;
            """)
            self.title_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b;")
            self.dur_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
            self.status_lbl.setText("عرض ▶")
            self.status_lbl.setStyleSheet("font-size: 10px; color: #0284c7; font-weight: bold; background: #f0f9ff; border: 1px solid #bae6fd; padding: 3px 8px; border-radius: 6px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)


# ----------------------------------------------------
# Hardware-Safe Floating Watermark Overlay Window
# ----------------------------------------------------
class WatermarkOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowTransparentForInput |
            Qt.WindowDoesNotAcceptFocus |
            Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        
        self.label = QLabel(self)
        self.label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.70);
                font-size: 13px;
                font-weight: 800;
                font-family: 'Cairo', 'Outfit', 'Segoe UI', sans-serif;
                padding: 6px 14px;
                background-color: rgba(15, 23, 42, 0.72);
                border: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 8px;
            }
        """)
        self.label.setText("TRABUILD Student Security")
        self.label.adjustSize()

    def set_watermark_text(self, text: str):
        self.label.setText(text)
        self.label.adjustSize()

    def move_to_random_pos(self):
        w = self.width()
        h = self.height()
        self.label.adjustSize()
        lw = self.label.width()
        lh = self.label.height()
        
        if w > lw + 30 and h > lh + 30:
            rx = random.randint(15, w - lw - 15)
            ry = random.randint(15, h - lh - 15)
            self.label.move(rx, ry)


# ----------------------------------------------------
# 2. Main TRABUILD Desktop Player Window
# ----------------------------------------------------
class TrabuildPlayerWindow(QMainWindow):
    def __init__(self, api_url=API_DEFAULT):
        super().__init__()
        self.api_url = api_url
        self.hwid = get_hardware_fingerprint()
        
        # State
        self.license_key = ""
        self.student_name = "طالب TRABUILD"
        self.student_phone = ""
        self.courses = []
        self.current_lessons = []
        self.current_lesson_index = -1
        self.is_authenticated = False
        self.lesson_cards = []
        
        # Hardware-Safe Dedicated Watermark Overlay
        self.watermark_overlay = WatermarkOverlay(self)
        
        self.setWindowTitle("TRABUILD Player - مشغل الكورسات المحمي")
        self.resize(1140, 700)
        self.setMinimumSize(700, 460)
        
        # Set Application Icon
        icon_path = get_asset_path("app_icon.png")
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Apply Global Stylesheet
        self.apply_theme()
        
        # Central widget stacked (Login / Activation View vs Player Workspace View)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.init_activation_view()
        self.init_workspace_view()
        
        # Timers & Security Engine
        self.init_security_engine()
        
        # Install Global Event Filter for Hotkeys (Space for Play/Pause, Arrows for 5s Seek)
        QApplication.instance().installEventFilter(self)
        
        # Auto-login check
        QTimer.singleShot(200, self.check_saved_session)

    def apply_theme(self):
        """Applies TRABUILD brand styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f1f5f9;
                font-family: 'Cairo', 'Outfit', 'Segoe UI', sans-serif;
            }
            QWidget {
                color: #0f172a;
                font-family: 'Cairo', 'Outfit', 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border-color: #007ea7;
                background-color: #ffffff;
            }
            QPushButton {
                background-color: #007ea7;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #006688;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QSplitter::handle {
                background-color: #e2e8f0;
                width: 3px;
            }
        """)

    # ----------------------------------------------------
    # VIEW 1: Activation & Login View
    # ----------------------------------------------------
    def init_activation_view(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet("background-color: #f1f5f9; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        view = QWidget()
        view.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(view)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(16, 16, 16, 16)
        
        card = QFrame()
        card.setObjectName("activationCard")
        card.setMinimumWidth(320)
        card.setMaximumWidth(460)
        card.setStyleSheet("""
            QFrame#activationCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 18px;
                padding: 24px 28px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignCenter)
        
        # Logo Image
        logo_label = QLabel()
        logo_path = get_asset_path("logo.png")
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaledToHeight(48, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("TRABUILD")
            logo_label.setStyleSheet("font-size: 24px; font-weight: 900; color: #007ea7;")
        logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(logo_label)
        
        # Title
        title = QLabel("تفعيل رخصة المحاضرات")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 2px;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)
        
        sub = QLabel("أدخل مفتاح الترخيص المسلّم لك من إدارة الكورس لربطه بحاسبتك")
        sub.setStyleSheet("font-size: 12px; color: #64748b; margin-bottom: 4px;")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        card_layout.addWidget(sub)
        
        # License input
        lbl_key = QLabel("مفتاح الترخيص (License Key):")
        lbl_key.setStyleSheet("font-size: 12px; font-weight: bold; color: #475569;")
        card_layout.addWidget(lbl_key)
        
        self.input_license = QLineEdit()
        self.input_license.setPlaceholderText("TRABUILD-2026-XXXX-XXXX")
        self.input_license.setAlignment(Qt.AlignCenter)
        self.input_license.setFixedHeight(48)
        self.input_license.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #94a3b8;
                border-radius: 10px;
                padding: 8px 12px;
                font-family: monospace;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1.5px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 2px solid #007ea7;
                background-color: #f0f9ff;
            }
        """)
        card_layout.addWidget(self.input_license)
        
        # HWID Box
        hwid_box = QFrame()
        hwid_box.setFixedHeight(40)
        hwid_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 4px 10px;")
        hwid_layout = QHBoxLayout(hwid_box)
        hwid_layout.setContentsMargins(8, 2, 8, 2)
        
        hwid_label = QLabel("بصمة حاسبتك:")
        hwid_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: bold;")
        hwid_val = QLabel(self.hwid)
        hwid_val.setStyleSheet("font-family: monospace; font-size: 12px; color: #007ea7; font-weight: bold;")
        
        hwid_layout.addWidget(hwid_label)
        hwid_layout.addStretch()
        hwid_layout.addWidget(hwid_val)
        card_layout.addWidget(hwid_box)
        
        # Activate Button
        self.btn_activate = QPushButton("تأكيد الترخيص والدخول 🔓")
        self.btn_activate.setFixedHeight(44)
        self.btn_activate.setStyleSheet("background-color: #007ea7; font-size: 14px; border-radius: 8px;")
        self.btn_activate.clicked.connect(self.perform_activation)
        card_layout.addWidget(self.btn_activate)
        
        layout.addWidget(card)
        scroll.setWidget(view)
        self.stacked_widget.addWidget(scroll)

    # ----------------------------------------------------
    # VIEW 2: Workspace & Video Player View
    # ----------------------------------------------------
    def init_workspace_view(self):
        view = QWidget()
        main_layout = QVBoxLayout(view)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Top Navbar Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(10)
        
        # Brand Logo
        brand_lbl = QLabel()
        logo_path = get_asset_path("logo.png")
        if logo_path and os.path.exists(logo_path):
            brand_lbl.setPixmap(QPixmap(logo_path).scaledToHeight(38, Qt.SmoothTransformation))
        else:
            brand_lbl.setText("TRABUILD")
            brand_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #007ea7;")
        header_layout.addWidget(brand_lbl)
        
        header_layout.addStretch()
        
        # Shield & Student Badges
        shield_badge = QLabel("🛡️ حماية الشاشة نشطة")
        shield_badge.setStyleSheet("background-color: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; border-radius: 14px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(shield_badge)
        
        self.student_badge = QLabel("الطالب: -")
        self.student_badge.setStyleSheet("background-color: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; border-radius: 14px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(self.student_badge)
        
        main_layout.addWidget(header)
        
        # 2. Main Body Splitter (Video Stage + Sidebar Playlist)
        self.body_splitter = QSplitter(Qt.Horizontal)
        self.body_splitter.setStyleSheet("background-color: #0f172a;")
        
        # --- Stage & Video Player (Right side) ---
        stage = QWidget()
        stage.setStyleSheet("background-color: #0f172a;")
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.setSpacing(0)
        
        # Video Container (Hosts Video Widget + Dynamic Watermark)
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background-color: #000000;")
        video_inner_layout = QVBoxLayout(self.video_container)
        video_inner_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget(self.video_container)
        video_inner_layout.addWidget(self.video_widget)
        
        stage_layout.addWidget(self.video_container, stretch=1)
        
        # Stage Footer Controls (Classy Dark Studio Console)
        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_frame.setFixedHeight(94)
        controls_frame.setStyleSheet("""
            QFrame#controlsFrame {
                background-color: #0b1120;
                border-top: 1px solid #1e293b;
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(14, 6, 14, 6)
        controls_layout.setSpacing(4)
        
        # Timeline slider
        slider_layout = QHBoxLayout()
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 11px; font-weight: bold;")
        
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setFocusPolicy(Qt.NoFocus)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: #1e293b; border-radius: 3px; }
            QSlider::handle:horizontal { background: #38bdf8; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px; border: 2px solid #ffffff; }
            QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007ea7, stop:1 #38bdf8); border-radius: 3px; }
        """)
        self.position_slider.sliderMoved.connect(self.set_position)
        
        slider_layout.addWidget(self.position_slider)
        slider_layout.addWidget(self.time_label)
        controls_layout.addLayout(slider_layout)
        
        # Control Buttons Bar (Classy Glass Badges)
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)
        
        # Play/Pause (Glowing Cyan Pill)
        self.btn_play_pause = QPushButton()
        self.btn_play_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play_pause.setToolTip("تشغيل / إيقاف مؤقت (المسافة Space)")
        self.btn_play_pause.setFocusPolicy(Qt.NoFocus)
        self.btn_play_pause.setStyleSheet("""
            QPushButton {
                background-color: #007ea7;
                color: #ffffff;
                border-radius: 16px;
                padding: 6px 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0284c7;
            }
        """)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        btn_bar.addWidget(self.btn_play_pause)
        
        # Seek -5s (Dark Glass Pill)
        btn_back_5 = QPushButton("⏪ 5s-")
        btn_back_5.setToolTip("تأخير 5 ثوانٍ (السهم الأيسر ←)")
        btn_back_5.setFocusPolicy(Qt.NoFocus)
        btn_back_5.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        btn_back_5.clicked.connect(lambda: self.seek_relative(-5000))
        btn_bar.addWidget(btn_back_5)
        
        # Seek +5s (Dark Glass Pill)
        btn_fwd_5 = QPushButton("+5s ⏩")
        btn_fwd_5.setToolTip("تقديم 5 ثوانٍ (السهم الأيمن →)")
        btn_fwd_5.setFocusPolicy(Qt.NoFocus)
        btn_fwd_5.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        btn_fwd_5.clicked.connect(lambda: self.seek_relative(5000))
        btn_bar.addWidget(btn_fwd_5)
        
        # Lecture Title
        self.current_title_lbl = QLabel("اختر محاضرة من القائمة لبدء المشاهدة")
        self.current_title_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc; padding: 0 6px;")
        self.current_title_lbl.setWordWrap(True)
        self.current_title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_bar.addWidget(self.current_title_lbl, stretch=1)
        
        # Playback Speed (0.75x -> 2.0x)
        self.speed_combo = QComboBox()
        self.speed_combo.setFocusPolicy(Qt.NoFocus)
        self.speed_combo.addItems(["⚡ 1.0x", "⚡ 1.25x", "⚡ 1.5x", "⚡ 1.75x", "⚡ 2.0x", "⚡ 0.75x"])
        self.speed_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #38bdf8;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #ffffff;
                selection-background-color: #007ea7;
            }
        """)
        self.speed_combo.currentIndexChanged.connect(self.change_speed)
        btn_bar.addWidget(self.speed_combo)
        
        # Quality Selector
        self.quality_combo = QComboBox()
        self.quality_combo.setFocusPolicy(Qt.NoFocus)
        self.quality_combo.addItems([
            "⚡ 720p HD (سريعة - موصى بها)",
            "💎 1080p FHD (أعلى دقة)",
            "🌐 تلقائي (Adaptive Auto)"
        ])
        self.quality_combo.setCurrentIndex(0) # Default to 720p HD for instant playback!
        self.quality_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #a5f3fc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #007ea7;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #ffffff;
                selection-background-color: #007ea7;
            }
        """)
        self.quality_combo.currentIndexChanged.connect(self.change_quality)
        btn_bar.addWidget(self.quality_combo)
        
        # Fullscreen Toggle
        btn_fullscreen = QPushButton("⛶")
        btn_fullscreen.setToolTip("ملء الشاشة (F)")
        btn_fullscreen.setFocusPolicy(Qt.NoFocus)
        btn_fullscreen.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 13px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        btn_bar.addWidget(btn_fullscreen)
        
        # Logout
        btn_logout = QPushButton("خروج 🔒")
        btn_logout.setFocusPolicy(Qt.NoFocus)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
                color: #ffffff;
            }
        """)
        btn_logout.clicked.connect(self.logout)
        btn_bar.addWidget(btn_logout)
        
        controls_layout.addLayout(btn_bar)
        stage_layout.addWidget(controls_frame)
        
        self.body_splitter.addWidget(stage)
        
        # --- Sidebar Playlist (Left side in RTL) ---
        sidebar = QFrame()
        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(380)
        sidebar.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        sidebar_header = QFrame()
        sidebar_header.setStyleSheet("background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 12px 14px;")
        sb_h_layout = QVBoxLayout(sidebar_header)
        sb_h_layout.setContentsMargins(0, 0, 0, 0)
        
        sb_title = QLabel("قائمة المحاضرات")
        sb_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")
        sb_h_layout.addWidget(sb_title)
        
        self.course_sub_lbl = QLabel("كورس TRABUILD المتقدم")
        self.course_sub_lbl.setStyleSheet("font-size: 12px; color: #007ea7; font-weight: bold; margin-top: 2px;")
        self.course_sub_lbl.setWordWrap(True)
        sb_h_layout.addWidget(self.course_sub_lbl)
        
        sidebar_layout.addWidget(sidebar_header)
        
        # Lessons Scroll Area (No horizontal scrollbar!)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.lessons_container = QWidget()
        self.lessons_container.setStyleSheet("background-color: #ffffff;")
        self.lessons_layout = QVBoxLayout(self.lessons_container)
        self.lessons_layout.setContentsMargins(8, 8, 8, 8)
        self.lessons_layout.setSpacing(8)
        self.lessons_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.lessons_container)
        
        sidebar_layout.addWidget(self.scroll_area)
        
        self.body_splitter.addWidget(sidebar)
        
        # Set Splitter Proportions (Stage 75%, Sidebar 25%)
        self.body_splitter.setStretchFactor(0, 7)
        self.body_splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(self.body_splitter)
        
        # Media Player Init
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        
        self.stacked_widget.addWidget(view)

    # ----------------------------------------------------
    # 3. Security Engine & Process Scanner
    # ----------------------------------------------------
    def init_security_engine(self):
        # 1. Apply Win32 Anti-Capture (SetWindowDisplayAffinity)
        QTimer.singleShot(250, self.apply_anti_screen_capture)
        
        # 2. Watermark Mover Timer (every 3.5 seconds)
        self.watermark_timer = QTimer(self)
        self.watermark_timer.setInterval(3500)
        self.watermark_timer.timeout.connect(self.reposition_watermark)
        
        # 3. Heartbeat & Live Sync Timer (every 3.5 seconds)
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.setInterval(3500)
        self.heartbeat_timer.timeout.connect(self.check_heartbeat_status)
        
        # 4. Process Scanner for recording tools (every 2 seconds)
        self.scanner_timer = QTimer(self)
        self.scanner_timer.setInterval(2000)
        self.scanner_timer.timeout.connect(self.scan_forbidden_processes)
        self.scanner_timer.start()

    def apply_anti_screen_capture(self):
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            WDA_EXCLUDEFROMCAPTURE = 0x11
            WDA_MONITOR = 1
            
            res = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if not res:
                res = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
            if res:
                print("[SECURITY] Win32 Anti-Screen Capture Activated Successfully.")
        except Exception as e:
            print(f"[SECURITY] Display affinity error: {e}")

    def scan_forbidden_processes(self):
        """Scans active processes for recording/streaming software."""
        forbidden = [
            "obs64.exe", "obs.exe", "camtasiastudio.exe", "camtasia.exe",
            "sharex.exe", "bandicam.exe", "snagit.exe", "anydesk.exe",
            "teamviewer.exe", "discord.exe", "skype.exe"
        ]
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                pname = proc.info.get('name')
                if pname and pname.lower() in forbidden:
                    self.trigger_security_violation(f"تم اكتشاف برنامج تسجيل أو مشاركة شاشة نشط ({pname}).")
                    break
        except Exception:
            pass

    def trigger_security_violation(self, message):
        self.media_player.stop()
        QMessageBox.critical(self, "تحذير أمني 🚨", f"{message}\nيرجى إغلاق البرنامج فوراً لمتابعة المحاضرات.")
        self.logout()

    def sync_overlay_geometry(self):
        if not self.is_authenticated or self.stacked_widget.currentIndex() != 1 or not self.isVisible() or self.isMinimized():
            self.watermark_overlay.hide()
            return
            
        if not self.video_widget.isVisible():
            self.watermark_overlay.hide()
            return
            
        # Map video_widget coordinates strictly to screen
        global_pos = self.video_widget.mapToGlobal(QPoint(0, 0))
        w = self.video_widget.width()
        h = self.video_widget.height()
        
        if w > 60 and h > 60:
            self.watermark_overlay.setGeometry(global_pos.x(), global_pos.y(), w, h)
            self.watermark_overlay.show()
            self.watermark_overlay.raise_()
        else:
            self.watermark_overlay.hide()

    def reposition_watermark(self):
        self.sync_overlay_geometry()
        if self.watermark_overlay.isVisible():
            self.watermark_overlay.move_to_random_pos()

    # ----------------------------------------------------
    # 4. Session Persistence & Cloud Synchronization
    # ----------------------------------------------------
    def check_saved_session(self):
        """Checks for saved session and auto-activates if valid."""
        sess_file = get_session_file_path()
        if os.path.exists(sess_file):
            try:
                with open(sess_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_key = data.get("license_key", "").strip()
                    if saved_key:
                        self.input_license.setText(saved_key)
                        self.perform_activation(silent=True)
            except Exception:
                pass

    def save_session(self, key):
        """Saves active license key locally."""
        try:
            sess_file = get_session_file_path()
            with open(sess_file, "w", encoding="utf-8") as f:
                json.dump({"license_key": key}, f)
        except Exception:
            pass

    def clear_session(self):
        """Removes saved license session file."""
        try:
            sess_file = get_session_file_path()
            if os.path.exists(sess_file):
                os.remove(sess_file)
        except Exception:
            pass

    def perform_activation(self, silent=False):
        key = self.input_license.text().strip()
        if not key:
            if not silent:
                QMessageBox.warning(self, "تنبيه", "يرجى إدخال مفتاح الترخيص أولاً.")
            return

        self.btn_activate.setEnabled(False)
        self.btn_activate.setText("جاري التحقق من السيرفر...")

        self.act_worker = ActivationWorker(self.api_url, key, self.hwid)
        self.act_thread = threading.Thread(target=self.act_worker.run, daemon=True)
        self.act_worker.finished.connect(self.handle_activation_response)
        self.act_worker.error.connect(self.handle_activation_error)
        self.act_thread.start()

    def handle_activation_response(self, data):
        self.btn_activate.setEnabled(True)
        self.btn_activate.setText("تأكيد الترخيص والدخول 🔓")
        
        if data.get("success"):
            student = data.get("student", {})
            self.license_key = student.get("key", "")
            self.student_name = student.get("name", "")
            self.student_phone = student.get("phone", "")
            self.courses = data.get("courses", [])
            self.is_authenticated = True
            
            # Save session for auto-login
            self.save_session(self.license_key)
            
            # Update UI labels
            self.student_badge.setText(f"الطالب: {self.student_name}")
            wm_text = f"🔒 {self.student_name} | {self.student_phone}" if self.student_phone else f"🔒 {self.student_name}"
            self.watermark_overlay.set_watermark_text(wm_text)
            self.sync_overlay_geometry()
            self.watermark_overlay.move_to_random_pos()
            self.watermark_timer.start()
            self.heartbeat_timer.start()
            
            # Load lessons list
            self.render_lessons()
            
            # Switch to workspace
            self.stacked_widget.setCurrentIndex(1)
        else:
            msg = data.get("message", "فشل التفعيل.")
            self.clear_session()
            QMessageBox.critical(self, "فشل تفعيل الترخيص", msg)

    def handle_activation_error(self, err_msg):
        self.btn_activate.setEnabled(True)
        self.btn_activate.setText("تأكيد الترخيص والدخول 🔓")
        QMessageBox.critical(self, "خطأ اتصال", f"تعذر الاتصال بالسيرفر السحابي:\n{err_msg}")

    def check_heartbeat_status(self):
        """Periodically checks if the student has been banned and syncs course title."""
        if not self.is_authenticated:
            return

        self.hb_worker = HeartbeatWorker(self.api_url, self.license_key, self.hwid)
        self.hb_worker.ban_detected.connect(self.handle_ban_enforcement)
        self.hb_worker.courses_synced.connect(self.handle_courses_sync)
        self.hb_thread = threading.Thread(target=self.hb_worker.run, daemon=True)
        self.hb_thread.start()

    def handle_courses_sync(self, fresh_courses):
        """Live updates course title and list when admin makes changes."""
        if not fresh_courses:
            return
        self.courses = fresh_courses
        course = self.courses[0]
        new_title = course.get("title", "")
        if self.course_sub_lbl.text() != new_title:
            self.course_sub_lbl.setText(new_title)

    def handle_ban_enforcement(self, message):
        """Enforces instant ban ordered by the Admin."""
        self.media_player.stop()
        self.heartbeat_timer.stop()
        self.watermark_timer.stop()
        self.clear_session()
        QMessageBox.critical(self, "إشعار من الإدارة 🚫", message)
        self.logout()

    def render_lessons(self):
        # Clear previous items
        for i in reversed(range(self.lessons_layout.count())):
            widget = self.lessons_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.courses:
            return

        course = self.courses[0]
        self.course_sub_lbl.setText(course.get("title", ""))
        self.current_lessons = course.get("lessons", [])
        
        self.lesson_cards = []
        for idx, lesson in enumerate(self.current_lessons):
            card = LessonCardWidget(idx, lesson)
            card.clicked.connect(self.select_lesson)
            self.lessons_layout.addWidget(card)
            self.lesson_cards.append(card)

    def select_lesson(self, index):
        if index < 0 or index >= len(self.current_lessons):
            return
            
        self.current_lesson_index = index
        lesson = self.current_lessons[index]
        
        # Highlight active card
        for i, card in enumerate(self.lesson_cards):
            card.set_selected(i == index)
            
    def get_stream_url_for_quality(self, orig_url: str, quality_index: int) -> str:
        """Translates master m3u8 to specific ultra-fast HLS quality stream."""
        if not orig_url or "playlist.m3u8" not in orig_url:
            return orig_url
        
        # 0: 720p HD, 1: 1080p FHD, 2: Auto Adaptive
        quality_map = {
            0: "720p/video.m3u8",
            1: "1080p/video.m3u8",
            2: "playlist.m3u8"
        }
        if quality_index in quality_map:
            return orig_url.replace("playlist.m3u8", quality_map[quality_index])
        return orig_url

    def select_lesson(self, index):
        if 0 <= index < len(self.current_lessons):
            self.current_lesson_index = index
            lesson = self.current_lessons[index]
            
            # Highlight active card
            for i, card in enumerate(self.lesson_cards):
                card.set_selected(i == index)
                
            self.current_title_lbl.setText(lesson.get("title", ""))
            
            # Play Stream with fast quality resolution
            stream_url = lesson.get("stream_url", "")
            resolved_url = self.get_stream_url_for_quality(stream_url, self.quality_combo.currentIndex())
            self.media_player.setSource(QUrl(resolved_url))
            self.media_player.play()
            self.btn_play_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.sync_overlay_geometry()
            self.watermark_overlay.move_to_random_pos()

    # ----------------------------------------------------
    # 5. Media Player Controls
    # ----------------------------------------------------
    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.btn_play_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.media_player.play()
            self.btn_play_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def set_position(self, pos):
        self.media_player.setPosition(pos)

    def position_changed(self, pos):
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(pos)
        self.position_slider.blockSignals(False)
        self.update_time_label(pos, self.media_player.duration())

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_label(self.media_player.position(), duration)

    def update_time_label(self, pos, dur):
        pos_t = QTime(0, 0, 0).addMSecs(pos).toString("hh:mm:ss")
        dur_t = QTime(0, 0, 0).addMSecs(dur).toString("hh:mm:ss")
        self.time_label.setText(f"{pos_t} / {dur_t}")

    def seek_relative(self, delta_ms):
        """Seeks forward or backward by delta_ms milliseconds."""
        cur = self.media_player.position()
        dur = self.media_player.duration()
        new_pos = max(0, min(dur, cur + delta_ms))
        self.media_player.setPosition(new_pos)

    def change_speed(self, index):
        """Changes playback speed."""
        speeds = [1.0, 1.25, 1.5, 1.75, 2.0, 0.75]
        if 0 <= index < len(speeds):
            self.media_player.setPlaybackRate(speeds[index])

    def change_quality(self, index):
        """Switches stream quality with instant playback preservation."""
        if self.current_lesson_index < 0 or self.current_lesson_index >= len(self.current_lessons):
            return
        
        lesson = self.current_lessons[self.current_lesson_index]
        orig_url = lesson.get("stream_url", "")
        if not orig_url:
            return
            
        cur_pos = self.media_player.position()
        was_playing = self.media_player.playbackState() == QMediaPlayer.PlayingState
        
        target_url = self.get_stream_url_for_quality(orig_url, index)
        self.media_player.setSource(QUrl(target_url))
        if was_playing:
            self.media_player.play()
        if cur_pos > 0:
            self.media_player.setPosition(cur_pos)
        self.btn_play_pause.setIcon(self.style().standardIcon(
            QStyle.SP_MediaPause if was_playing else QStyle.SP_MediaPlay
        ))

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def eventFilter(self, obj, event):
        """Global Application Event Filter: Space for Play/Pause, Arrows for Seek ±5s."""
        if self.is_authenticated and self.stacked_widget.currentIndex() == 1:
            if event.type() == QEvent.KeyPress:
                # 1. Spacebar exclusively toggles Play / Pause
                if event.key() == Qt.Key_Space:
                    self.toggle_play_pause()
                    return True
                # 2. Right Arrow seeks +5 seconds
                elif event.key() == Qt.Key_Right:
                    self.seek_relative(5000)
                    return True
                # 3. Left Arrow seeks -5 seconds
                elif event.key() == Qt.Key_Left:
                    self.seek_relative(-5000)
                    return True
                # 4. F toggles fullscreen
                elif event.key() == Qt.Key_F:
                    self.toggle_fullscreen()
                    return True
                # 5. Escape exits fullscreen
                elif event.key() == Qt.Key_Escape and self.isFullScreen():
                    self.showNormal()
                    return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Fallback Keyboard shortcuts."""
        if self.is_authenticated and self.stacked_widget.currentIndex() == 1:
            if event.key() == Qt.Key_Right:
                self.seek_relative(5000)
                event.accept()
                return
            elif event.key() == Qt.Key_Left:
                self.seek_relative(-5000)
                event.accept()
                return
            elif event.key() == Qt.Key_Space:
                self.toggle_play_pause()
                event.accept()
                return
            elif event.key() == Qt.Key_F:
                self.toggle_fullscreen()
                event.accept()
                return
            elif event.key() == Qt.Key_Escape and self.isFullScreen():
                self.showNormal()
                event.accept()
                return
        super().keyPressEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self.sync_overlay_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_overlay_geometry()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.watermark_overlay.hide()
            else:
                self.sync_overlay_geometry()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.watermark_overlay.hide()

    def showEvent(self, event):
        super().showEvent(event)
        if self.is_authenticated and self.stacked_widget.currentIndex() == 1:
            self.sync_overlay_geometry()

    def closeEvent(self, event):
        self.watermark_overlay.close()
        super().closeEvent(event)

    def logout(self):
        self.media_player.stop()
        self.is_authenticated = False
        self.watermark_timer.stop()
        self.heartbeat_timer.stop()
        self.watermark_overlay.hide()
        self.clear_session()
        self.input_license.clear()
        self.stacked_widget.setCurrentIndex(0)

# ----------------------------------------------------
# Application Launcher
# ----------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Custom font if available
    font = QFont("Cairo", 10)
    app.setFont(font)
    
    # Set App Icon globally
    icon_path = get_asset_path("app_icon.png")
    if icon_path and os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    window = TrabuildPlayerWindow()
    window.show()
    sys.exit(app.exec())
