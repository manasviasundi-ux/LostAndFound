## Digital Lost & Found

Hackathon-ready Flask app for cataloging lost and found items with image-based matching. Uses OpenCV color histograms plus text similarity for quick triage between reported “lost” and “found” entries.

### Requirements
- Python 3.10+
- pip / virtualenv
- Dependencies: `Flask`, `opencv-python-headless`, `numpy`, `scikit-learn`

### Setup & Run
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt  # or pip install flask opencv-python-headless numpy scikit-learn
python app.py
```
Visit `http://127.0.0.1:5000/` to use the main interface.

### QR-Based Quick Upload
Finders can scan a QR code placed in common areas to open a streamlined form at `/quick-upload`.

1. Generate a link that encodes the location: `https://your-host/quick-upload?location=Library%20Lobby`.
2. Create a QR poster for that URL. Example using the `qrcode` package:
   ```bash
   pip install qrcode[pil]
   python - <<'PY'
   import qrcode
   url = "https://your-host/quick-upload?location=Library%20Lobby"
   qrcode.make(url).save("library-lobby-qr.png")
   PY
   ```
3. Print and post the QR near the collection point.
4. When scanned, the quick-upload page auto-selects “Found Item,” prefills the location, and lets the finder snap a photo and submit in seconds.

### Data Storage
- Uploaded photos live in `uploads/`.
- Item metadata and histogram features are appended to `data.json`.

### Matching Logic
- HSV histograms (8×8×8 bins) + TF-IDF of type/name/color/location.
- Similarity score = `0.75 * image + 0.25 * text`, returned with each match.

### Next Ideas
- Add email/SMS alerts when a high-percentage match arrives.
- Build an admin dashboard to moderate entries.
- Swap in deeper image descriptors (ORB/SIFT or CLIP) for better accuracy.

