import os
import logging
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

# Configure logging
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger("upload-service")

app = Flask(__name__)
CORS(app)

SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS", "/etc/secrets/service-account.json"
)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

FOLDER_ID = os.getenv("FOLDER_ID")
if not FOLDER_ID:
    raise RuntimeError("FOLDER_ID environment variable is required")

# Initialize Drive client
logger.info("Loading service account credentials from %s", SERVICE_ACCOUNT_FILE)
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)


@app.route("/", methods=["GET"])
def home():
    # serve index.html from project root (no templates folder needed)
    return send_from_directory(".", "index.html")


@app.route("/upload", methods=["POST"])
def upload():
    # Basic checks
    if "file" not in request.files:
        logger.warning("Upload attempt with no file")
        return jsonify({"success": False, "error": "No file provided"}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        logger.warning("Upload attempt with empty filename")
        return jsonify({"success": False, "error": "Empty filename"}), 400

    # Log some info (size may be None for streamed uploads)
    try:
        content_length = request.content_length
    except Exception:
        content_length = None

    logger.info("Uploading file: %s (mimetype=%s, content_length=%s)",
                uploaded_file.filename, uploaded_file.mimetype, content_length)

    file_metadata = {"name": uploaded_file.filename, "parents": [FOLDER_ID]}

    # Use MediaIoBaseUpload to stream the upload
    media = MediaIoBaseUpload(uploaded_file.stream, mimetype=uploaded_file.mimetype, resumable=False)

    try:
        created = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id, name, webViewLink"
        ).execute()

        logger.info("Upload success: %s (id=%s)", created.get("name"), created.get("id"))
        return jsonify({"success": True, "file": created})
    except HttpError as he:
        # HttpError provides detailed content
        content = None
        try:
            content = he.content.decode() if isinstance(he.content, (bytes, bytearray)) else str(he.content)
        except Exception:
            content = str(he)
        logger.error("Google API error uploading file: %s", content)
        resp = {"success": False, "error": "Google API error", "google_error": content}
        if DEBUG:
            resp["traceback"] = traceback.format_exc()
        return jsonify(resp), 500
    except Exception as e:
        logger.exception("Unexpected error uploading file")
        resp = {"success": False, "error": str(e)}
        if DEBUG:
            resp["traceback"] = traceback.format_exc()
        return jsonify(resp), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("Starting app on port %s (DEBUG=%s)", port, DEBUG)
    app.run(host="0.0.0.0", port=port)
