import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = Flask(__name__)
CORS(app)  # allow cross-origin from your frontend

# Optional: limit max upload size (bytes). Set via env var MAX_UPLOAD_BYTES
max_bytes = os.getenv("MAX_UPLOAD_BYTES")
if max_bytes:
    app.config["MAX_CONTENT_LENGTH"] = int(max_bytes)

# Service account credentials path (Render secret file path)
SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS", "/etc/secrets/service-account.json"
)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Drive folder id (must be shared with the service account)
FOLDER_ID = os.getenv("FOLDER_ID")
if not FOLDER_ID:
    raise RuntimeError("FOLDER_ID environment variable is required")

# Create credentials and Drive client
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)

@app.route("/")
def home():
    return "✅ File upload service is running"

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    uploaded_file = request.files["file"]
    filename = uploaded_file.filename

    file_metadata = {"name": filename, "parents": [FOLDER_ID]}
    # Use MediaIoBaseUpload with resumable=False for quick/simple uploads
    media = MediaIoBaseUpload(uploaded_file.stream, mimetype=uploaded_file.mimetype, resumable=False)

    try:
        created = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id, name, webViewLink"
        ).execute()
        return jsonify({"success": True, "file": created})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
