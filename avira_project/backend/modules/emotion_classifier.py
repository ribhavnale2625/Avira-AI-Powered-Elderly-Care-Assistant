import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import re
import os

# Negation words that flip emotion polarity
NEGATION_WORDS = {"not", "no", "never", "don't", "dont", "doesn't", "doesnt",
                  "didn't", "didnt", "wasn't", "wasnt", "isn't", "isnt",
                  "won't", "wont", "can't", "cant", "couldn't", "couldnt",
                  "shouldn't", "shouldnt", "hardly", "barely", "neither", "nor"}

# When negation is detected, positive ↔ negative emotion flips
NEGATION_FLIP = {
    "joy":      "sadness",
    "love":     "sadness",
    "sadness":  "joy",
    "anger":    "joy",
    "fear":     "joy",
    "surprise": "surprise",  # surprise is ambiguous, keep it
}


class EmotionClassifier:
    def __init__(self, model_path="models/emotion_model"):
        self.model_path = model_path
        self.device = torch.device("cpu")

        print(f"Loading emotion model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)
        self.model.eval()

        # Normalize id2label keys to int for consistent lookup
        raw = self.model.config.id2label
        self.id2label = {}
        for k, v in raw.items():
            self.id2label[int(k)] = v
        self.labels = list(self.id2label.values())
        print(f"Model loaded with labels: {self.labels}")

    def _has_negation(self, text: str) -> bool:
        """Check if text contains negation words near emotion words."""
        words = set(re.findall(r"[a-z']+", text.lower()))
        return bool(words & NEGATION_WORDS)

    def predict(self, text: str) -> str:
        """Returns the emotion label for the given text (negation-aware)."""
        if not text:
            return "neutral"

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            predicted_class_id = torch.argmax(logits, dim=-1).item()

        emotion = self.id2label[predicted_class_id]

        # Negation-aware post-processing
        if self._has_negation(text):
            flipped = NEGATION_FLIP.get(emotion, emotion)
            if flipped != emotion:
                print(f"  [Negation] '{text}' - {emotion} -> {flipped}")
                emotion = flipped

        return emotion

    def predict_with_scores(self, text: str) -> dict:
        """Returns emotion label + all class probabilities."""
        if not text:
            return {"emotion": "neutral", "scores": {l: 0.0 for l in self.labels}}

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)[0]
            predicted_class_id = torch.argmax(probs).item()

        emotion = self.id2label[predicted_class_id]
        scores = {self.id2label[i]: round(probs[i].item() * 100, 1) for i in range(len(probs))}

        # Negation handling
        if self._has_negation(text):
            flipped = NEGATION_FLIP.get(emotion, emotion)
            if flipped != emotion:
                print(f"  [Negation] '{text}' - {emotion} -> {flipped}")
                emotion = flipped

        return {"emotion": emotion, "scores": scores}

