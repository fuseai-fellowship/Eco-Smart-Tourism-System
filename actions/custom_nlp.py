# actions/custom_nlp.py
import spacy
import torch
import json
import os
import torch.nn.functional as F
from transformers import BertTokenizer, BertForSequenceClassification


class CustomNLPPipeline:
    """Custom NLP pipeline integrating:
    - BERT (Intent Classification)
    - spaCy (NER Extraction)
    """

    def __init__(self):
        print("🚀 Loading spaCy NER + BERT Intent Classifier on CPU...")

        # --------------------------
        # Load spaCy NER model
        # --------------------------
        spacy_path = "./models/spacy_ner_model"
        if not os.path.exists(spacy_path):
            raise FileNotFoundError(f"spaCy NER model not found at: {spacy_path}")
        self.spacy_model = spacy.load(spacy_path)

        # --------------------------
        # Load tokenizer & find checkpoint
        # --------------------------
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

        intent_model_dir = "./models/intent_model"
        checkpoints = [
            d for d in os.listdir(intent_model_dir)
            if os.path.isdir(os.path.join(intent_model_dir, d)) and d.startswith("checkpoint")
        ]
        if not checkpoints:
            raise FileNotFoundError(f"No checkpoints found in {intent_model_dir}")

        # Use latest checkpoint
        latest_checkpoint = sorted(checkpoints, key=lambda x: int(x.split("-")[1]))[-1]
        model_path = os.path.join(intent_model_dir, latest_checkpoint)

        # --------------------------
        # Load BERT model
        # --------------------------
        self.model = BertForSequenceClassification.from_pretrained(
            model_path,
            local_files_only=True
        )
        self.model.to("cpu")
        self.model.eval()

        # --------------------------
        # Load label map
        # --------------------------
        label_map_path = os.path.join(model_path, "label_map.json")
        if not os.path.exists(label_map_path):
            raise FileNotFoundError(f"Label map not found at {label_map_path}")
        with open(label_map_path, "r") as f:
            label_map = json.load(f)
        self.label_map = label_map["label2id"]
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}

        print(f"✅ Models loaded successfully from {latest_checkpoint}!")

    # --------------------------------------------------------
    # BERT INTENT PREDICTION
    # --------------------------------------------------------
    def predict_intent(self, text: str):
        """Use fine-tuned BERT to predict intent + confidence"""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128
        )
        inputs = {k: v.to("cpu") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=1)
            confidence, predicted_label = torch.max(probs, dim=1)
            confidence = confidence.item()
            predicted_label = predicted_label.item()

        intent = self.reverse_label_map.get(predicted_label, "unknown")
        return intent, confidence

    # --------------------------------------------------------
    # spaCy ENTITY EXTRACTION
    # --------------------------------------------------------
    def extract_entities(self, text: str):
        """Use spaCy to extract entities and map to Rasa's DESTINATION"""
        doc = self.spacy_model(text)
        entities = []
        for ent in doc.ents:
            label = ent.label_.upper()
            mapped_label = (
                "DESTINATION" if label in ["GPE", "LOC", "CITY", "PLACE", "LOCATION"] else label
            )
            entities.append({
                "entity": mapped_label,
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 0.9,  # heuristic, as spaCy doesn’t output score by default
                "extractor": "spacy",
            })
        return entities

    # --------------------------------------------------------
    # MAIN ANALYSIS METHOD
    # --------------------------------------------------------
    def analyze(self, text: str):
        """Run both intent + entity extraction"""
        try:
            intent, confidence = self.predict_intent(text)
            entities = self.extract_entities(text)
            return {
                "intent": intent,
                "confidence": confidence,
                "entities": entities
            }
        except Exception as e:
            print(f"⚠️ Error during NLP analysis: {e}")
            return {"intent": "unknown", "confidence": 0.0, "entities": []}


# --------------------------------------------------------
# 🔹 Standalone test mode
# --------------------------------------------------------
if __name__ == "__main__":
    nlp = CustomNLPPipeline()
    test_texts = [
        "hi",
        "I want to visit Pokhara next week",
        "Plan a 3-day trip to Dolakha",
        "What is my budget for this trip?",
        "Show me popular hotels in Chitwan",
        "bye"
    ]

    for text in test_texts:
        result = nlp.analyze(text)
        print(f"\n🧠 Text: {text}")
        print("→ Intent:", result["intent"], f"({result['confidence']:.2f})")
        print("→ Entities:", result["entities"])
        print("-" * 60)
