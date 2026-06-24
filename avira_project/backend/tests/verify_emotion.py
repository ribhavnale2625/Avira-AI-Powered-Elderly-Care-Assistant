import sys
import os

# Add the project root to sys.path to allow module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.emotion_classifier import EmotionClassifier

def test():
    try:
        classifier = EmotionClassifier(model_path="models/emotion_model")
        
        test_sentences = [
            ("I am so happy and excited today!", "joy"),
            ("I feel so lonely and sad...", "sadness"),
            ("I love my family so much.", "love"),
            ("I am very angry with this service!", "anger"),
            ("I am a bit scared about the surgery.", "fear"),
            ("Oh wow, what a surprise!", "surprise")
        ]
        
        print("\n" + "="*50)
        print("  EMOTION MODEL VERIFICATION")
        print("="*50)
        
        passed = 0
        for text, expected in test_sentences:
            prediction = classifier.predict(text)
            status = "✅ PASS" if prediction == expected else "❌ FAIL"
            print(f"Text: '{text}'")
            print(f"Target: {expected} | Predicted: {prediction} | {status}\n")
            if prediction == expected:
                passed += 1
                
        print(f"Result: {passed}/{len(test_sentences)} passed.")
        
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    test()
