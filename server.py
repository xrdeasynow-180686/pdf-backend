from flask import Flask, request, send_file
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import os, uuid, zipfile

app = Flask(__name__)
CORS(app)

UPLOAD = "uploads"
OUTPUT = "output"

os.makedirs(UPLOAD, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)


@app.route("/")
def home():
    return {"status": "running"}


# ================= MERGE =================
@app.route("/merge", methods=["POST"])
def merge():
    files = request.files.getlist("files")

    writer = PdfWriter()

    for f in files:
        path = os.path.join(UPLOAD, f"{uuid.uuid4()}.pdf")
        f.save(path)

        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    out = os.path.join(OUTPUT, f"merge_{uuid.uuid4()}.pdf")

    with open(out, "wb") as f:
        writer.write(f)

    return send_file(out, as_attachment=True)


# ================= SPLIT =================
@app.route("/split", methods=["POST"])
def split():
    file = request.files["file"]

    path = os.path.join(UPLOAD, f"{uuid.uuid4()}.pdf")
    file.save(path)

    reader = PdfReader(path)

    zip_path = os.path.join(OUTPUT, f"split_{uuid.uuid4()}.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)

            temp = os.path.join(OUTPUT, f"{i}.pdf")
            with open(temp, "wb") as f:
                writer.write(f)

            zipf.write(temp, f"page_{i}.pdf")

    return send_file(zip_path, as_attachment=True)


# ================= EDIT (TEXT + HIGHLIGHT DATA) =================
@app.route("/edit", methods=["POST"])
def edit():
    file = request.files["file"]
    highlight = request.form.get("highlight", "")

    path = os.path.join(UPLOAD, f"{uuid.uuid4()}.pdf")
    file.save(path)

    reader = PdfReader(path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    out = os.path.join(OUTPUT, f"edit_{uuid.uuid4()}.pdf")

    with open(out, "wb") as f:
        writer.write(f)

    return send_file(out, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)