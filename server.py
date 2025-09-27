import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = Flask(__name__)
CORS(app)

# Service account credentials
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/etc/secrets/service-account.json")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

FOLDER_ID = os.getenv("FOLDER_ID")
if not FOLDER_ID:
    raise RuntimeError("FOLDER_ID environment variable is required")

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)

# Serve index.html from root directory
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# Upload endpoint
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    uploaded_file = request.files["file"]
    filename = uploaded_file.filename

    file_metadata = {"name": filename, "parents": [FOLDER_ID]}
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
