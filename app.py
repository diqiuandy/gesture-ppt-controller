import mediapipe as mp
import cv2, pyautogui, time

#  Model initialization 
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

model_path = "models/gesture_recognizer.task"

# Playback utility
KEY_MAP = {
    "Thumb_Up":      "left",   # Previous page
    "Thumb_Down":    "right",  # Next page
    "Victory":       "esc",    # exit the slideshow
    "Open_Palm":     "f5",     # Play the slides
    "Closed_Fist":   "b",      # Blackout/un-blackout
    "Pointing_Up":   "m",      # Mute/Unmute
}

# Gesture callback
last_time = 0
def callback(result, output, timestamp):
    global last_time
    if not result.gestures: 
        return
    category = result.gestures[0][0].category_name
    if category not in KEY_MAP or KEY_MAP[category] is None:
        return
    now = time.time()
    if now - last_time >= 1.2:         
        pyautogui.press(KEY_MAP[category])
        print(f"Detected: {category} → press {KEY_MAP[category]}")
        last_time = now

# Create recognizer
options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=callback,
)
recognizer = GestureRecognizer.create_from_options(options)

# Webcam main loop
cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    recognizer.recognize_async(mp_img, int(time.time()*1000))

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
