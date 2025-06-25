import os
import json
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sklearn.cluster import KMeans
import torch
from shutil import copy2, rmtree
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import uvicorn

# CONFIG
INPUT_FOLDER = "sample_photos"
OUTPUT_FOLDER = "organized_photos"
NUM_CLUSTERS = 4
MODEL_NAME = "openai/clip-vit-base-patch32"
BLUR_THRESHOLD = 100.0  # lower = blurrier
TOP_PICKS_PERCENT = 0.1  # top 10% by sharpness

# Load model
print("Loading CLIP model...")
model = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)

app = FastAPI()

# Utility functions
def save_uploaded_files(files: List[UploadFile], save_dir: str):
    if os.path.exists(save_dir):
        rmtree(save_dir)
    os.makedirs(save_dir)
    for file in files:
        with open(os.path.join(save_dir, file.filename), "wb") as f:
            f.write(file.file.read())

def load_images(input_folder):
    files = [f for f in os.listdir(input_folder) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
    images = []
    paths = []
    for f in files:
        try:
            img = Image.open(os.path.join(input_folder, f)).convert("RGB")
            images.append(img)
            paths.append(f)
        except Exception as e:
            print(f"Skipping {f}: {e}")
    return images, paths

def blur_score(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance

@app.post("/organize")
async def organize_photos(files: List[UploadFile] = File(...)):
    try:
        print(f"Received {len(files)} files")
        save_uploaded_files(files, INPUT_FOLDER)
        print("Files saved.")

        images, filenames = load_images(INPUT_FOLDER)
        print(f"Loaded {len(images)} images.")

        non_blurry_images, non_blurry_filenames, non_blurry_scores = [], [], {}
        blurry_images, blurry_filenames = [], []

        for img, fname in zip(images, filenames):
            full_path = os.path.join(INPUT_FOLDER, fname)
            score = blur_score(full_path)
            print(f"{fname} blur score: {score:.2f}")
            if score < BLUR_THRESHOLD:
                blurry_images.append(img)
                blurry_filenames.append(fname)
            else:
                non_blurry_images.append(img)
                non_blurry_filenames.append(fname)
                non_blurry_scores[fname] = score

        if len(non_blurry_images) == 0:
            raise HTTPException(status_code=400, detail="No sharp images to process.")

        print("Generating embeddings...")
        inputs = processor(images=non_blurry_images, return_tensors="pt", padding=True)
        with torch.no_grad():
            embeddings = model.get_image_features(**inputs).cpu().numpy()

        print("Clustering...")
        num_clusters = min(NUM_CLUSTERS, len(non_blurry_images))
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        labels = kmeans.fit_predict(embeddings)

        if os.path.exists(OUTPUT_FOLDER):
            rmtree(OUTPUT_FOLDER)
        os.makedirs(OUTPUT_FOLDER)

        results = {}
        sorted_by_score = sorted(non_blurry_scores.items(), key=lambda x: x[1], reverse=True)
        top_n = max(1, int(len(sorted_by_score) * TOP_PICKS_PERCENT))
        top_picks = set([fname for fname, _ in sorted_by_score[:top_n]])
        top_picks_folder = os.path.join(OUTPUT_FOLDER, "Top_Picks")
        os.makedirs(top_picks_folder, exist_ok=True)
        results["Top_Picks"] = []

        for i, label in enumerate(labels):
            fname = non_blurry_filenames[i]
            cluster_folder = os.path.join(OUTPUT_FOLDER, f"cluster_{label}")
            os.makedirs(cluster_folder, exist_ok=True)
            src = os.path.join(INPUT_FOLDER, fname)
            dst = os.path.join(cluster_folder, fname)
            copy2(src, dst)
            results.setdefault(f"cluster_{label}", []).append(fname)

            if fname in top_picks:
                dst_top = os.path.join(top_picks_folder, fname)
                copy2(src, dst_top)
                results["Top_Picks"].append(fname)

        trash_folder = os.path.join(OUTPUT_FOLDER, "Trash")
        os.makedirs(trash_folder, exist_ok=True)
        for fname in blurry_filenames:
            src = os.path.join(INPUT_FOLDER, fname)
            dst = os.path.join(trash_folder, fname)
            copy2(src, dst)
        results["Trash"] = blurry_filenames

        return JSONResponse(content=results)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("photo_curator:app", host="0.0.0.0", port=8000, reload=True)


