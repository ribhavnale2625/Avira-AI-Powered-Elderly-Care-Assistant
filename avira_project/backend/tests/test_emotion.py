import sys
sys.path.insert(0, '.')
from modules.emotion_classifier import EmotionClassifier

ec = EmotionClassifier()

tests = [
    "i m not happy today",
    "i am not happy today",
    "i am sad",
    "hello how are you",
    "i feel terrible",
    "i am feeling great",
    "i am worried about my health",
    "turn on the lights",
    "play some music",
    "i feel so lonely",
]

print("\n=== DistilBERT Emotion Model Test ===")
for t in tests:
    result = ec.predict(t)
    print(f"  '{t}' -> {result}")
print("=====================================")
