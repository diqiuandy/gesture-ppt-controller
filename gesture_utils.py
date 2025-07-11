import math

def dist(p1, p2):
    """Euclidean distance between two MediaPipe landmarks (normalized)."""
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def is_v_sign(lm, hand_size, angle_thresh):
    """Geometry‑rule check for V‑sign using landmarks (single hand)."""
    idx_tip, mid_tip, ring_tip, pink_tip = 8, 12, 16, 20
    idx_mcp, mid_mcp, ring_mcp, pink_mcp = 5, 9, 13, 17

    up_ok = (
        lm[idx_tip].y < lm[idx_mcp].y - 0.25 * hand_size and
        lm[mid_tip].y < lm[mid_mcp].y - 0.25 * hand_size
    )
    down_ok = (
        lm[ring_tip].y > lm[ring_mcp].y and
        lm[pink_tip].y > lm[pink_mcp].y
    )
    v_angle = math.degrees(
        math.atan2(lm[mid_tip].y - lm[idx_tip].y,
                   lm[mid_tip].x - lm[idx_tip].x)
    )
    angle_ok = abs(v_angle) > angle_thresh
    return up_ok and down_ok and angle_ok
