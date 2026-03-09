"""
resume_parser.py
----------------
Extracts and cleans text from resume files.
Supports: PDF, DOCX, and plain TXT formats.
"""

import re
import io
import pdfplumber
from docx import Document


def extract_text_from_pdf(file) -> str:
    """
    Extract text from a PDF file.
    Accepts a file path (str) or a file-like object (BytesIO).
    """
    text_pages = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)
    return "\n".join(text_pages)


def extract_text_from_docx(file) -> str:
    """
    Extract text from a DOCX file.
    Accepts a file path (str) or a file-like object (BytesIO).
    """
    doc = Document(file)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_txt(file) -> str:
    """
    Read plain text from a .txt file or file-like object.
    """
    if hasattr(file, "read"):
        content = file.read()
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="ignore")
        return content
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def clean_text(text: str) -> str:
    """
    Clean extracted resume text:
    - Remove excessive whitespace and blank lines
    - Strip hidden/special characters
    - Normalize line endings
    """
    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3+ consecutive newlines with two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove non-printable characters (except newline/tab)
    text = re.sub(r"[^\x20-\x7E\n\t]", "", text)
    return text.strip()


def parse_resume(file, filename: str = "") -> dict:
    """
    Main entry point. Detects file type and returns:
    {
        "raw_text": str,
        "clean_text": str,
        "char_count": int,
        "word_count": int,
        "file_type": str
    }
    """
    filename_lower = filename.lower() if filename else ""

    try:
        if filename_lower.endswith(".pdf"):
            raw = extract_text_from_pdf(file)
            file_type = "PDF"
        elif filename_lower.endswith(".docx"):
            raw = extract_text_from_docx(file)
            file_type = "DOCX"
        elif filename_lower.endswith(".txt"):
            raw = extract_text_from_txt(file)
            file_type = "TXT"
        else:
            # Try PDF first, fall back to plain text
            try:
                raw = extract_text_from_pdf(file)
                file_type = "PDF (auto-detected)"
            except Exception:
                raw = extract_text_from_txt(file)
                file_type = "TXT (fallback)"

        cleaned = clean_text(raw)
        return {
            "raw_text": raw,
            "clean_text": cleaned,
            "char_count": len(cleaned),
            "word_count": len(cleaned.split()),
            "file_type": file_type,
        }

    except Exception as e:
        return {
            "raw_text": "",
            "clean_text": "",
            "char_count": 0,
            "word_count": 0,
            "file_type": "unknown",
            "error": str(e),
        }