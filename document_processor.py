"""
document_processor.py
----------------------
Module này lo 2 việc:
1. Đọc nội dung text từ file PDF và Word (.docx)
2. Chia (chunk) văn bản dài thành các đoạn nhỏ để đưa vào vector DB

Chạy độc lập để test:  python document_processor.py
"""

import os
from pathlib import Path
from pypdf import PdfReader
from docx import Document


def read_pdf(file_path: str) -> str:
    """Đọc toàn bộ text từ 1 file PDF, trả về 1 chuỗi text duy nhất."""
    reader = PdfReader(file_path)
    pages_text = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text.append(text)
    return "\n".join(pages_text)


def read_docx(file_path: str) -> str:
    """Đọc toàn bộ text từ 1 file Word (.docx)."""
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def read_document(file_path: str) -> str:
    """
    Tự nhận diện loại file (.pdf hoặc .docx) và đọc nội dung tương ứng.
    Ném lỗi rõ ràng nếu định dạng không được hỗ trợ.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return read_pdf(file_path)
    elif ext == ".docx":
        return read_docx(file_path)
    else:
        raise ValueError(
            f"Định dạng file '{ext}' chưa được hỗ trợ. "
            f"Chỉ hỗ trợ .pdf và .docx. File lỗi: {file_path}"
        )


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """
    Chia 1 đoạn text dài thành các chunk nhỏ hơn.

    chunk_size: số ký tự tối đa mỗi chunk (xấp xỉ, không cắt giữa câu nếu có thể)
    overlap:    số ký tự lặp lại giữa 2 chunk liên tiếp, giúp không mất ngữ cảnh
                ở điểm cắt

    Lưu ý: đây là cách chunk đơn giản theo ký tự, đủ dùng cho demo.
    Khi lên production, có thể nâng cấp lên chunk theo câu/đoạn văn (sentence-aware).
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Cố gắng cắt tại dấu xuống dòng hoặc dấu câu gần nhất để chunk không bị
        # cắt ngang giữa câu, đọc tự nhiên hơn
        if end < text_length:
            last_newline = text.rfind("\n", start, end)
            last_period = text.rfind(". ", start, end)
            cut_point = max(last_newline, last_period)
            if cut_point > start:
                end = cut_point + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Lùi lại "overlap" ký tự để chunk sau có phần gối lên chunk trước
        start = end - overlap
        if start <= 0:
            start = end

    return chunks


def process_folder(folder_path: str) -> list[dict]:
    """
    Đọc tất cả file PDF/Word trong 1 folder, chia chunk, và trả về danh sách
    dict có dạng:
        {
            "chunk_id": "ten_file.pdf__chunk_0",
            "text": "...",
            "source_file": "ten_file.pdf",
            "chunk_index": 0
        }

    Đây là cấu trúc dữ liệu sẽ được đưa vào vector DB ở bước tiếp theo.
    """
    folder = Path(folder_path)
    supported_extensions = {".pdf", ".docx"}
    all_chunks = []

    files = [f for f in folder.iterdir() if f.suffix.lower() in supported_extensions]

    if not files:
        print(f"⚠️  Không tìm thấy file .pdf hoặc .docx nào trong: {folder_path}")
        return []

    for file_path in files:
        print(f"📄 Đang đọc: {file_path.name}")
        try:
            raw_text = read_document(str(file_path))
        except Exception as e:
            print(f"   ❌ Lỗi khi đọc file này, bỏ qua: {e}")
            continue

        if not raw_text.strip():
            print(f"   ⚠️  File không có text trích xuất được (có thể là PDF scan ảnh)")
            continue

        chunks = chunk_text(raw_text)
        print(f"   ✅ Chia được {len(chunks)} chunk")

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"{file_path.name}__chunk_{i}",
                "text": chunk,
                "source_file": file_path.name,
                "chunk_index": i,
            })

    return all_chunks


if __name__ == "__main__":
    # Chạy thử nghiệm: đọc thư mục data/pdfs và in ra kết quả
    folder = os.path.join(os.path.dirname(__file__), "data", "pdfs")
    results = process_folder(folder)
    print(f"\n=== Tổng cộng: {len(results)} chunks từ tất cả tài liệu ===")
    if results:
        print("\n--- Ví dụ chunk đầu tiên ---")
        print(results[0])
