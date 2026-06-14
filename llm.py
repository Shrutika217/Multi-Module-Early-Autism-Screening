import json
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# ==============================
# LOAD ENV VARIABLES
# ==============================
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found")

genai.configure(api_key=api_key)

# ==============================
# LOAD MODEL
# ==============================
model = genai.GenerativeModel("gemini-2.5-flash")


# ==============================
# CLEAN INPUT DATA (VERY IMPORTANT)
# ==============================
def clean_data(data):

    demo = data.get("demographics", {})

    return {
        "age": demo.get("age"),
        "gender": demo.get("gender"),
        "jaundice": demo.get("jaundice"),
        "family_asd": demo.get("family_asd"),
        "ethnicity": demo.get("ethnicity", "Not specified"),
        "who_completed": demo.get("who_completed", "Not specified"),

        "eye_tracking": {
            "prediction": data["level_1_eye_tracking"]["prediction"],
            "confidence": data["level_1_eye_tracking"]["confidence"]
        },

        "facial": {
            "prediction": data["level_2_facial"]["prediction"],
            "autism_probability": data["level_2_facial"]["autism_probability"],
            "confidence": data["level_2_facial"]["confidence"]
        },

        "questionnaire": {
            "traits": data["level_3_questionnaire"]["total_traits"],
            "max_traits": data["level_3_questionnaire"]["max_traits"],
            "prediction": data["level_3_questionnaire"]["prediction"],
            "probability": data["level_3_questionnaire"]["autism_probability"],
            "confidence": data["level_3_questionnaire"]["confidence"]
        }
    }

# ==============================
# SAFE GENERATION (RETRY + CONTINUE)
# ==============================
def safe_generate(prompt, retries=3):

    full_text = ""

    for attempt in range(retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.85,
                    "max_output_tokens": 4000   # increased
                }
            )

            if hasattr(response, "text") and response.text:
                full_text = response.text

            elif response.candidates:
                full_text = response.candidates[0].content.parts[0].text

            # ✅ CHECK COMPLETION
            if "DISCLAIMER" in full_text:
                return full_text

            # 🔁 CONTINUE IF TRUNCATED
            prompt = prompt + "\nContinue the report from where you stopped."

        except Exception:
            time.sleep(2)

    return full_text if full_text else "Error: Unable to generate report."


# ==============================
# MAIN FUNCTION
# ==============================
def generate_report_from_json(json_path="temp/temp_result.json"):

    if not os.path.exists(json_path):
        return "Error: temp_result.json not found."

    with open(json_path, "r") as f:
        data = json.load(f)

    # ✅ CLEAN DATA (CRITICAL FIX)
    cleaned_data = clean_data(data)

    # ✅ BUILD PROMPT (UNCHANGED)
    prompt = build_prompt(cleaned_data)

    # ✅ SAFE GENERATION
    report = safe_generate(prompt)

    return report


# ==============================
# PROMPT BUILDER (UNCHANGED)
# ==============================
def build_prompt(data):

    return f"""
You are a clinical AI report generator.

Your task is to generate a COMPLETE autism screening report.

----------------------------------
CRITICAL COMPLETION RULE
----------------------------------
You MUST generate ALL sections listed below.
You are NOT allowed to stop early.
You MUST continue writing until ALL sections are completed.

If output is incomplete, it is considered FAILURE.

----------------------------------
DATA RULES
----------------------------------
- Do NOT change numbers
- Confidence values are already in percentage. Do NOT rescale them
- Show confidence in percentage
- Do NOT invent data
- all clinical interpretation should be in common medical language
- Keep ALL clinical interpretations approximately equal in length (2–3 sentences each) and the same size

----------------------------------
OUTPUT FORMAT (STRICT)
----------------------------------

PATIENT INFORMATION
- Age
- Gender
- Ethnicity
- Jaundice history
- Family history of ASD
- Who completed the form

LEVEL 1: EYE-TRACKING ANALYSIS
- Key feature summary
- Model output
- Clinical interpretation

LEVEL 2: FACIAL ANALYSIS
- Model output
- Clinical interpretation

LEVEL 3: BEHAVIORAL QUESTIONNAIRE
- ASD Traits detected (list based on count)
- Model output
- Confidence (%)
- Clinical interpretation

FINAL SCREENING RESULT 

DISCLAIMER
"This is an AI-based screening tool and not a diagnostic system. Please visit a specialist for a comprehensive diagnostic assessment."

----------------------------------
IMPORTANT INSTRUCTIONS
----------------------------------
- Even if modalities contradict → you MUST explain
- If probability ~50% → interpret as "borderline / inconclusive"
- DO NOT stop midway
- Ensure FULL report is generated

----------------------------------
INPUT DATA
----------------------------------
{json.dumps(data, indent=2)}

----------------------------------
NOW GENERATE FULL REPORT
----------------------------------
"""
