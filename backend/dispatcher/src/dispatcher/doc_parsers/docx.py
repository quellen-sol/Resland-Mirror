import io

from docx import Document


def parse_docx(file_data: bytes) -> str:
    doc = Document(io.BytesIO(file_data))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])
