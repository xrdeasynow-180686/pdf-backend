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
    return {"message": "PDF Merge-Split API Running 🚀"}


# ================= MERGE =================
@app.route("/merge", methods=["POST"])
def merge_pdfs():
    try:
        files = request.files.getlist("files")

        if len(files) < 2:
            return {"error": "Upload at least 2 PDFs"}, 400

        writer = PdfWriter()

        for file in files:
            temp_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
            file.save(temp_path)

            reader = PdfReader(temp_path)
            for page in reader.pages:
                writer.add_page(page)

        output_path = os.path.join(
            OUTPUT_FOLDER, f"merged_{uuid.uuid4()}.pdf"
        )

        with open(output_path, "wb") as f:
            writer.write(f)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500


# ================= SPLIT (ZIP OUTPUT) =================
@app.route("/split", methods=["POST"])
def split_pdf():
    try:
        file = request.files["file"]

        temp_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
        file.save(temp_path)

        reader = PdfReader(temp_path)

        zip_path = os.path.join(
            OUTPUT_FOLDER, f"split_{uuid.uuid4()}.zip"
        )

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)

                pdf_path = os.path.join(
                    OUTPUT_FOLDER, f"page_{i}.pdf"
                )

                with open(pdf_path, "wb") as f:
                    writer.write(f)

                zipf.write(pdf_path, f"page_{i}.pdf")

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500


# ================= AI SUMMARY =================
@app.route("/summary", methods=["POST"])
def summary():
    try:
        file = request.files["file"]

        reader = PdfReader(file)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        text = text[:3000]

        sentences = text.split(".")
        points = []

        for s in sentences:
            if len(s.strip()) > 40:
                points.append("• " + s.strip())

        return jsonify({"summary": "\n".join(points[:8])})

    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)