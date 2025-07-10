import cv2, mediapipe as mp, pyautogui, time, math

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.6,
)
mp_drawing = mp.solutions.drawing_utils

LAST_TRIGGER   = 0
DEBOUNCE_SEC   = 0.8          # Minimum time (s) between two page flips
FRAME_CONFIRM  = 4            # Frames needed in a row to confirm a V-sign
v_counter      = 0            # Running count of consecutive V-sign frames
ANGLE_THRESH  = 10            # Minimum fork angle (degrees) for a valid V

def dist(p1, p2):            
    ## Euclidean distance between two landmarks (normalized coords).
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def is_v_sign(lm):
    idx_tip, mid_tip, ring_tip, pink_tip = 8, 12, 16, 20
    idx_mcp, mid_mcp, ring_mcp, pink_mcp = 5, 9, 13, 17
    wrist = lm.landmark[0]

    # Index & middle fingers must be comfortably above their MCPs
    hand_size = dist(lm.landmark[0], lm.landmark[9])  # wrist→middle MCP ≈ palm height
    up_ok = (
        lm.landmark[idx_tip].y < lm.landmark[idx_mcp].y - 0.25 * hand_size and
        lm.landmark[mid_tip].y < lm.landmark[mid_mcp].y - 0.25 * hand_size
    )

    # Ring & pinky must be clearly bent (tip below MCP)
    down_ok = (
        lm.landmark[ring_tip].y > lm.landmark[ring_mcp].y and
        lm.landmark[pink_tip].y > lm.landmark[pink_mcp].y
    )

    # Fork angle between the two extended fingers must exceed threshold
    v_angle = math.degrees(
        math.atan2(
            lm.landmark[mid_tip].y - lm.landmark[idx_tip].y,
            lm.landmark[mid_tip].x - lm.landmark[idx_tip].x
        )
    )
    angle_ok = abs(v_angle) > ANGLE_THRESH          

    return up_ok and down_ok and angle_ok

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Camera not found")

print("Hold a V-sign for ≥4 consecutive frames to flip forward. Press q to quit.")
while True:
    ok, frame = cap.read()
    if not ok:
        break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    if res.multi_hand_landmarks:
        lm = res.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        if is_v_sign(lm):
            v_counter += 1
            if v_counter >= FRAME_CONFIRM:
                now = time.time()
                if now - LAST_TRIGGER >= DEBOUNCE_SEC:
                    pyautogui.press("right")
                    LAST_TRIGGER = now
                v_counter = 0              # Reset counter after action
        else:
            v_counter = 0
    else:
        v_counter = 0                     # Reset if no hand detected

    cv2.putText(frame, f"V-count: {v_counter}/{FRAME_CONFIRM}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
    cv2.imshow("Gesture PPT Controller", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
