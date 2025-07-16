import sys, time, json, threading
import cv2, pyautogui, mediapipe as mp
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QSlider, QComboBox, QPushButton, QTextEdit, QGraphicsDropShadowEffect
)

DEFAULT_MAP = {
    "Thumb_Up": "left", "Thumb_Down": "right", "Victory": "esc",
    "Open_Palm": "f5", "Closed_Fist": "b", "Pointing_Up": "m"
}
CONFIG_PATH = "gesture_keymap.json"
MODEL_PATH = "models/gesture_recognizer.task"
PREVIEW_W, PREVIEW_H = 160, 120

class Config:
    keymap = DEFAULT_MAP.copy()
    debounce = 1.2
    @classmethod
    def load(cls):
        try:
            with open(CONFIG_PATH) as f:
                d = json.load(f)
                cls.keymap.update(d.get("keymap", {}))
                cls.debounce = float(d.get("debounce", cls.debounce))
        except: pass
    @classmethod
    def save(cls):
        json.dump({"keymap": cls.keymap, "debounce": cls.debounce}, open(CONFIG_PATH, "w"), indent=2)

class GestureWorker(QObject):
    gesture = pyqtSignal(str)
    frame = pyqtSignal(QPixmap)
    def __init__(self):
        super().__init__()
        self._last = 0
        self._run = True
        opts = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            result_callback=self._cb
        )
        self.recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(opts)
        self.cap = cv2.VideoCapture(0)
    def _cb(self, res, *_):
        if not res.gestures:
            return
        cat = res.gestures[0][0].category_name
        key = Config.keymap.get(cat)
        if not key or time.time() - self._last < Config.debounce:
            return

        from PyQt5.QtWidgets import QApplication          
        aw = QApplication.activeWindow()
        if aw and aw.windowTitle().startswith("Gesture Navigator"):
            print("UI in focus, skip keypress")
            self._last = time.time()
            self.gesture.emit(f"SKIP:{cat}")      
            return

        pyautogui.press(key)
        self._last = time.time()
        print(f"{cat:<12} → {key}")
        self.gesture.emit(cat)
    def run(self):
        while self._run and self.cap.isOpened():
            ok, frm = self.cap.read()
            if ok:
                rgb = cv2.cvtColor(cv2.resize(frm, (PREVIEW_W, PREVIEW_H)), cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                self.frame.emit(QPixmap.fromImage(QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)))
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))
                try:
                    self.recognizer.recognize_async(mp_img, int(time.time() * 1000))
                except:
                    pass
            time.sleep(0.01)
        self.cap.release()
    def stop(self):
        self._run = False

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        Config.load()
        self._theme()
        self._ui()
        self._start()

    def _theme(self):
        app.setStyle("Fusion")
        pal = QPalette()
        base = QColor("#2e3440")
        txt = QColor("#d8dee9")
        pal.setColor(QPalette.Window, base)
        pal.setColor(QPalette.Base, QColor("#3b4252"))
        pal.setColor(QPalette.Button, QColor("#434c5e"))
        pal.setColor(QPalette.ButtonText, txt)
        pal.setColor(QPalette.Text, txt)
        pal.setColor(QPalette.WindowText, txt)
        pal.setColor(QPalette.Highlight, QColor("#88c0d0"))
        app.setPalette(pal)
        app.setFont(QFont("Segoe UI", 11, QFont.Bold))

    def _glass(self, wid):
        eff = QGraphicsDropShadowEffect(blurRadius=20, xOffset=0, yOffset=0)
        eff.setColor(QColor(0, 0, 0, 150))
        wid.setGraphicsEffect(eff)

    def _ui(self):
        self.setWindowTitle("Gesture Navigator ✋")
        self.setFixedSize(570, 560)

        self.status = QLabel("Waiting…", alignment=Qt.AlignCenter)
        self.status.setFixedHeight(48)
        self.status.setStyleSheet("font-size:24px;border-radius:20px;background:#4c566a;color:#eceff4;")
        self._glass(self.status)

        self.preview = QLabel()
        self.preview.setFixedSize(PREVIEW_W, PREVIEW_H)
        self.preview.setStyleSheet("border-radius:10px;border:2px solid #4c566a;")

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedSize(220, PREVIEW_H)
        self.log.setStyleSheet("background:#3b4252;border-radius:8px;color:#d8dee9;font-family:Consolas;font-size:10pt;")

        head = QHBoxLayout()
        head.addWidget(self.status, 1)
        head.addWidget(self.preview)
        head.addWidget(self.log)

        keys = ["left", "right", "up", "down", "f5", "esc", "b", "m", "space", "enter", "pageup", "pagedown"]
        self.combo = {}
        maps = QVBoxLayout()
        for g in DEFAULT_MAP:
            row = QHBoxLayout()
            lab = QLabel(g)
            lab.setMinimumWidth(110)
            cb = QComboBox()
            cb.addItems(keys)
            cb.setCurrentText(Config.keymap.get(g))
            cb.setStyleSheet("QComboBox{background:#3b4252;border-radius:8px;padding:4px;}QComboBox::drop-down{width:18px;}")
            cb.activated.connect(lambda idx, gg=g, box=cb: self._set_map(gg, box.currentText()))
            self.combo[g] = cb
            row.addWidget(lab)
            row.addWidget(cb)
            maps.addLayout(row)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(3, 30)
        self.slider.setValue(int(Config.debounce * 10))
        self.slider.valueChanged.connect(self._set_db)
        self.slider.setStyleSheet("QSlider::groove:horizontal{height:6px;border-radius:3px;background:#4c566a;}QSlider::handle:horizontal{background:#88c0d0;width:16px;border-radius:8px;margin:-5px 0;}")

        btn = QPushButton("Reset")
        btn.clicked.connect(self._reset)
        btn.setStyleSheet("QPushButton{background:#5e81ac;color:#eceff4;border:none;border-radius:10px;padding:6px 14px;}QPushButton:hover{background:#81a1c1;}")

        lay = QVBoxLayout()
        lay.setSpacing(16)
        lay.addLayout(head)
        lay.addLayout(maps)
        lay.addWidget(QLabel("Debounce (s):"))
        lay.addWidget(self.slider)
        lay.addWidget(btn)
        self.setLayout(lay)

    def _start(self):
        self.worker = GestureWorker()
        threading.Thread(target=self.worker.run, daemon=True).start()
        self.worker.gesture.connect(self._flash)
        self.worker.frame.connect(self.preview.setPixmap)

    def _set_map(self, g, k):
        Config.keymap[g] = k
        Config.save()
        self.worker._last = 0
        msg = f"✍ {g} → {k}"
        self.log.append(msg)
        print(msg)

    def _set_db(self, v):
        Config.debounce = v / 10
        Config.save()
        msg = f"⏱ debounce → {Config.debounce:.1f}s"
        self.log.append(msg)
        print(msg)

    def _reset(self):
        Config.keymap.update(DEFAULT_MAP)
        Config.debounce = 1.2
        Config.save()
        for g, cb in self.combo.items():
            cb.setCurrentText(Config.keymap[g])
        self.slider.setValue(int(Config.debounce * 10))

    def _flash(self, cat):
        skipped = False
        if cat.startswith("SKIP:"):
            skipped = True
            cat = cat[5:]               

        neon = {
            "Thumb_Up": "#a3be8c", "Thumb_Down": "#ebcb8b", "Victory": "#88c0d0",
            "Open_Palm": "#b48ead", "Closed_Fist": "#bf616a", "Pointing_Up": "#eccc8b"
        }.get(cat, "#81a1c1")

        self.status.setText(cat)
        self.status.setStyleSheet(
            f"font-size:24px;border-radius:20px;background:{neon};color:#2e3440;"
        )

        if skipped:
            self.log.append(f"⚠ {cat} skipped (UI in focus)")
        else:
            self.log.append(f"{cat} detected → {Config.keymap.get(cat)}")

        QTimer.singleShot(
            700,
            lambda: self.status.setStyleSheet(
                "font-size:24px;border-radius:20px;background:#4c566a;color:#eceff4;"
            ),
        )

    def closeEvent(self, e):
        self.worker.stop()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())
