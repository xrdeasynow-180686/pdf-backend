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
from pypdf import PdfMerger

@app.route("/merge", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")

    merger = PdfMerger()

    for f in files:
        path = f"uploads/{uuid.uuid4()}.pdf"
        f.save(path)
        merger.append(path)

    output = f"outputs/{uuid.uuid4()}.pdf"
    merger.write(output)
    merger.close()

    return {"file": os.path.basename(output)}

# ================= SPLIT (FIXED) =================
from pypdf import PdfReader, PdfWriter
import zipfile

@app.route("/split", methods=["POST"])
def split_pdf():
    file = request.files["file"]

    input_path = f"uploads/{uuid.uuid4()}.pdf"
    file.save(input_path)

    reader = PdfReader(input_path)

    output_files = []
    zip_name = f"outputs/{uuid.uuid4()}.zip"

    with zipfile.ZipFile(zip_name, "w") as zipf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)

            out_path = f"outputs/page_{i+1}_{uuid.uuid4()}.pdf"
            with open(out_path, "wb") as f:
                writer.write(f)

            zipf.write(out_path, os.path.basename(out_path))
            output_files.append(os.path.basename(out_path))

    return {
        "pages": output_files,
        "zip": os.path.basename(zip_name)
    }
# ================= PDF TO WORD =================
from pdf2docx import Converter
import uuid

@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files["file"]

    input_path = f"uploads/{uuid.uuid4()}.pdf"
    output_path = f"outputs/{uuid.uuid4()}.docx"

    file.save(input_path)

    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()

    return {"file": os.path.basename(output_path)}

# ================= IMAGE TO PDF =================
@app.route("/image-to-pdf", methods=["POST"])
def image_to_pdf():
    file = request.files["file"]

    filename = f"{uuid.uuid4()}.pdf"
    path = os.path.join(OUTPUT_FOLDER, filename)

    from PIL import Image

    img = Image.open(file)
    img.convert("RGB").save(path)

    return jsonify({"file": filename})


# ================= COMPRESS =================
@app.route("/compress", methods=["POST"])
def compress_pdf():
    file = request.files["file"]

    filename = f"{uuid.uuid4()}.pdf"
    path = os.path.join(OUTPUT_FOLDER, filename)

    # basic compression copy (can improve later)
    with open(path, "wb") as f:
        f.write(file.read())

    return jsonify({"file": filename})

# ================= DOWNLOAD =================
from flask import send_file
import os

@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join("outputs", filename)

    return send_file(
        path,
        as_attachment=True,
        download_name=filename
    )