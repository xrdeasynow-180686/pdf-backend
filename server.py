from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from upstash_redis import Redis
from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter
import uuid
import os
import threading

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- UPSTASH REDIS ----------------
redis = Redis(
    url="https://amazed-woodcock-68349.upstash.io",
    token="gQAAAAAAAQr9AAIncDE3NjkzMDM0ZmM5Mzk0MGJiYWVlZGQ1MGRjYTg0ZTMxZnAxNjgzNDk"
)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return {"status": "PDF backend running (Upstash)"}

# ---------------- BACKGROUND WORKER ----------------
def process_pdf(job_id, job_type, file_paths):
    try:
        redis.set(job_id, "processing")

        if job_type == "merge":
            writer = PdfWriter()

            for path in file_paths:
                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)

            output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.pdf")

            with open(output_path, "wb") as f:
                writer.write(f)

            redis.set(job_id, output_path)

        elif job_type == "word":
            input_path = file_paths[0]
            output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.docx")

            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()

            redis.set(job_id, output_path)

    except Exception as e:
        redis.set(job_id, f"error:{str(e)}")


# ---------------- MERGE PDF ----------------
@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("files")

    file_paths = []
    for f in files:
        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
        f.save(path)
        file_paths.append(path)

    job_id = str(uuid.uuid4())

    redis.set(job_id, "queued")

    threading.Thread(
        target=process_pdf,
        args=(job_id, "merge", file_paths)
    ).start()

    return jsonify({"job_id": job_id, "status": "queued"})


# ---------------- PDF TO WORD ----------------
@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    file = request.files["file"]

    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.pdf")
    file.save(path)

    job_id = str(uuid.uuid4())

    redis.set(job_id, "queued")

    threading.Thread(
        target=process_pdf,
        args=(job_id, "word", [path])
    ).start()

    return jsonify({"job_id": job_id, "status": "queued"})


# ---------------- JOB STATUS ----------------
@app.route("/status/<job_id>")
def status(job_id):
    result = redis.get(job_id)

    if not result:
        return jsonify({"status": "not_found"})

    if isinstance(result, bytes):
        result = result.decode()

    if result.startswith("error:"):
        return jsonify({"status": "error", "message": result})

    if result in ["queued", "processing"]:
        return jsonify({"status": result})

    return jsonify({"status": "done", "file": result})


# ---------------- DOWNLOAD FILE ----------------
@app.route("/download/<job_id>")
def download(job_id):
    result = redis.get(job_id)

    if isinstance(result, bytes):
        result = result.decode()

    return send_file(result, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)