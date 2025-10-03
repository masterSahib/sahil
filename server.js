import express from "express";
import multer from "multer";
import { google } from "googleapis";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

// Setup
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const upload = multer({ dest: "uploads/" });
app.use(express.static("public"));

// Google Drive Setup
const KEYFILE = "service_account.json"; // your service account key file
const SCOPES = ["https://www.googleapis.com/auth/drive"];
const auth = new google.auth.GoogleAuth({
  keyFile: KEYFILE,
  scopes: SCOPES,
});
const drive = google.drive({ version: "v3", auth });

// Your shared Google Drive folder ID
const FOLDER_ID = "YOUR_FOLDER_ID_HERE";

// Upload endpoint
app.post("/upload", upload.single("file"), async (req, res) => {
  try {
    const fileMetadata = {
      name: req.file.originalname,
      parents: [FOLDER_ID],
    };
    const media = {
      mimeType: req.file.mimetype,
      body: fs.createReadStream(req.file.path),
    };

    const file = await drive.files.create({
      resource: fileMetadata,
      media: media,
      fields: "id, name, webViewLink",
    });

    fs.unlinkSync(req.file.path); // remove temp file
    res.json({ success: true, file: file.data });
  } catch (err) {
    console.error("Upload error:", err);
    res.status(500).send("Upload failed");
  }
});

// List files endpoint
app.get("/files", async (req, res) => {
  try {
    const response = await drive.files.list({
      q: `'${FOLDER_ID}' in parents`,
      fields: "files(id, name, webViewLink, createdTime)",
    });
    res.json(response.data.files);
  } catch (err) {
    console.error("List error:", err);
    res.status(500).send("Error listing files");
  }
});

// Run server
app.listen(3000, () => console.log("🚀 Server running at http://localhost:3000"));
