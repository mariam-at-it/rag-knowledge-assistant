"""
Step 1 of the pipeline: read files and turn them into plain-text *sections*.

Why sections and not just one big string? Because the client wants every answer
to cite "the exact document and section". So while reading we remember where
each piece of text came from:
  - PDF  -> one section per page        (location = "page 3")
  - DOCX -> one section per heading     (location = "Connecting to the VPN")
  - TXT  -> one section per "# heading" line, or the whole file if there are none
"""

from dataclasses import dataclass
from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@dataclass
class Section:
    text: str      # the content
    source: str    # file name, e.g. "employee_handbook.pdf"
    location: str  # human-readable place inside the file, e.g. "page 2"


def load_pdf(path: Path) -> list[Section]:
    reader = PdfReader(str(path))
    sections = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:  # skip empty pages (e.g. scanned images without text)
            sections.append(Section(text, path.name, f"page {page_number}"))
    return sections


def load_docx(path: Path) -> list[Section]:
    doc = Document(str(path))
    sections = []
    heading = "Introduction"  # text before the first heading goes here
    lines: list[str] = []

    def flush():
        if lines:
            sections.append(Section("\n".join(lines), path.name, heading))

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style = paragraph.style.name if paragraph.style is not None else ""
        if style == "Title":
            continue  # the document title is not useful content
        if style.startswith("Heading"):
            flush()  # a new heading closes the previous section
            heading, lines = text, [text]  # keep the heading inside the text, it helps search
        else:
            lines.append(text)
    flush()
    return sections


def load_txt(path: Path) -> list[Section]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    sections = []
    heading = "Introduction"
    lines: list[str] = []

    def flush():
        body = "\n".join(lines).strip()
        if body:
            sections.append(Section(body, path.name, heading))

    for line in text.splitlines():
        if line.startswith("#"):  # Markdown-style heading: "# 2. Travel Booking"
            flush()
            heading = line.lstrip("#").strip()
            lines = [heading]
        else:
            lines.append(line)
    flush()
    return sections


def load_document(path: Path) -> list[Section]:
    """Pick the right loader based on the file extension."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return load_pdf(path)
    if ext == ".docx":
        return load_docx(path)
    if ext in (".txt", ".md"):
        return load_txt(path)
    raise ValueError(f"Unsupported file type: {path.name}")
