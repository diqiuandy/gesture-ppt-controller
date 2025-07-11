import cv2, yaml, time, pyautogui, mediapipe as mp
from model_wrapper import load_model

CFG = yaml.safe_load(open('config.yaml'))

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.6,
)
mp_draw = mp.solutions.drawing_utils

model = load_model(CFG)

last_trigger = 0
v_counter = 0
frame_confirm = CFG['frame_confirm']
debounce_sec = CFG['debounce_sec']

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError('Camera not found')
print('Running… press q to quit')

while True:
    ok, frame = cap.read()
    if not ok:
        break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    if res.multi_hand_landmarks:
        lm = res.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        gesture = model.predict(lm.landmark)
        if gesture == 'V_SIGN':
            v_counter += 1
            if v_counter >= frame_confirm:
                now = time.time()
                if now - last_trigger >= debounce_sec:
                    pyautogui.press(CFG['key_bindings']['V_SIGN'])
                    last_trigger = now
                v_counter = 0
        else:
            v_counter = 0
    else:
        v_counter = 0

    cv2.putText(frame, f'V: {v_counter}/{frame_confirm}', (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, tuple(CFG['hud']['text']), 2)
    cv2.imshow('Gesture Controller', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
