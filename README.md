1R# LostAndFound

Short description: A Flask app for registering lost and found items on campus.

## Run locally
1. Create a virtualenv:
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
2. Install dependencies:
   pip install -r requirements.txt
3. Start the server:
   gunicorn app:app --bind 127.0.0.1:5000
   # or for development:
   python app.py

