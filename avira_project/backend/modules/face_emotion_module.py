import logging
import gc
import numpy as np
import cv2

logger = logging.getLogger("FaceEmotionModule")

# Mapping from FER labels → AVIRA emotion types
FER_TO_AVIRA = {
    "angry":    "anger",
    "disgust":  "anger",      # map disgust → anger for simplicity
    "fear":     "fear",
    "happy":    "joy",
    "sad":      "sadness",
    "surprise": "surprise",
    "neutral":  "neutral",
}

# AVIRA emotion → radar-chart score keys
AVIRA_SCORE_MAP = {
    "joy":      {"joy": 85, "love": 30, "sadness": 5,  "anger": 5,  "fear": 5,  "surprise": 10},
    "anger":    {"joy": 5,  "love": 5,  "sadness": 15, "anger": 85, "fear": 20, "surprise": 10},
    "fear":     {"joy": 5,  "love": 5,  "sadness": 25, "anger": 15, "fear": 85, "surprise": 30},
    "sadness":  {"joy": 5,  "love": 10, "sadness": 85, "anger": 10, "fear": 20, "surprise": 5},
    "surprise": {"joy": 30, "love": 10, "sadness": 5,  "anger": 5,  "fear": 15, "surprise": 85},
    "neutral":  {"joy": 20, "love": 15, "sadness": 10, "anger": 10, "fear": 10, "surprise": 10},
}


class FaceEmotionDetector:
    """Lightweight face emotion detector using FER (FER-2013 CNN)."""

    def __init__(self):
        self._detector = None
        self._initialized = False
        self._init_error = None

    def _lazy_init(self):
        """Lazy-load the FER detector (TensorFlow is heavy, only load when needed)."""
        if self._initialized:
            return
        try:
            from fer.fer import FER
            # mtcnn=True uses MTCNN neural network for much better face detection
            self._detector = FER(mtcnn=True)
            self._initialized = True
            logger.info("FER face emotion detector initialized (MTCNN mode)")
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"Failed to initialize FER detector: {e}")
            self._initialized = True  # prevent retry loops

    def detect(self, image_bytes: bytes) -> dict:
        """
        Detect emotion from a JPEG image. Image data is deleted after processing.

        Args:
            image_bytes: Raw JPEG bytes of the image

        Returns:
            {
                "face_detected": bool,
                "emotion": str (AVIRA emotion type),
                "confidence": float (0-100),
                "fer_scores": { "angry": float, ... },
                "avira_scores": { "joy": float, ... }
            }
        """
        self._lazy_init()

        if self._detector is None:
            return {
                "face_detected": False,
                "emotion": "neutral",
                "confidence": 0,
                "error": self._init_error or "Detector not available"
            }

        img = None
        nparr = None
        try:
            # Decode JPEG bytes → OpenCV image (BGR)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return {"face_detected": False, "emotion": "neutral", "confidence": 0,
                        "error": "Could not decode image"}

            # Run FER detection
            results = self._detector.detect_emotions(img)

            if not results:
                return {"face_detected": False, "emotion": "neutral", "confidence": 0}

            # Take the first (largest) face
            face = results[0]
            fer_scores = face["emotions"]  # {"angry": 0.02, "happy": 0.85, ...}

            # Find dominant emotion
            dominant = max(fer_scores, key=fer_scores.get)
            confidence = round(fer_scores[dominant] * 100, 1)

            # Map to AVIRA emotion type
            avira_emotion = FER_TO_AVIRA.get(dominant, "neutral")
            avira_scores = AVIRA_SCORE_MAP.get(avira_emotion, AVIRA_SCORE_MAP["neutral"])

            return {
                "face_detected": True,
                "emotion": avira_emotion,
                "confidence": confidence,
                "fer_emotion": dominant,
                "fer_scores": {k: round(v * 100, 1) for k, v in fer_scores.items()},
                "avira_scores": avira_scores,
            }

        except Exception as e:
            logger.error(f"Face emotion detection error: {e}")
            return {"face_detected": False, "emotion": "neutral", "confidence": 0,
                    "error": str(e)}

        finally:
            # ── Explicitly delete all image data from memory ──────────
            del img
            del nparr
            del image_bytes
            gc.collect()

