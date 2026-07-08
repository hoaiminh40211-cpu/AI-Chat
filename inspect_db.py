"""
inspect_db.py
-------------
Script tiện ích để "xem" toàn bộ nội dung đang lưu trong vector database,
giống như mở 1 cuốn sổ ghi lại tất cả chunk đã được nạp vào hệ thống.

Khác với vector_store.py (dùng để TEST TÌM KIẾM theo câu hỏi), file này
dùng để LIỆT KÊ TOÀN BỘ dữ liệu hiện có — hữu ích khi bạn muốn kiểm tra
xem dữ liệu đã nạp đúng/đủ chưa, hoặc tài liệu nào bị thiếu/lỗi.

Cách chạy:
    python inspect_db.py
"""

from vector_store import get_chroma_collection


def main():
    collection = get_chroma_collection()
    total = collection.count()

    print("=" * 60)
    print(f"TỔNG SỐ CHUNK TRONG VECTOR DATABASE: {total}")
    print("=" * 60)

    if total == 0:
        print("\n⚠️  Chưa có dữ liệu nào. Hãy chạy 'python ingest.py' trước.")
        return

    # Lấy toàn bộ dữ liệu (không phải tìm kiếm, mà lấy hết)
    all_data = collection.get()

    ids = all_data["ids"]
    documents = all_data["documents"]
    metadatas = all_data["metadatas"]

    # Gom nhóm theo file nguồn để dễ xem
    by_source = {}
    for doc, meta in zip(documents, metadatas):
        source = meta["source_file"]
        by_source.setdefault(source, []).append(doc)

    print(f"\nSố file nguồn khác nhau: {len(by_source)}\n")

    for source_file, chunks in by_source.items():
        print(f"📄 {source_file} — {len(chunks)} chunk")

    print("\n" + "=" * 60)
    detail = input("\nNhập tên file muốn xem chi tiết nội dung (Enter để bỏ qua): ")

    if detail.strip() in by_source:
        chunks = by_source[detail.strip()]
        print(f"\n--- Nội dung {len(chunks)} chunk của '{detail.strip()}' ---\n")
        for i, chunk in enumerate(chunks):
            print(f"[Chunk {i}]")
            print(chunk)
            print("-" * 40)
    elif detail.strip():
        print(f"Không tìm thấy file '{detail.strip()}' trong vector database.")


if __name__ == "__main__":
    main()
