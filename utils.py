import json
import os
from datetime import datetime

# ==============================
# GLOBAL TEMP STRUCTURE
# ==============================
def initialize_temp():
    return {
        "demographics": {},
        "level_1_eye_tracking": {},
        "level_2_facial": {},
        "level_3_questionnaire": {}
    }


# ==============================
# SAVE JSON
# ==============================
def save_temp_json(data, filename="temp_result.json"):
    os.makedirs("temp", exist_ok=True)

    filepath = os.path.join("temp", filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    return filepath


# ==============================
# LEVEL 1 BUILDER
# ==============================
def build_eye_data(features, prediction, confidence):
    return {
        "features": {
            "path_length": float(features[0]),
            "avg_velocity": float(features[1]),
            "fixation_count": float(features[2]),
            "saccade_ratio": float(features[3]),
            "dispersion": float(features[4]),
            "scan_entropy": float(features[5])
        },
        "prediction": prediction,
        "confidence": round(float(confidence), 2)   # ✅ ensure %
    }


# ==============================
# LEVEL 2 BUILDER
# ==============================
def build_face_data(autism_prob, non_autism_prob, threshold, decision, confidence):
    return {
        "autism_probability": float(autism_prob),
        "non_autism_probability": float(non_autism_prob),
        "threshold": float(threshold),
        "prediction": decision,
        "confidence": round(float(confidence), 2)
    }


# ==============================
# LEVEL 3 BUILDER
# ==============================
def build_ques_data(total_traits, prediction, autism_prob, confidence):
    return {
        "total_traits": int(total_traits),
        "max_traits": 10,
        "prediction": prediction,
        "autism_probability": float(autism_prob),
        "confidence": round(float(confidence), 2) 
    }

# ==============================
# DEMOGRAPHICS BUILDER
# ==============================
def build_demographics(age, gender, jaundice, family_asd, ethnicity=None, who_completed=None):
    return {
        "age": float(age),
        "gender": gender,
        "jaundice": str(jaundice).lower() == "yes",
        "family_asd": str(family_asd).lower() == "yes",
        "ethnicity": ethnicity if ethnicity else "Not specified",
        "who_completed": who_completed if who_completed else "Not specified"
    }


# ==============================
# OPTIONAL: UNIQUE FILE NAME
# ==============================
def generate_filename():
    return f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"