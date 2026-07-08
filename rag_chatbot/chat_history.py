"""
chat_history.py
----------------
Module quản lý việc LƯU TRỮ CÁC PHIÊN CHAT (giống "Conversations" trong Claude/ChatGPT).

Dùng SQLite (built-in trong Python, không cần cài thêm gì) để lưu vĩnh viễn
vào 1 file duy nhất: chat_sessions.db — khác hoàn toàn với vector database
(chroma_db), không liên quan đến nhau.

Cấu trúc dữ liệu:
- 1 "session" = 1 cuộc hội thoại (giống 1 "conversation" trong Claude)
- Mỗi session có nhiều "message" (câu hỏi của user + câu trả lời của assistant)
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "chat_sessions.db"


def get_connection():
    """Mở kết nối tới file SQLite, tự tạo file nếu chưa tồn tại."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # cho phép truy cập cột theo tên, dễ đọc hơn
    return conn


def init_db():
    """
    Tạo 2 bảng nếu chưa có:
    - sessions: thông tin từng phiên chat (id, tên hiển thị, thời gian tạo)
    - messages: từng tin nhắn trong phiên đó (role: user/assistant, nội dung, nguồn)
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def create_session(title: str = "Cuộc trò chuyện mới") -> str:
    """
    Tạo 1 session mới, trả về session_id (dạng UUID, duy nhất).
    """
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, title, now, now),
    )
    conn.commit()
    conn.close()

    return session_id


def list_sessions() -> list[dict]:
    """
    Lấy danh sách tất cả session, sắp xếp theo session được cập nhật gần nhất lên đầu
    (giống cách Claude hiển thị "Recent" ở sidebar).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_messages(session_id: str) -> list[dict]:
    """Lấy toàn bộ tin nhắn của 1 session, theo đúng thứ tự thời gian."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, sources, created_at FROM messages "
        "WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    )
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def add_message(session_id: str, role: str, content: str, sources: str = ""):
    """
    Lưu 1 tin nhắn mới vào session, đồng thời cập nhật "updated_at" của session
    đó để nó nhảy lên đầu danh sách (giống hành vi của Claude/ChatGPT).
    """
    now = datetime.now().isoformat()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (session_id, role, content, sources, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, role, content, sources, now),
    )
    cur.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def update_session_title(session_id: str, title: str):
    """
    Đổi tên hiển thị của session — dùng để tự đặt tên session theo câu hỏi
    đầu tiên của user (giống Claude tự đặt tên cuộc hội thoại).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE sessions SET title = ? WHERE id = ?",
        (title, session_id),
    )
    conn.commit()
    conn.close()


def delete_session(session_id: str):
    """Xoá 1 session và toàn bộ tin nhắn thuộc session đó."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def make_title_from_text(text: str, max_length: int = 40) -> str:
    """
    Tự tạo tên session ngắn gọn từ câu hỏi đầu tiên của user,
    giống cách Claude/ChatGPT tự đặt tên cuộc hội thoại.
    """
    text = text.strip().replace("\n", " ")
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


# Khởi tạo database ngay khi module được import lần đầu,
# đảm bảo file + bảng luôn tồn tại trước khi app.py dùng đến.
init_db()


if __name__ == "__main__":
    # Test nhanh qua terminal
    print("=== Test chat_history.py ===")
    sid = create_session("Test session")
    print(f"Đã tạo session: {sid}")

    add_message(sid, "user", "Chính sách nghỉ phép là gì?")
    add_message(sid, "assistant", "Theo tài liệu, nhân viên được nghỉ 12 ngày/năm.", "chinh_sach.docx")

    print("\nDanh sách session:")
    for s in list_sessions():
        print(f"  - {s['title']} (id={s['id'][:8]}...)")

    print(f"\nTin nhắn trong session {sid[:8]}...:")
    for m in get_messages(sid):
        print(f"  [{m['role']}] {m['content']}")
