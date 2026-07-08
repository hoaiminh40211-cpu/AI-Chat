"""
auth.py
-------
Quản lý toàn bộ việc xác thực và phân quyền:
- Tạo/lưu tài khoản user vào SQLite (users.db)
- Đăng ký tự đăng ký, chờ admin duyệt
- Đăng nhập kiểm tra username/password (hash bcrypt)
- Quản lý session trong Streamlit st.session_state
- Phân quyền: admin / user thường, gán nhóm phòng ban

Các nhóm mặc định:
  - admin       : toàn quyền, xem tất cả tài liệu, quản lý user
  - chung       : tất cả user đã được duyệt đều có
  - kinh_doanh  : chỉ nhóm Kinh doanh
  - ky_thuat    : chỉ nhóm Kỹ thuật
  - nhan_su     : chỉ nhóm Nhân sự
"""

import sqlite3
import hashlib
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "users.db"

# Nhóm hợp lệ trong hệ thống
VALID_GROUPS = ["chung", "kinh_doanh", "ky_thuat", "nhan_su", "admin"]

# Tên hiển thị đẹp cho từng nhóm
GROUP_LABELS = {
    "chung":       "📁 Chung (tất cả)",
    "kinh_doanh":  "💼 Kinh doanh",
    "ky_thuat":    "🔧 Kỹ thuật",
    "nhan_su":     "👥 Nhân sự",
    "admin":       "🔑 Admin",
}


def _hash_password(password: str) -> str:
    """Hash password bằng SHA-256 + salt cố định. Đủ dùng cho demo nội bộ."""
    salt = "rag_chatbot_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tạo bảng users nếu chưa có, và tạo tài khoản admin mặc định."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            full_name   TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            groups      TEXT NOT NULL DEFAULT 'chung',
            created_at  TEXT NOT NULL,
            approved_at TEXT
        )
    """)
    conn.commit()

    # Tạo tài khoản admin mặc định nếu chưa có
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        now = datetime.now().isoformat()
        cur.execute("""
            INSERT INTO users (username, password, full_name, status, groups, created_at, approved_at)
            VALUES (?, ?, ?, 'active', 'admin,chung,kinh_doanh,ky_thuat,nhan_su', ?, ?)
        """, ("admin", _hash_password("admin123"), "Quản trị viên", now, now))
        conn.commit()

    conn.close()


def register_user(username: str, password: str, full_name: str) -> tuple[bool, str]:
    """
    Đăng ký tài khoản mới, trạng thái mặc định là 'pending' (chờ admin duyệt).
    Trả về (True, message) nếu thành công, (False, lỗi) nếu thất bại.
    """
    if not username or not password or not full_name:
        return False, "Vui lòng điền đầy đủ thông tin."
    if len(username) < 3:
        return False, "Username phải có ít nhất 3 ký tự."
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."
    if not username.isalnum():
        return False, "Username chỉ được dùng chữ cái và số, không dấu cách."

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (username, password, full_name, status, groups, created_at)
            VALUES (?, ?, ?, 'pending', 'chung', ?)
        """, (username.lower(), _hash_password(password), full_name, datetime.now().isoformat()))
        conn.commit()
        return True, "Đăng ký thành công! Tài khoản đang chờ admin duyệt."
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' đã được sử dụng. Vui lòng chọn tên khác."
    finally:
        conn.close()


def login(username: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Đăng nhập. Trả về (True, message, user_dict) nếu thành công,
    (False, lý do, None) nếu thất bại.
    """
    if not username or not password:
        return False, "Vui lòng nhập username và mật khẩu.", None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username.lower(),))
    user = cur.fetchone()
    conn.close()

    if not user:
        return False, "Username không tồn tại.", None
    if user["password"] != _hash_password(password):
        return False, "Mật khẩu không đúng.", None
    if user["status"] == "pending":
        return False, "Tài khoản đang chờ admin duyệt. Vui lòng chờ.", None
    if user["status"] == "rejected":
        return False, "Tài khoản đã bị từ chối. Liên hệ admin để biết thêm.", None
    if user["status"] != "active":
        return False, "Tài khoản không hợp lệ.", None

    user_dict = dict(user)
    user_dict["groups_list"] = [g.strip() for g in user["groups"].split(",")]
    return True, "Đăng nhập thành công!", user_dict


def get_current_user() -> dict | None:
    """Lấy user đang đăng nhập từ Streamlit session state."""
    import streamlit as st
    return st.session_state.get("current_user")


def require_login():
    """
    Gọi hàm này ở đầu mỗi trang cần đăng nhập.
    Nếu chưa đăng nhập → redirect về trang login (dừng render trang hiện tại).
    """
    import streamlit as st
    if not get_current_user():
        st.warning("⚠️ Bạn cần đăng nhập để sử dụng chatbot.")
        st.stop()


def require_admin():
    """Gọi hàm này ở đầu trang chỉ dành cho admin."""
    import streamlit as st
    user = get_current_user()
    if not user or "admin" not in user.get("groups_list", []):
        st.error("🚫 Bạn không có quyền truy cập trang này.")
        st.stop()


def is_admin(user: dict) -> bool:
    return "admin" in user.get("groups_list", [])


def get_user_groups(user: dict) -> list[str]:
    return user.get("groups_list", ["chung"])


# ============================================================
# Các hàm dành cho admin quản lý user
# ============================================================

def list_users(status_filter: str = None) -> list[dict]:
    """Lấy danh sách tất cả user, có thể lọc theo status."""
    conn = get_connection()
    cur = conn.cursor()
    if status_filter:
        cur.execute("SELECT * FROM users WHERE status = ? ORDER BY created_at DESC", (status_filter,))
    else:
        cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def approve_user(user_id: int, groups: list[str]) -> bool:
    """Admin duyệt user và gán nhóm."""
    groups_str = ",".join(g for g in groups if g in VALID_GROUPS)
    if not groups_str:
        groups_str = "chung"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET status = 'active', groups = ?, approved_at = ?
        WHERE id = ?
    """, (groups_str, datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()
    return True


def reject_user(user_id: int) -> bool:
    """Admin từ chối user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = 'rejected' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


def update_user_groups(user_id: int, groups: list[str]) -> bool:
    """Admin cập nhật lại nhóm của user đã active."""
    groups_str = ",".join(g for g in groups if g in VALID_GROUPS)
    if not groups_str:
        groups_str = "chung"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET groups = ? WHERE id = ?", (groups_str, user_id))
    conn.commit()
    conn.close()
    return True


def delete_user(user_id: int) -> bool:
    """Admin xóa user (không thể xóa admin gốc)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ? AND username != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    return True


def change_password(user_id: int, new_password: str) -> tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = ? WHERE id = ?",
                (_hash_password(new_password), user_id))
    conn.commit()
    conn.close()
    return True, "Đổi mật khẩu thành công."


# Khởi tạo DB khi import
init_db()


if __name__ == "__main__":
    print("=== Test auth.py ===")
    ok, msg, _ = login("admin", "admin123")
    print(f"Login admin: {ok} — {msg}")

    ok, msg = register_user("testuser", "pass123", "Nguyễn Test")
    print(f"Register: {ok} — {msg}")

    users = list_users()
    print(f"Tổng số user: {len(users)}")
    for u in users:
        print(f"  {u['username']} | {u['status']} | {u['groups']}")
