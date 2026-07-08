"""
ingest.py
---------
Script nạp tài liệu vào vector database, hỗ trợ phân nhóm theo folder.

Cấu trúc folder:
    data/pdfs/
        chung/        → nhóm "chung" (tất cả user xem được)
        kinh_doanh/   → chỉ nhóm Kinh doanh
        ky_thuat/     → chỉ nhóm Kỹ thuật
        nhan_su/      → chỉ nhóm Nhân sự

Cách chạy:
    python ingest.py
"""

import os
from pathlib import Path
from document_processor import process_folder
from vector_store import add_chunks_to_store, get_collection_count

BASE_FOLDER = Path(__file__).parent / "data" / "pdfs"

GROUP_FOLDERS = {
    "chung":       BASE_FOLDER / "chung",
    "kinh_doanh":  BASE_FOLDER / "kinh_doanh",
    "ky_thuat":    BASE_FOLDER / "ky_thuat",
    "nhan_su":     BASE_FOLDER / "nhan_su",
}


def main():
    print("=" * 60)
    print("NẠP TÀI LIỆU VÀO VECTOR DATABASE (có phân nhóm)")
    print("=" * 60)

    total_chunks = []

    for group, folder in GROUP_FOLDERS.items():
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)

        print(f"\n📂 Nhóm [{group}]: {folder}")
        chunks = process_folder(str(folder))

        if not chunks:
            print(f"   (Không có file nào trong thư mục này)")
            continue

        # Gắn thêm thông tin nhóm vào mỗi chunk
        for c in chunks:
            c["group"] = group
            # Đổi chunk_id để tránh trùng giữa các folder khác nhau
            c["chunk_id"] = f"{group}__{c['chunk_id']}"

        total_chunks.extend(chunks)

    if not total_chunks:
        print("\n❌ Không có chunk nào được tạo ra.")
        print("   Hãy copy file PDF/Word vào các folder trong data/pdfs/")
        return

    print(f"\n💾 Đang lưu {len(total_chunks)} chunk vào vector database...")
    print("   (Lần đầu chạy sẽ download embedding model ~80MB)")
    add_chunks_to_store(total_chunks)

    print(f"\n✅ HOÀN TẤT. Tổng chunk trong DB: {get_collection_count()}")
    print("\nBây giờ chạy chatbot bằng lệnh:")
    print("   streamlit run app.py")


if __name__ == "__main__":
    main()
