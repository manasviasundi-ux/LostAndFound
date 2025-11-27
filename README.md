# LostAndFound

Run locally:
1. python -m venv venv
2. source venv/bin/activate    # Windows: venv\Scripts\activate
3. pip install -r requirements.txt
4. gunicorn app:app --bind 127.0.0.1:5000
# or for dev:
# python app.py
