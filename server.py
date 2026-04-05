from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfReader, PdfWriter
import os
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return {"message": "PDF API Running"}


# ✅ MERGE PDF
@app.route("/merge", methods=["POST"])
def merge_pdfs():
    files = request.files.getlist("files")

    if len(files) < 2:
        return {"error": "Need at least 2 PDFs"}, 400

    writer = PdfWriter()

    for file in files:
        path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".pdf")
        file.save(path)

        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    output_file = os.path.join(
        OUTPUT_FOLDER,
        f"merged_{uuid.uuid4()}.pdf"
    )

    with open(output_file, "wb") as f:
        writer.write(f)

    return send_file(output_file, as_attachment=True)


# ✅ AI SUMMARY
@app.route("/summary", methods=["POST"])
def summary():
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

    result = "\n".join(points[:8])

    return jsonify({
        "summary": result
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)