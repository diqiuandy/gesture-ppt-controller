import sys, time, json, threading
import cv2, pyautogui, mediapipe as mp
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QSlider, QComboBox, QPushButton, QMessageBox
)

DEFAULT_MAP = {
    "Thumb_Up": "left",      
    "Thumb_Down": "right",   
    "Victory": "esc",          
    "Open_Palm": "f5",        
    "Closed_Fist": "b",    
    "Pointing_Up": "m",
}

CONFIG_PATH = "gesture_keymap.json"
MODEL_PATH  = "models/gesture_recognizer.task"
PREVIEW_W, PREVIEW_H = 160, 120

class Config:
    keymap = DEFAULT_MAP.copy()
    debounce = 1.2

    @classmethod
    def load(cls):
        try:
            with open(CONFIG_PATH) as f:
                data = json.load(f)
            if "keymap" in data:
                for k, v in data["keymap"].items():
                    if k in DEFAULT_MAP:  
                        cls.keymap[k] = v
            if "debounce" in data:
                cls.debounce = float(data["debounce"])
        except (ValueError, FileNotFoundError):
            pass  

    @classmethod
    def save(cls):
        tidy = {k: v for k, v in cls.keymap.items() if v}
        with open(CONFIG_PATH, "w") as f:
            json.dump({"keymap": tidy, "debounce": cls.debounce}, f, indent=2)

    @classmethod
    def reset_defaults(cls):
        cls.keymap = DEFAULT_MAP.copy(); cls.debounce = 1.2; cls.save()

class GestureWorker(QObject):
    gesture = pyqtSignal(str)
    frame   = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__(); self._run = True; self._last = 0
        opts = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            result_callback=self._callback)
        self.recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(opts)
        self.cap = cv2.VideoCapture(0)

    def _callback(self, res, *_):
        if not res.gestures: return
        cat = res.gestures[0][0].category_name
        key = Config.keymap.get(cat)
        if not key: return
        if time.time() - self._last < Config.debounce: return
        if QApplication.activeWindow() and QApplication.activeWindow().windowTitle() == "Gesture Slide Navigator":
            print("⚠ UI in focus, skip keypress"); self._last = time.time(); self.gesture.emit(cat); return
        pyautogui.press(key); self._last = time.time()
        print(f"{cat:<12} → {key}"); self.gesture.emit(cat)

    def run(self):
        while self._run and self.cap.isOpened():
            ok, frame = self.cap.read();
            if not ok: continue
            small = cv2.cvtColor(cv2.resize(frame, (PREVIEW_W, PREVIEW_H)), cv2.COLOR_BGR2RGB)
            h, w, ch = small.shape
            self.frame.emit(QPixmap.fromImage(QImage(small.data, w, h, ch*w, QImage.Format.Format_RGB888)))
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            try:
                self.recognizer.recognize_async(mp_img, int(time.time()*1000))
            except Exception:
                pass
            time.sleep(0.01)
        self.cap.release()

    def stop(self):
        self._run = False

class MainWindow(QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Gesture Slide Navigator"); self.setWindowFlags(self.windowFlags()|Qt.WindowStaysOnTopHint)
        Config.load(); self._build_ui(); self._start_worker()

    def _build_ui(self):
        self.status = QLabel("Waiting…", alignment=Qt.AlignCenter)
        self.status.setStyleSheet("font-size:24px;padding:6px;border-radius:12px;background:#444;color:#fff;")
        self.preview = QLabel(); self.preview.setFixedSize(PREVIEW_W, PREVIEW_H); self.preview.setStyleSheet("border:1px solid #999;")
        header = QHBoxLayout(); header.addWidget(self.status, 1); header.addWidget(self.preview)

        keys = ["left","right","up","down","f5","esc","b","m","space","enter","pageup","pagedown"]
        self.combo = {}; map_layout = QVBoxLayout()
        for gest in DEFAULT_MAP:
            row = QHBoxLayout(); row.addWidget(QLabel(gest))
            cb = QComboBox(); cb.addItems(keys); cb.setCurrentText(Config.keymap.get(gest, ""))
            cb.activated.connect(lambda idx, g=gest, box=cb: self._change_mapping(g, box.currentText()))
            self.combo[gest] = cb; row.addWidget(cb); map_layout.addLayout(row)

        self.slider = QSlider(Qt.Horizontal); self.slider.setRange(3, 30); self.slider.setValue(int(Config.debounce*10))
        self.slider.valueChanged.connect(self._set_debounce)

        reset_btn = QPushButton("Reset to Defaults"); reset_btn.clicked.connect(self._reset_defaults)

        lay = QVBoxLayout(); lay.addLayout(header); lay.addLayout(map_layout)
        lay.addWidget(QLabel("Debounce (s):")); lay.addWidget(self.slider); lay.addWidget(reset_btn)
        self.setLayout(lay); self.resize(550, 540)

    def _start_worker(self):
        self.worker = GestureWorker(); th = threading.Thread(target=self.worker.run, daemon=True); th.start()
        self.worker.gesture.connect(self._flash_status); self.worker.frame.connect(self.preview.setPixmap)

    def _change_mapping(self, gesture, key):
        Config.keymap[gesture] = key
        Config.save()
        self.worker._last = 0  
        print(f"✍ {gesture:<10} -> {key}")
    def _set_debounce(self, val):
        Config.debounce = val/10; Config.save(); print(f"⏱ debounce = {Config.debounce:.1f}s")
    def _reset_defaults(self):
        if QMessageBox.question(self, "Reset", "Restore default gesture mappings?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            Config.reset_defaults();
            for gest, cb in self.combo.items(): cb.setCurrentText(Config.keymap[gest])
            self.slider.setValue(int(Config.debounce*10))
            print("🔄  Restored default mappings")
    def _flash_status(self, cat):
        self.status.setText(cat); self.status.setStyleSheet("font-size:24px;padding:6px;border-radius:12px;background:#28a745;color:#fff;")
        QTimer.singleShot(800, lambda: self.status.setStyleSheet("font-size:24px;padding:6px;border-radius:12px;background:#444;color:#fff;"))
    def closeEvent(self, e):
        self.worker.stop(); e.accept()

# ------------------------------ main -----------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
