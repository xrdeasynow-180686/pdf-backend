from flask import Flask, request, send_file
from flask_cors import CORS
from pypdf import PdfMerger
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
    return {"message": "PDF Merge API is running"}

@app.route("/merge", methods=["POST"])
def merge_pdfs():
    files = request.files.getlist("files")

    if len(files) < 2:
        return {"error": "Need at least 2 PDFs"}, 400

    merger = PdfMerger()

    saved_files = []

    for file in files:
        filename = str(uuid.uuid4()) + ".pdf"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        saved_files.append(path)
        merger.append(path)

    output_file = os.path.join(
        OUTPUT_FOLDER,
        f"merged_{uuid.uuid4()}.pdf"
    )

    merger.write(output_file)
    merger.close()

    return send_file(output_file, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)