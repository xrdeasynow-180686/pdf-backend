from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import os, uuid, zipfile

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {"status": "PDF PRO API running"}


# ================= MERGE =================
@app.route("/merge", methods=["POST"])
def merge():
    try:
        files = request.files.getlist("files")
        order = request.form.get("order")

        writer = PdfWriter()
        temp_paths = []

        for f in files:
            path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
            f.save(path)
            temp_paths.append(path)

        # ignore order for simplicity (frontend controls order)
        for path in temp_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

        out = os.path.join(OUTPUT_FOLDER, f"merged_{uuid.uuid4()}.pdf")

        with open(out, "wb") as fp:
            writer.write(fp)

        return send_file(out, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500


# ================= SPLIT =================
@app.route("/split", methods=["POST"])
def split():
    try:
        file = request.files["file"]

        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
        file.save(path)

        reader = PdfReader(path)

        zip_path = os.path.join(OUTPUT_FOLDER, f"split_{uuid.uuid4()}.zip")

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)

                temp_pdf = os.path.join(OUTPUT_FOLDER, f"p_{i}.pdf")

                with open(temp_pdf, "wb") as f:
                    writer.write(f)

                zipf.write(temp_pdf, f"page_{i}.pdf")

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500


# ================= PDF EDITOR =================
@app.route("/edit", methods=["POST"])
def edit():
    try:
        file = request.files["file"]
        text = request.form.get("text", "")

        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
        file.save(path)

        reader = PdfReader(path)
        writer = PdfWriter()

        for page in reader.pages:
            page.merge_text(text) if hasattr(page, "merge_text") else None
            writer.add_page(page)

        out = os.path.join(OUTPUT_FOLDER, f"edited_{uuid.uuid4()}.pdf")

        with open(out, "wb") as f:
            writer.write(f)

        return send_file(out, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)