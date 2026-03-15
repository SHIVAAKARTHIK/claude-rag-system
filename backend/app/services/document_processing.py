import re
from pathlib import Path


class DocumentProcessingService:
    CHUNK_SIZE = 500       # target words per chunk
    CHUNK_OVERLAP = 50     # words of overlap between chunks

    def process_file(self, file_path: str, filename: str) -> list[dict]:
        """Parse a document and return a list of text chunks with metadata."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            text_pages = self._parse_pdf(path)
        elif ext in (".docx",):
            text_pages = self._parse_docx(path)
        elif ext in (".txt", ".md"):
            text_pages = self._parse_plain(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        chunks = []
        for page_num, page_text in text_pages:
            page_chunks = self._chunk_text(page_text, filename, page_num)
            chunks.extend(page_chunks)

        return chunks

    def _parse_pdf(self, path: Path) -> list[tuple[int, str]]:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((i, text))
        return pages

    def _parse_docx(self, path: Path) -> list[tuple[int, str]]:
        from docx import Document
        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [(1, text)]

    def _parse_plain(self, path: Path) -> list[tuple[int, str]]:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        return [(1, text)]

    def _chunk_text(self, text: str, filename: str, page_num: int) -> list[dict]:
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []

        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = min(start + self.CHUNK_SIZE, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            chunks.append({
                "text": chunk_text,
                "filename": filename,
                "page": page_num,
                "chunk_index": len(chunks),
                "word_count": len(chunk_words),
            })

            if end >= len(words):
                break
            start = end - self.CHUNK_OVERLAP

        return chunks
