from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import uuid
import zipfile

# ✅ IMPORTANT: use ONLY these
from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {"message": "PDF API Running"}


# ================= MERGE (NO PdfMerger ❌) =================
@app.route("/merge", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")

    writer = PdfWriter()

    for f in files:
        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
        f.save(path)

        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    output_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}.pdf")

    with open(output_path, "wb") as f:
        writer.write(f)

    return {"file": os.path.basename(output_path)}


# ================= SPLIT =================
@app.route("/split", methods=["POST"])
def split_pdf():
    file = request.files["file"]

    input_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
    file.save(input_path)

    reader = PdfReader(input_path)

    output_files = []
    zip_name = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}.zip")

    with zipfile.ZipFile(zip_name, "w") as zipf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)

            out_name = f"page_{i+1}_{uuid.uuid4()}.pdf"
            out_path = os.path.join(OUTPUT_FOLDER, out_name)

            with open(out_path, "wb") as f:
                writer.write(f)

            zipf.write(out_path, out_name)
            output_files.append(out_name)

    return {
        "pages": output_files,
        "zip": os.path.basename(zip_name)
    }


# ================= PDF TO WORD (FIXED) =================
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files["file"]

    input_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
    output_path = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}.docx")

    file.save(input_path)

    cv = Converter(input_path)
    cv.convert(output_path, start=0, end=None)  # ✅ important fix
    cv.close()

    return {"file": os.path.basename(output_path)}


# ================= IMAGE TO PDF =================
@app.route("/image-to-pdf", methods=["POST"])
def image_to_pdf():
    file = request.files["file"]

    filename = f"{uuid.uuid4()}.pdf"
    path = os.path.join(OUTPUT_FOLDER, filename)

    img = Image.open(file)
    img.convert("RGB").save(path)

    return {"file": filename}


# ================= COMPRESS =================
@app.route("/compress", methods=["POST"])
def compress_pdf():
    file = request.files["file"]

    filename = f"{uuid.uuid4()}.pdf"
    path = os.path.join(OUTPUT_FOLDER, filename)

    # simple compression (safe)
    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open(path, "wb") as f:
        writer.write(f)

    return {"file": filename}


# ================= DOWNLOAD =================
@app.route("/download/<filename>")
def download_file(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)

    return send_file(
        path,
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)