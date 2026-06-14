from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from catboost import CatBoostClassifier
import numpy as np
import pandas as pd
import joblib
import torch
import torchvision
from torchvision import transforms
from PIL import Image
import io
import json
import os
from pdf_generator import generate_pdf
from fastapi.responses import FileResponse


from fastapi.middleware.cors import CORSMiddleware
from llm import generate_report_from_json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# TEMP STORAGE (for combining all 3 levels)
TEMP_RESULT = {
    "demographics": {},
    "level_1_eye_tracking": {},
    "level_2_facial": {},
    "level_3_questionnaire": {}
}


def save_temp_json():
    os.makedirs("temp", exist_ok=True)
    with open("temp/temp_result.json", "w") as f:
        json.dump(TEMP_RESULT, f, indent=4)

# ==============================
# LOAD EYE MODEL (LEVEL 1)
# ==============================
model = joblib.load("models/rf_eye_model.pkl")
scaler = joblib.load("models/scaler_eye.pkl")

# ==============================
# LOAD FACE MODEL (LEVEL 2)
# ==============================
face_model = torchvision.models.resnet50(weights=None)

face_model.maxpool = torch.nn.AvgPool2d(kernel_size=3, stride=2, padding=1)
face_model.fc = torch.nn.Linear(face_model.fc.in_features, 2)

face_model.load_state_dict(torch.load("models/resnet_face_model.pth", map_location=DEVICE))
face_model.to(DEVICE)
face_model.eval()

face_transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
])

# ==============================
# INPUT SCHEMA
# ==============================

class InputData(BaseModel):
    features: list[float]

# ==============================
# ROOT ROUTE
# ==============================

@app.get("/")
def home():
    return {"message": "Backend is running 🚀"}

# ==============================
# LEVEL 1: EYE PREDICTION (FIXED)
# ==============================

@app.post("/predict-eye")
def predict_eye(data: InputData):

    print("Incoming features:", data.features)

    if len(data.features) != 6:
        return {"error": f"Expected 6 features, got {len(data.features)}"}

    X = np.array(data.features, dtype=float).reshape(1, -1)
    X = scaler.transform(X)

    pred = int(model.predict(X)[0])
    label = "Autistic" if pred == 1 else "Non-Autistic"
    probs = model.predict_proba(X)[0]

    autism_prob = probs[1]
    non_autism_prob = probs[0]

    # 🔥 FIXED CONFIDENCE
    final_conf = autism_prob if pred == 1 else non_autism_prob

    print("Prediction:", pred)
    print("Autism Prob:", autism_prob)
    print("Non-Autism Prob:", non_autism_prob)
    print("Final Confidence:", final_conf)

    # SAVE TO TEMP JSON
    TEMP_RESULT["level_1_eye_tracking"] = {
        "features": {
            "path_length": float(data.features[0]),
            "avg_velocity": float(data.features[1]),
            "fixation_count": float(data.features[2]),
            "saccade_ratio": float(data.features[3]),
            "dispersion": float(data.features[4]),
            "scan_entropy": float(data.features[5])
        },
        "prediction": label,
        "confidence": round(final_conf, 2)
    }

    save_temp_json()

    return {
        "prediction": label,
        "confidence": round(final_conf, 2)
    }

# ==============================
# LEVEL 2: FACE PREDICTION (FIXED)
# ==============================

@app.post("/predict-face")
async def predict_face(file: UploadFile = File(...)):

    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    image = face_transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        output = face_model(image)
        temperature = 2.0 
        probs = torch.softmax(output / temperature, dim=1)

    confidence_autism = probs[0][1].item()
    confidence_non_autism = probs[0][0].item()

    best_thresh = 0.47
    prediction = "Autistic" if confidence_autism > best_thresh else "Non-Autistic"

    final_confidence = confidence_autism if prediction == "Autistic" else confidence_non_autism

    # ==========================
    # DEBUG OUTPUT
    # ==========================
    print("\n===== FACE MODEL ANALYSIS =====")

    print("Logits:", output.cpu().numpy())
    print("Softmax Probabilities:", probs.cpu().numpy())

    print(f"Autism Probability: {confidence_autism:.4f}")
    print(f"Non-Autism Probability: {confidence_non_autism:.4f}")

    print("Threshold Used:", best_thresh)
    print("Final Confidence Used:", final_confidence)

    print("Decision Rule: prob > threshold ?")
    print(f"{confidence_autism:.4f} > {best_thresh} → {prediction}")

    print("================================\n")

    # SAVE TO TEMP JSON
    TEMP_RESULT["level_2_facial"] = {
        "autism_probability": round(confidence_autism, 4),
        "non_autism_probability": round(confidence_non_autism, 4),
        "threshold": float(best_thresh),
        "prediction": prediction,
        "confidence": round(final_confidence, 2)
    }

    save_temp_json()

    return {
        "prediction": prediction,
        "confidence": round(final_confidence, 2)
    }

# ==============================
# LEVEL 3: QUESTIONNAIRE PREDICTION
# ==============================
# ==============================
# LOAD QUESTIONNAIRE MODEL (LEVEL 3)
# ==============================
ques_model = CatBoostClassifier()
ques_model.load_model("models/catboost_autism_model.cbm")

# ==============================
# INPUT SCHEMA (LEVEL 3)
# ==============================
class QuesInput(BaseModel):
    responses: list
    age: float
    gender: str
    jaundice: str
    family_asd: str
    ethnicity: str
    who_completed: str

# ==============================
# LEVEL 3: QUESTIONNAIRE PREDICTION
# ==============================
@app.post("/predict-ques")
def predict_ques(data: QuesInput):

    print("\n===== QUESTIONNAIRE MODEL (CATBOOST) =====")

    # VALIDATION
    if len(data.responses) != 10:
        return {"error": "Expected 10 questionnaire responses"}
    
    # ------------------------------
    # INPUT VALIDATION (ADD HERE)
    # ------------------------------
    valid_sex = ["m", "f"]
    valid_binary = ["yes", "no"]

    if data.gender.lower() not in valid_sex:
        return {"error": "Invalid gender"}

    if data.jaundice.lower() not in valid_binary:
        return {"error": "Invalid jaundice value"}

    if data.family_asd.lower() not in valid_binary:
        return {"error": "Invalid family ASD value"}

    if not all(x in [0, 1] for x in data.responses):
        return {"error": "Responses must be binary (0/1)"}

    # SAFE BINARY
    ques_binary = [int(x) for x in data.responses]

    print("Binary Responses:", ques_binary)

    # BUILD INPUT
    input_dict = {
        "a1": ques_binary[0],
        "a2": ques_binary[1],
        "a3": ques_binary[2],
        "a4": ques_binary[3],
        "a5": ques_binary[4],
        "a6": ques_binary[5],
        "a7": ques_binary[6],
        "a8": ques_binary[7],
        "a9": ques_binary[8],
        "a10": ques_binary[9],
        "age_mons": data.age * 12,
        "sex": data.gender.lower(),
        "ethnicity": data.ethnicity.lower(),
        "jaundice": data.jaundice.lower(),
        "family_mem_with_asd": data.family_asd.lower(),
        "who_completed_the_test": data.who_completed.lower()
    }

    df_input = pd.DataFrame([input_dict])
    cat_cols = ["sex", "ethnicity", "jaundice", "family_mem_with_asd", "who_completed_the_test"]
    df_input[cat_cols] = df_input[cat_cols].astype("str")

    # NORMALIZE CATEGORIES
    df_input["who_completed_the_test"] = df_input["who_completed_the_test"].replace({
        "healthcare professional": "health care professional",
        "doctor": "health care professional",
        "parent": "family member",
        "caregiver": "family member"
    })

    df_input["ethnicity"] = df_input["ethnicity"].replace({
        "indian": "south asian",
        "asian indian": "south asian"
    })

    print("\nInput DataFrame:")
    print(df_input)

    # SAFE PREDICTION
    try:
        pred = int(ques_model.predict(df_input)[0])
        probs = ques_model.predict_proba(df_input)[0]
    except Exception as e:
        print("Prediction Error:", e)
        return {"error": "Model prediction failed"}

    autism_prob = probs[1]
    non_autism_prob = probs[0]

    final_conf = autism_prob if pred == 1 else non_autism_prob
    label = "Autistic" if pred == 1 else "Non-Autistic"

    total_traits = sum(ques_binary)

    print("\n===== INTERPRETABLE SIGNALS =====")
    print("Total Traits:", total_traits, "/10")

    # SAVE RESULTS
    TEMP_RESULT["demographics"] = {
        "age": float(data.age),
        "gender": data.gender,
        "ethnicity": data.ethnicity,
        "jaundice": data.jaundice == "yes",
        "family_asd": data.family_asd == "yes",
        "who_completed": data.who_completed
    }

    TEMP_RESULT["level_3_questionnaire"] = {
        "total_traits": int(total_traits),
        "max_traits": 10,  
        "prediction": label,
        "autism_probability": float(autism_prob),
        "confidence": round(final_conf * 100, 2)
    }

    save_temp_json()

    print("\n===== FINAL DECISION =====")
    print("Prediction:", label)
    print("Confidence (%):", round(final_conf * 100, 2))
    print("================================\n")

    return {
        "prediction": label,
        "confidence": round(final_conf * 100, 2)
    }

@app.get("/generate-report")
def generate_report():
    try:
        report = generate_report_from_json()
        return {"report": report}
    except Exception as e:
        return {"error": str(e)}
    

@app.get("/download-report")
def download_report():
    try:

        # ✅ CHECK ALL LEVELS COMPLETED
        if not TEMP_RESULT["level_1_eye_tracking"]:
            return {"error": "Eye tracking not completed"}

        if not TEMP_RESULT["level_2_facial"]:
            return {"error": "Face analysis not completed"}

        if not TEMP_RESULT["level_3_questionnaire"]:
            return {"error": "Questionnaire not completed"}

        # ✅ NOW GENERATE REPORT
        report = generate_report_from_json()

        pdf_path = generate_pdf(report)

        return FileResponse(
            path=pdf_path,
            filename="Autism_Screening_Report.pdf",
            media_type='application/pdf'
        )

    except Exception as e:
        return {"error": str(e)}
    
def generate_visuals(data):

    prob = data["level_3_questionnaire"]["autism_probability"]
    traits = data["level_3_questionnaire"]["total_traits"]

    eye = 1 if data["level_1_eye_tracking"] else 0
    face = 1 if data["level_2_facial"] else 0
    behavior = 1

    return {
        "probability": create_probability_chart(prob),
        "traits": create_trait_radar(traits),
        "modalities": create_modality_chart(eye, face, behavior)
    }