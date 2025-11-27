import json
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple

import cv2
import numpy as np
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_from_directory,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(BASE_DIR, "data.json")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB cap

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_items() -> list:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_items(items: list) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def compute_histogram(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to load image for histogram computation.")

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv_image], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten().astype(np.float32)


def build_text_signature(
    item: Optional[dict] = None,
    *,
    item_type: str = "",
    item_name: str = "",
    color: str = "",
    location: str = "",
) -> str:
    if item:
        parts = [
            item.get("item_type", ""),
            item.get("item_name", ""),
            item.get("color", ""),
            item.get("location", ""),
        ]
    else:
        parts = [item_type, item_name, color, location]

    return " ".join(part.strip().lower() for part in parts if part)


def find_top_matches(
    new_hist: np.ndarray,
    items: list,
    target_type: str | None = None,
    top_n: int = 3,
    new_signature: str = "",
    combine_ratio: Tuple[float, float] = (0.75, 0.25),
) -> list:
    filtered_items = []
    histograms = []
    signatures = []

    for item in items:
        if target_type and item.get("item_type") != target_type:
            continue

        hist_list = item.get("histogram")
        if not hist_list:
            continue

        filtered_items.append(item)
        histograms.append(np.array(hist_list, dtype=np.float32))
        signatures.append(build_text_signature(item))

    text_scores = np.zeros(len(filtered_items), dtype=np.float32)
    if signatures and new_signature:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([new_signature] + signatures)
        text_scores = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:]).flatten().astype(np.float32)

    weight_img, weight_txt = combine_ratio
    candidates = []

    for idx, item in enumerate(filtered_items):
        hist_score = float(
            cosine_similarity(
                new_hist.reshape(1, -1),
                histograms[idx].reshape(1, -1),
            )[0][0]
        )
        text_score = float(text_scores[idx]) if text_scores.size else 0.0

        combined = (weight_img * hist_score) + (weight_txt * text_score)
        combined = max(0.0, min(combined, 1.0))

        candidates.append(
            {
                "item_name": item.get("item_name"),
                "item_type": item.get("item_type"),
                "color": item.get("color"),
                "location": item.get("location"),
                "filename": item.get("filename"),
                "date": item.get("date"),
                "similarity": combined,
                "image_similarity": max(0.0, min(hist_score, 1.0)),
                "text_similarity": max(0.0, min(text_score, 1.0)),
            }
        )

    candidates.sort(key=lambda entry: entry["similarity"], reverse=True)
    return candidates[:top_n]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "itemImage" not in request.files:
        return jsonify({"error": "Image file is required."}), 400

    file = request.files["itemImage"]
    if file.filename == "":
        return jsonify({"error": "Please choose an image file."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type."}), 400

    item_type = request.form.get("itemType")
    item_name = request.form.get("itemName")
    color = request.form.get("itemColor")
    location = request.form.get("itemLocation")

    if not all([item_type, item_name, color, location]):
        return jsonify({"error": "All fields are required."}), 400

    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)

    try:
        new_hist = compute_histogram(save_path)
    except ValueError as exc:
        os.remove(save_path)
        return jsonify({"error": str(exc)}), 400

    new_item = {
        "id": uuid.uuid4().hex,
        "item_type": item_type,
        "item_name": item_name,
        "color": color,
        "location": location,
        "filename": unique_name,
        "date": datetime.utcnow().isoformat(),
        "histogram": new_hist.tolist(),
    }

    existing_items = load_items()
    target_type = "found" if item_type == "lost" else "lost"
    signature = build_text_signature(
        item_type=item_type,
        item_name=item_name,
        color=color,
        location=location,
    )
    matches = find_top_matches(
        new_hist,
        existing_items,
        target_type=target_type,
        new_signature=signature,
    )

    existing_items.append(new_item)
    save_items(existing_items)

    return jsonify(
        {
            "message": "Item stored successfully.",
            "matches": matches,
        }
    )


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)


