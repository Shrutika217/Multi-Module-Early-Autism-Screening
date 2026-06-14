import gdown
import os

MODELS = {
    "catboost_autism_model.cbm":
        "https://drive.google.com/file/d/1ksgtpas31U8CTB2bGN4_Kb9DsEw1IrOe/view?usp=drive_link",

    "resnet_face_model.pth":
        "https://drive.google.com/file/d/1ulXgkHXHSQmMbwsltJkO22ZTgg9ETtfZ/view?usp=drive_link",

    "rf_eye_model.pkl":
        "https://drive.google.com/file/d/14Ab4rbrxpqITOE9flL1hB59YgtqRM5Ak/view?usp=drive_link",

    "scaler_eye.pkl":
        "https://drive.google.com/file/d/1UZfV9zat399cjdOba3pozRE-tflfSsB9/view?usp=drive_link"
}


def download_models():

    os.makedirs("models", exist_ok=True)

    for filename, url in MODELS.items():

        path = f"models/{filename}"

        if not os.path.exists(path):
            print(f"Downloading {filename}...")
            gdown.download(url, path, quiet=False)

        else:
            print(f"{filename} already exists")
