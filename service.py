from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import os

app = Flask(__name__)

# Load service account credentials
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)

# 👇 Replace with your shared folder ID
FOLDER_ID = "YOUR_SHARED_FOLDER_ID_HERE"


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    uploaded_file = request.files["file"]

    file_metadata = {
        "name": uploaded_file.filename,
        "parents": [FOLDER_ID]
    }

    media = MediaIoBaseUpload(uploaded_file.stream, mimetype=uploaded_file.mimetype, resumable=True)

    try:
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()

        return jsonify({"success": True, "file": file})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "✅ File upload service is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
