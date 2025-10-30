import os
import sys
from django.conf import settings
import joblib
from travel_app.working_model import WorkingTravelItineraryGenerator

sys.modules['__main__'] = sys.modules['travel_app.working_model']

class TravelModelManager:
    def __init__(self):
        self.travel_model = None
        self.load_models()

    def load_models(self):
        try:
            base_ml_path = os.path.join(settings.BASE_DIR, 'travel_app', 'ml_models')
            pkl_path = os.path.join(base_ml_path, 'travel_model.pkl')
            
            intent_model_path = os.path.join(base_ml_path, 'intent_model')
            spacy_model_path = os.path.join(base_ml_path, 'spacy_model')  # optional

            # Skip intent model if required files are missing
            if not os.path.exists(os.path.join(intent_model_path, "pytorch_model.bin")):
                print("⚠️ Intent model not found, skipping intent model loading.")
                intent_model_path = None

            # Load .pkl
            loaded = joblib.load(pkl_path)

            # Initialize generator
            model_obj = WorkingTravelItineraryGenerator(
                intent_model_path=intent_model_path,
                spacy_model_path=spacy_model_path
            )

            if isinstance(loaded, dict):
                model_obj.__dict__.update(loaded)

            self.travel_model = model_obj
            print("✅ Travel model loaded successfully!")

        except Exception as e:
            print(f"❌ Error loading travel_model.pkl: {e}")
            self.travel_model = None

model_manager = TravelModelManager()
