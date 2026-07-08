"""
vector_store.py
----------------
Quản lý vector database Chroma với hỗ trợ phân quyền theo nhóm.

Mỗi chunk được lưu kèm metadata:
  - source_file  : tên file gốc
  - chunk_index  : số thứ tự chunk trong file
  - group        : nhóm phòng ban được phép xem (kinh_doanh, ky_thuat, nhan_su, chung)

Khi search, truyền vào danh sách groups của user hiện tại để chỉ lấy
chunk thuộc nhóm user được phép xem.
"""

import chromadb
from chromadb.utils import embedding_functions

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DISTANCE_THRESHOLD = 1.3


def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )
    return collection


def add_chunks_to_store(chunks: list[dict]):
    """
    Lưu chunk vào Chroma. Mỗi chunk phải có thêm field 'group'
    để biết nhóm nào được phép xem.
    """
    if not chunks:
        print("⚠️  Không có chunk nào để lưu.")
        return

    collection = get_chroma_collection()

    ids       = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "source_file":  c["source_file"],
            "chunk_index":  c["chunk_index"],
            "group":        c.get("group", "chung"),
        }
        for c in chunks
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(f"✅ Đã lưu {len(chunks)} chunk vào vector database.")


def search_relevant_chunks(query: str, user_groups: list[str] = None, top_k: int = 4) -> list[dict]:
    """
    Tìm top_k chunk liên quan nhất tới câu hỏi.

    user_groups: danh sách nhóm của user đang đăng nhập.
                 Chỉ trả về chunk có group nằm trong danh sách này.
                 Nếu None → không lọc (dùng khi test).
    """
    collection = get_chroma_collection()

    # Xây dựng điều kiện lọc theo nhóm
    where_filter = None
    if user_groups:
        if len(user_groups) == 1:
            where_filter = {"group": {"$eq": user_groups[0]}}
        else:
            where_filter = {"group": {"$in": user_groups}}

    query_params = {
        "query_texts": [query],
        "n_results":   min(top_k, get_collection_count() or 1),
    }
    if where_filter:
        query_params["where"] = where_filter

    results = collection.query(**query_params)

    relevant_chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        relevant_chunks.append({
            "text":        doc,
            "source_file": meta["source_file"],
            "chunk_index": meta["chunk_index"],
            "group":       meta.get("group", "chung"),
            "distance":    dist,
        })

    return relevant_chunks


def get_collection_count() -> int:
    collection = get_chroma_collection()
    return collection.count()


def get_groups_summary() -> dict:
    """Trả về dict {group: số chunk} để admin xem tổng quan."""
    collection = get_chroma_collection()
    all_data = collection.get()
    summary = {}
    for meta in all_data.get("metadatas", []):
        g = meta.get("group", "chung")
        summary[g] = summary.get(g, 0) + 1
    return summary


if __name__ == "__main__":
    count = get_collection_count()
    print(f"Số chunk trong vector DB: {count}")
    if count > 0:
        print("\nPhân bổ theo nhóm:")
        for g, n in get_groups_summary().items():
            print(f"  {g}: {n} chunk")
