from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter
import uuid
import os

OUTPUT_FOLDER = "outputs"

def merge_pdfs(file_paths):
    writer = PdfWriter()

    for path in file_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    output = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}.pdf")

    with open(output, "wb") as f:
        writer.write(f)

    return output


def pdf_to_word(file_path):
    output = os.path.join(OUTPUT_FOLDER, f"{uuid.uuid4()}.docx")

    cv = Converter(file_path)
    cv.convert(output)
    cv.close()

    return output