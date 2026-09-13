import io

from docx import Document


def parse_docx(file_data: bytes):
    return Document(io.BytesIO(file_data))
