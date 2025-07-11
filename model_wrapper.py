"""Abstraction layer – now returns RULE label; later swap in ML model."""

from gesture_utils import is_v_sign, dist

class RuleBasedClassifier:
    def __init__(self, cfg):
        self.angle_thresh = cfg['angle_thresh']
    def predict(self, landmarks):
        hand_size = dist(landmarks[0], landmarks[9])
        return "V_SIGN" if is_v_sign(landmarks, hand_size, self.angle_thresh) else None

def load_model(cfg):
    # placeholder – expand to load MediaPipe or ONNX later
    return RuleBasedClassifier(cfg)
