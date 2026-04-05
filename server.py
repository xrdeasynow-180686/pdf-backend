from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import os
import uuid
import zipfile

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {"message": "PDF API Running"}


# ================= MERGE =================
@app.route("/merge", methods=["POST"])
def merge_pdfs():
    files = request.files.getlist("files")

    writer = PdfWriter()

    for file in files:
        path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
        file.save(path)

        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    output_path = os.path.join(OUTPUT_FOLDER, f"merged_{uuid.uuid4()}.pdf")

    with open(output_path, "wb") as f:
        writer.write(f)

    return send_file(output_path, as_attachment=True)


# ================= SPLIT (FIXED) =================
@app.route("/split", methods=["POST"])
def split_pdf():
    file = request.files["file"]

    input_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
    file.save(input_path)

    reader = PdfReader(input_path)

    page_paths = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        page_filename = f"page_{i}_{uuid.uuid4()}.pdf"
        page_path = os.path.join(OUTPUT_FOLDER, page_filename)

        with open(page_path, "wb") as f:
            writer.write(f)

        page_paths.append(page_filename)

    # ALSO CREATE ZIP
    zip_name = f"split_{uuid.uuid4()}.zip"
    zip_path = os.path.join(OUTPUT_FOLDER, zip_name)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for p in page_paths:
            zipf.write(os.path.join(OUTPUT_FOLDER, p), p)

    return jsonify({
        "pages": page_paths,
        "zip": zip_name
    })


# ================= DOWNLOAD =================
@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)