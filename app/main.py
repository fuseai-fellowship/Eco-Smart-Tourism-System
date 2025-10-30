from fastapi import FastAPI
import joblib
import pandas as pd
import numpy as np
from tensorflow import keras

# ------------------ 1️⃣ Load Model and Preprocessor ------------------
# Load pre-trained Keras model
model = keras.models.load_model("trained_risk_model.keras", safe_mode=False)

# Load preprocessing pipeline (e.g., OneHotEncoder, StandardScaler)
preprocessor = joblib.load("preprocessor.joblib")

# Define class labels (same order as your training)
class_names = np.array(["low", "moderate", "high", "critical"])

# Define weights for calculating overall risk score
risk_weights = np.array([0, 33, 66, 100])

# ------------------ 2️⃣ Initialize FastAPI ------------------
app = FastAPI(
    title="Traveller Risk Prediction API",
    description="Analyzes wearable and environmental data to predict traveller risk level.",
    version="1.0.0"
)

# ------------------ 3️⃣ Root Endpoint ------------------
@app.get("/")
def read_root():
    return {"message": "Traveller Risk Prediction API is running!"}


# ------------------ 4️⃣ Prediction Endpoint ------------------
@app.post("/predict/")
def predict_risk(data: dict):
    """
    Accepts traveller data and returns:
    - Predicted risk label
    - Confidence score
    - Overall risk score (0–100)
    """
    try:
        # Step 1 — Convert JSON to DataFrame
        input_df = pd.DataFrame([data])

        # Step 2 — Apply preprocessing (encode categorical, scale numerical)
        X_processed = preprocessor.transform(input_df)

        # Step 3 — Get model predictions
        probabilities = model.predict(X_processed)
        predicted_index = int(np.argmax(probabilities, axis=1)[0])
        predicted_label = class_names[predicted_index]
        confidence = float(probabilities[0][predicted_index])

        # Step 4 — Compute overall risk score (weighted average)
        risk_score = float(np.sum(probabilities * risk_weights))

        # Step 5 — Add human-readable risk level with thresholds
        if confidence < 0.6:
            final_label = "uncertain"
        else:
            final_label = predicted_label

        # Step 6 — Return JSON response
        return {
            "predicted_risk_level": final_label,
            "confidence": round(confidence, 3),
            "risk_score": round(risk_score, 2),
            "probabilities": {
                "low": round(float(probabilities[0][0]), 3),
                "moderate": round(float(probabilities[0][1]), 3),
                "high": round(float(probabilities[0][2]), 3),
                "critical": round(float(probabilities[0][3]), 3),
            },
        }

    except Exception as e:
        return {"error": str(e)}
