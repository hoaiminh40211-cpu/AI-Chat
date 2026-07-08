"""
app.py
------
UI chính của RAG Chatbot với hệ thống phân quyền đầy đủ.

Các trang:
  - Login / Đăng ký  : mặc định khi chưa đăng nhập
  - Chat             : chatbot RAG, lọc tài liệu theo nhóm user
  - Admin Panel      : chỉ admin, duyệt user, gán nhóm, xem thống kê

Chạy: streamlit run app.py
"""

import streamlit as st
import auth
import chat_history as history
from rag_chat import ask
from vector_store import get_collection_count, get_groups_summary
from auth import (
    login, register_user, get_current_user, is_admin,
    get_user_groups, list_users, approve_user, reject_user,
    update_user_groups, delete_user, VALID_GROUPS, GROUP_LABELS,
)

st.set_page_config(page_title="RAG Chatbot", page_icon="💬", layout="wide")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 860px; }
    section[data-testid="stSidebar"] button { text-align: left; }

    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse; margin-left: 18%;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"])
        div[data-testid="stChatMessageContent"] {
        background-color: #2563eb; color: white;
        border-radius: 16px; padding: 0.6rem 1rem;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"])
        div[data-testid="stChatMessageContent"] p { color: white; }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        margin-right: 18%;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"])
        div[data-testid="stChatMessageContent"] {
        background-color: rgba(120,120,120,0.12);
        border-radius: 16px; padding: 0.6rem 1rem;
    }
    .source-caption { color: #888; font-size: 0.82rem; }
    .badge {
        display: inline-block; padding: 2px 10px;
        border-radius: 12px; font-size: 0.78rem; font-weight: 500;
    }
    .badge-admin   { background:#fee2e2; color:#991b1b; }
    .badge-active  { background:#dcfce7; color:#166534; }
    .badge-pending { background:#fef9c3; color:#854d0e; }
    .badge-reject  { background:#f3f4f6; color:#6b7280; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# TRANG LOGIN / ĐĂNG KÝ
# ============================================================
def render_login_page():
    st.title("💬 RAG Chatbot")
    st.caption("Đăng nhập để sử dụng chatbot tài liệu nội bộ")

    tab_login, tab_register = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký tài khoản"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")

        if submitted:
            ok, msg, user = login(username, password)
            if ok:
                st.session_state.current_user = user
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error(msg)

        st.info("💡 Tài khoản admin mặc định: **admin** / **admin123** — đổi mật khẩu sau khi đăng nhập lần đầu.")

    with tab_register:
        with st.form("register_form"):
            new_fullname = st.text_input("Họ và tên")
            new_username = st.text_input("Username (chỉ chữ cái và số, không dấu cách)")
            new_password = st.text_input("Mật khẩu (ít nhất 6 ký tự)", type="password")
            submitted_reg = st.form_submit_button("Gửi yêu cầu đăng ký", use_container_width=True)

        if submitted_reg:
            ok, msg = register_user(new_username, new_password, new_fullname)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


# ============================================================
# TRANG CHAT
# ============================================================
def render_chat_page(user: dict):
    user_groups   = get_user_groups(user)
    doc_count     = get_collection_count()

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        groups_display = " ".join(
            f"`{GROUP_LABELS.get(g, g)}`" for g in user_groups
        )
        st.caption(f"Nhóm: {groups_display}")
        st.markdown("---")

        if is_admin(user):
            if st.button("⚙️ Admin Panel", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()

        if st.button("➕ Cuộc trò chuyện mới", use_container_width=True, type="primary"):
            st.session_state.current_session_id = history.create_session()
            st.rerun()

        st.markdown("---")
        st.caption("LỊCH SỬ TRÒ CHUYỆN")

        sessions = history.list_sessions()
        if not sessions:
            st.caption("Chưa có cuộc trò chuyện nào.")
        else:
            for s in sessions:
                is_active = s["id"] == st.session_state.get("current_session_id")
                col1, col2 = st.columns([5, 1])
                with col1:
                    label = ("📍 " if is_active else "") + s["title"]
                    if st.button(label, key=f"sess_{s['id']}", use_container_width=True):
                        st.session_state.current_session_id = s["id"]
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{s['id']}"):
                        history.delete_session(s["id"])
                        remaining = history.list_sessions()
                        st.session_state.current_session_id = (
                            remaining[0]["id"] if remaining else history.create_session()
                        )
                        st.rerun()

        st.markdown("---")
        if doc_count == 0:
            st.error("⚠️ Chưa có tài liệu. Chạy `python ingest.py`")
        else:
            st.caption(f"✅ {doc_count} đoạn tài liệu")

        st.markdown("---")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Màn hình chat chính
    if "current_session_id" not in st.session_state:
        sessions = history.list_sessions()
        st.session_state.current_session_id = (
            sessions[0]["id"] if sessions else history.create_session()
        )

    current_id = st.session_state.current_session_id
    messages   = history.get_messages(current_id)

    st.title("💬 RAG Chatbot")
    st.caption(f"Bạn đang xem tài liệu của nhóm: {', '.join(GROUP_LABELS.get(g, g) for g in user_groups)}")

    if doc_count == 0:
        st.warning("Chưa có tài liệu nào trong hệ thống. Admin cần chạy `python ingest.py` trước.")
        st.stop()

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                st.markdown(f"<span class='source-caption'>📎 {msg['sources']}</span>", unsafe_allow_html=True)

    user_input = st.chat_input("Nhập câu hỏi về tài liệu...")

    if user_input:
        if not messages:
            history.update_session_title(current_id, history.make_title_from_text(user_input))

        history.add_message(current_id, "user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Đang tìm kiếm..."):
                result = ask(user_input, user_groups=user_groups)

            st.markdown(result["answer"])
            sources_str = ", ".join(result["sources"]) if result["sources"] else ""
            if sources_str:
                st.markdown(f"<span class='source-caption'>📎 Nguồn: {sources_str}</span>", unsafe_allow_html=True)

            if result["chunks_used"]:
                with st.expander("🔍 Xem chi tiết đoạn tài liệu đã dùng"):
                    for i, chunk in enumerate(result["chunks_used"]):
                        st.markdown(
                            f"**[{i+1}] {chunk['source_file']}** | Nhóm: `{chunk['group']}` | distance={chunk['distance']:.3f}"
                        )
                        st.text(chunk["text"][:500] + ("..." if len(chunk["text"]) > 500 else ""))
                        st.divider()

        history.add_message(current_id, "assistant", result["answer"], sources_str)
        st.rerun()


# ============================================================
# TRANG ADMIN PANEL
# ============================================================
def render_admin_page(user: dict):
    st.title("⚙️ Admin Panel")

    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        if st.button("💬 Quay lại Chat", use_container_width=True, type="primary"):
            st.session_state.page = "chat"
            st.rerun()
        st.markdown("---")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["⏳ Chờ duyệt", "👥 Tất cả user", "📊 Thống kê tài liệu"])

    # ---- Tab 1: Duyệt user mới ----
    with tab1:
        pending = list_users("pending")
        if not pending:
            st.info("✅ Không có tài khoản nào đang chờ duyệt.")
        else:
            st.caption(f"{len(pending)} tài khoản đang chờ duyệt")
            for u in pending:
                with st.container(border=True):
                    col_info, col_action = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"**{u['full_name']}** (`{u['username']}`)")
                        st.caption(f"Đăng ký lúc: {u['created_at'][:16].replace('T', ' ')}")

                    with col_action:
                        # Chọn nhóm trước khi duyệt
                        selected_groups = st.multiselect(
                            "Gán nhóm",
                            options=[g for g in VALID_GROUPS if g != "admin"],
                            default=["chung"],
                            key=f"groups_{u['id']}",
                            format_func=lambda g: GROUP_LABELS.get(g, g),
                        )
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Duyệt", key=f"approve_{u['id']}", use_container_width=True, type="primary"):
                                approve_user(u["id"], selected_groups or ["chung"])
                                st.success(f"Đã duyệt {u['username']}")
                                st.rerun()
                        with c2:
                            if st.button("❌ Từ chối", key=f"reject_{u['id']}", use_container_width=True):
                                reject_user(u["id"])
                                st.warning(f"Đã từ chối {u['username']}")
                                st.rerun()

    # ---- Tab 2: Quản lý tất cả user ----
    with tab2:
        all_users = list_users()
        st.caption(f"Tổng {len(all_users)} tài khoản")

        for u in all_users:
            if u["username"] == "admin" and u["id"] == 1:
                continue  # Bỏ qua admin gốc trong danh sách

            status_badge = {
                "active":   "<span class='badge badge-active'>✓ Active</span>",
                "pending":  "<span class='badge badge-pending'>⏳ Pending</span>",
                "rejected": "<span class='badge badge-reject'>✗ Rejected</span>",
            }.get(u["status"], u["status"])

            with st.expander(f"**{u['full_name']}** (`{u['username']}`) — {u['status'].upper()}"):
                st.markdown(f"Trạng thái: {status_badge}", unsafe_allow_html=True)
                st.caption(f"Nhóm hiện tại: {u['groups']}")
                st.caption(f"Tạo lúc: {u['created_at'][:16].replace('T', ' ')}")

                # Cập nhật nhóm
                current_groups = [g.strip() for g in u["groups"].split(",")]
                new_groups = st.multiselect(
                    "Cập nhật nhóm",
                    options=[g for g in VALID_GROUPS if g != "admin"],
                    default=[g for g in current_groups if g in VALID_GROUPS and g != "admin"],
                    key=f"edit_groups_{u['id']}",
                    format_func=lambda g: GROUP_LABELS.get(g, g),
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💾 Cập nhật nhóm", key=f"update_{u['id']}", use_container_width=True):
                        update_user_groups(u["id"], new_groups or ["chung"])
                        st.success("Đã cập nhật!")
                        st.rerun()
                with col2:
                    if u["status"] == "rejected":
                        if st.button("✅ Kích hoạt lại", key=f"reactivate_{u['id']}", use_container_width=True):
                            approve_user(u["id"], new_groups or ["chung"])
                            st.rerun()
                with col3:
                    if st.button("🗑️ Xóa user", key=f"delete_{u['id']}", use_container_width=True):
                        delete_user(u["id"])
                        st.warning(f"Đã xóa {u['username']}")
                        st.rerun()

    # ---- Tab 3: Thống kê tài liệu ----
    with tab3:
        total = get_collection_count()
        st.metric("Tổng số chunk trong Vector DB", total)

        if total > 0:
            st.markdown("**Phân bổ tài liệu theo nhóm:**")
            summary = get_groups_summary()
            for g, count in sorted(summary.items()):
                label = GROUP_LABELS.get(g, g)
                st.progress(count / total, text=f"{label}: {count} chunk")

        st.markdown("---")
        st.info(
            "Để thêm tài liệu mới:\n"
            "1. Copy file PDF/Word vào đúng folder `data/pdfs/<nhóm>/`\n"
            "2. Chạy lại `python ingest.py` trong terminal (đã activate venv)"
        )


# ============================================================
# ĐIỀU HƯỚNG TRANG
# ============================================================
user = get_current_user()

if not user:
    render_login_page()
else:
    page = st.session_state.get("page", "chat")

    if page == "admin":
        if is_admin(user):
            render_admin_page(user)
        else:
            st.error("🚫 Bạn không có quyền truy cập trang này.")
            st.session_state.page = "chat"
            st.rerun()
    else:
        render_chat_page(user)
