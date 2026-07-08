"""
rag_chat.py
-----------
Query pipeline: retrieval + generation, có lọc tài liệu theo nhóm user.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv
from vector_store import search_relevant_chunks, DISTANCE_THRESHOLD

load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL_NAME = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Bạn là trợ lý AI nội bộ, chỉ trả lời dựa trên các đoạn tài liệu (context) được cung cấp dưới đây. Tuyệt đối không sử dụng kiến thức bên ngoài context này.

QUY TẮC BẮT BUỘC:
1. Chỉ trả lời nếu thông tin có trong context được cung cấp.
2. Nếu context không chứa thông tin để trả lời, hãy nói: "Tôi không tìm thấy thông tin này trong tài liệu được cung cấp."
3. Khi trả lời, trích dẫn rõ tài liệu nguồn (ví dụ: "Theo tài liệu [Tên file]...").
4. Nếu context có thông tin mâu thuẫn giữa các nguồn, hãy nêu rõ sự mâu thuẫn.
5. Không suy luận vượt ra ngoài những gì context nêu rõ.
6. Trả lời ngắn gọn, đúng trọng tâm."""


def build_context_block(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks):
        parts.append(
            f"[Đoạn {i+1} - Nguồn: {chunk['source_file']} | Nhóm: {chunk['group']}]\n{chunk['text']}"
        )
    return "\n\n".join(parts)


def ask(question: str, user_groups: list[str] = None, top_k: int = 4) -> dict:
    """
    Trả lời câu hỏi, chỉ dùng tài liệu thuộc nhóm của user.

    user_groups: list nhóm của user đang đăng nhập (từ auth.get_user_groups).
                 Nếu None → không lọc nhóm (chỉ dùng khi test terminal).
    """
    relevant_chunks = search_relevant_chunks(question, user_groups=user_groups, top_k=top_k)

    if not relevant_chunks or relevant_chunks[0]["distance"] > DISTANCE_THRESHOLD:
        return {
            "answer":      "Tôi không tìm thấy thông tin này trong tài liệu được cung cấp.",
            "sources":     [],
            "chunks_used": [],
            "skipped_llm": True,
        }

    context_block = build_context_block(relevant_chunks)
    user_message  = f"CONTEXT:\n{context_block}\n\nCÂU HỎI: {question}"

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    answer_text    = response.content[0].text
    unique_sources = sorted(set(c["source_file"] for c in relevant_chunks))

    return {
        "answer":      answer_text,
        "sources":     unique_sources,
        "chunks_used": relevant_chunks,
        "skipped_llm": False,
    }


if __name__ == "__main__":
    print("=== Test RAG chat (không lọc nhóm) ===\n")
    while True:
        q = input("Câu hỏi (exit để thoát): ")
        if q.strip().lower() in ("exit", "quit"):
            break
        result = ask(q)
        print(f"\n💬 {result['answer']}")
        if result["sources"]:
            print(f"📎 Nguồn: {', '.join(result['sources'])}")
        print()
