# Hướng dẫn cài đặt RAG Chatbot Demo (Windows)

Hướng dẫn này dành cho người mới, làm theo từng bước, không bỏ bước nào.

---

## Bước 0: Kiểm tra đã có Python chưa

Mở **PowerShell** (bấm Start, gõ "PowerShell", Enter), chạy:

```powershell
python --version
```

- Nếu hiện `Python 3.10.x` hoặc cao hơn (3.10, 3.11, 3.12) → bỏ qua, sang Bước 1.
- Nếu hiện lỗi "không tìm thấy lệnh python" → cài Python tại https://www.python.org/downloads/
  - **Quan trọng khi cài**: tick chọn ô **"Add Python to PATH"** ở màn hình đầu tiên của installer, nếu không các lệnh sau sẽ không chạy được.
  - Cài xong, **đóng và mở lại PowerShell** rồi chạy lại lệnh kiểm tra trên.

---

## Bước 1: Copy toàn bộ file project vào máy

Tạo 1 folder ở vị trí dễ tìm, ví dụ `C:\rag-chatbot-demo`, và copy toàn bộ các file mình đã chuẩn bị vào đó. Cấu trúc folder sẽ như sau:

```
rag-chatbot-demo/
├── data/
│   └── pdfs/              ← copy file PDF/Word của bạn vào đây
├── app.py
├── document_processor.py
├── ingest.py
├── rag_chat.py
├── vector_store.py
├── requirements.txt
├── .env.example
└── README.md (hướng dẫn này)
```

---

## Bước 2: Mở PowerShell tại đúng folder project

Cách nhanh nhất: mở **File Explorer**, vào folder `rag-chatbot-demo`, gõ `powershell` vào ô địa chỉ (thanh đường dẫn ở trên), Enter. PowerShell sẽ mở sẵn tại đúng folder này.

Kiểm tra lại bằng lệnh:

```powershell
dir
```

Phải thấy danh sách các file như `app.py`, `requirements.txt`...

---

## Bước 3: Tạo môi trường Python riêng (virtual environment)

Đây là bước **quan trọng**, giúp các thư viện của project này không xung đột với phần mềm khác trên máy bạn.

```powershell
python -m venv venv
```

Lệnh này tạo 1 folder `venv` chứa Python riêng cho project. Chạy xong, **kích hoạt** nó:

```powershell
.\venv\Scripts\Activate
```

Sau khi chạy, đầu dòng lệnh PowerShell sẽ hiện `(venv)` ở phía trước — đây là dấu hiệu môi trường đã được kích hoạt đúng.

**Lỗi thường gặp**: nếu PowerShell báo lỗi liên quan đến "execution policy", chạy lệnh sau rồi thử kích hoạt lại:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Chọn `Y` (Yes) khi được hỏi xác nhận.

> **Lưu ý**: mỗi lần mở PowerShell mới để làm việc với project này, bạn cần chạy lại lệnh `.\venv\Scripts\Activate` (Bước 3) trước khi chạy bất kỳ lệnh Python nào khác.

---

## Bước 4: Cài đặt các thư viện cần thiết

Đảm bảo bạn đang thấy `(venv)` ở đầu dòng lệnh (đã kích hoạt ở Bước 3), sau đó chạy:

```powershell
pip install -r requirements.txt
```

Lệnh này sẽ tự động cài tất cả thư viện cần thiết (anthropic, chromadb, streamlit...). Quá trình này mất khoảng **3-7 phút** tùy tốc độ mạng, vì có một số thư viện khá nặng (sentence-transformers).

Nếu thấy dòng cuối cùng có dạng `Successfully installed ...` → cài đặt thành công.

---

## Bước 5: Lấy và cấu hình Anthropic API key

1. Nếu chưa có key, làm theo hướng dẫn lấy key tại console.anthropic.com (đã hướng dẫn ở phần chat trước).
2. Trong folder project, copy file `.env.example` thành file mới tên là `.env` (chỉ cần đổi tên, bỏ phần `.example`).
3. Mở file `.env` bằng Notepad, thay dòng:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
   bằng key thật của bạn, ví dụ:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
   ```
4. Lưu file lại.

**Lưu ý bảo mật**: không chia sẻ file `.env` này cho ai, không đăng lên mạng hay gửi qua chat.

---

## Bước 6: Copy file PDF/Word của bạn vào đúng vị trí

Copy 5-10 file PDF (hoặc .docx) bạn muốn dùng cho demo vào folder:

```
rag-chatbot-demo/data/pdfs/
```

---

## Bước 7: Nạp tài liệu vào vector database

Vẫn trong PowerShell (đã activate venv), chạy:

```powershell
python ingest.py
```

- Lần đầu chạy, script sẽ tự **download embedding model** (~80MB), có thể mất 1-2 phút tùy mạng.
- Sau đó script đọc từng file, chia chunk, và lưu vào vector database (folder `chroma_db` sẽ tự được tạo).
- Khi xong, bạn sẽ thấy dòng `✅ HOÀN TẤT`.

**Mỗi khi bạn thêm tài liệu mới vào folder `data/pdfs`, chạy lại lệnh này** để cập nhật vector database.

---

## Bước 8: Chạy chatbot

```powershell
streamlit run app.py
```

Lệnh này sẽ tự mở trình duyệt với chatbot tại địa chỉ `http://localhost:8501`. Nếu không tự mở, copy địa chỉ đó dán vào trình duyệt.

Giờ bạn có thể chat hỏi về nội dung các file PDF/Word đã nạp.

Để dừng chatbot, quay lại PowerShell, bấm `Ctrl + C`.

---

## Các lỗi thường gặp

| Lỗi | Nguyên nhân khả năng cao | Cách xử lý |
|---|---|---|
| `ModuleNotFoundError: No module named 'anthropic'` | Chưa activate venv, hoặc chưa chạy `pip install -r requirements.txt` | Chạy lại Bước 3 và Bước 4 |
| `authentication_error` khi chat | API key sai hoặc chưa add thẻ thanh toán trên console.anthropic.com | Kiểm tra lại file `.env`, kiểm tra billing trên console |
| Vector DB báo 0 chunk | Chưa chạy `python ingest.py`, hoặc file PDF là dạng scan ảnh không trích xuất được text | Chạy `python ingest.py`, kiểm tra PDF có phải dạng scan không |
| PowerShell báo lỗi "execution policy" khi activate venv | Windows chặn chạy script theo mặc định | Chạy lệnh `Set-ExecutionPolicy` ở Bước 3 |
| Chatbot trả lời "không tìm thấy thông tin" dù tài liệu có | Câu hỏi quá khác cách diễn đạt trong tài liệu, hoặc ngưỡng `DISTANCE_THRESHOLD` trong `rag_chat.py` đang quá chặt | Thử hỏi câu khác gần với từ ngữ trong tài liệu, hoặc tăng giá trị `DISTANCE_THRESHOLD` trong file `rag_chat.py` |

---

## Cấu trúc code, nếu bạn muốn tìm hiểu/sửa

- `document_processor.py` — đọc PDF/Word, chia chunk
- `vector_store.py` — vector hóa và lưu/tìm trong Chroma
- `ingest.py` — script chạy 1 lần để nạp tài liệu (chạy lại khi có file mới)
- `rag_chat.py` — ghép retrieval + gọi Claude, có system prompt chống bịa thông tin
- `chat_history.py` — quản lý lưu trữ các cuộc trò chuyện (sessions) vào file `chat_sessions.db`
- `inspect_db.py` — script tiện ích để xem nội dung đã nạp vào vector DB
- `app.py` — UI chat Streamlit đa phiên (giống Claude/ChatGPT), đây là file chạy chính khi dùng chatbot

## Về tính năng lưu nhiều cuộc trò chuyện (giống Claude/ChatGPT)

- Mỗi cuộc trò chuyện được lưu vào file **`chat_sessions.db`** (tự động tạo trong folder project, dùng SQLite — khác hoàn toàn với vector database `chroma_db`)
- Lịch sử **lưu vĩnh viễn**: tắt Streamlit, tắt máy, mở lại vẫn còn nguyên
- Sidebar bên trái hiển thị danh sách cuộc trò chuyện, sắp xếp theo lần dùng gần nhất, có nút **➕ tạo mới** và **🗑️ xoá**
- Tên cuộc trò chuyện được **tự đặt theo câu hỏi đầu tiên** bạn gửi trong session đó

**Muốn xoá hết lịch sử chat để làm lại từ đầu?** Đóng Streamlit lại, xoá file `chat_sessions.db` trong folder project, rồi chạy lại `streamlit run app.py` — file sẽ tự được tạo mới, rỗng.
