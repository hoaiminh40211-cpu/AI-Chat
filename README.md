# RAG Chatbot Demo Setup Guide (Windows)

This guide is for beginners. Follow every step in order, don't skip any.

---

## Step 0: Check if Python is already installed

Open **PowerShell** (click Start, type "PowerShell", press Enter), then run:

```powershell
python --version
```

- If it shows `Python 3.10.x` or higher (3.10, 3.11, 3.12) → skip ahead to Step 1.
- If it shows an error like "python is not recognized" → install Python from https://www.python.org/downloads/
  - **Important during install**: check the box **"Add Python to PATH"** on the first screen of the installer, otherwise the commands below won't work.
  - After installing, **close and reopen PowerShell**, then re-run the check command above.

---

## Step 1: Copy all project files onto your machine

Create a folder somewhere easy to find, e.g. `C:\rag-chatbot-demo`, and copy all the prepared files into it. The folder structure should look like this:

```
rag-chatbot-demo/
├── data/
│   └── pdfs/              ← copy your PDF/Word files in here
├── app.py
├── document_processor.py
├── ingest.py
├── rag_chat.py
├── vector_store.py
├── requirements.txt
├── .env.example
└── README.md (this guide)
```

---

## Step 2: Open PowerShell in the project folder

The fastest way: open **File Explorer**, navigate to the `rag-chatbot-demo` folder, type `powershell` into the address bar (the path bar at the top), and press Enter. PowerShell will open directly in this folder.

Verify with:

```powershell
dir
```

You should see files like `app.py`, `requirements.txt`, etc.

---

## Step 3: Create a dedicated Python virtual environment

This is an **important** step — it keeps this project's libraries from conflicting with other software on your machine.

```powershell
python -m venv venv
```

This creates a `venv` folder containing a Python environment dedicated to this project. Once it's done, **activate** it:

```powershell
.\venv\Scripts\Activate
```

After running this, you should see `(venv)` at the start of the PowerShell prompt — this confirms the environment is active.

**Common error**: if PowerShell reports an "execution policy" error, run the following and then try activating again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Choose `Y` (Yes) when prompted to confirm.

> **Note**: every time you open a new PowerShell window to work on this project, you need to run `.\venv\Scripts\Activate` (Step 3) again before running any other Python commands.

---

## Step 4: Install the required libraries

Make sure `(venv)` is showing at the start of the prompt (activated in Step 3), then run:

```powershell
pip install -r requirements.txt
```

This automatically installs all required libraries (anthropic, chromadb, streamlit, etc.). This takes about **3-7 minutes** depending on your network speed, since some libraries are fairly large (sentence-transformers).

If the last line reads `Successfully installed ...` → the install succeeded.

---

## Step 5: Get and configure your Anthropic API key

1. If you don't have a key yet, follow the instructions to get one at console.anthropic.com (covered earlier in chat).
2. In the project folder, copy the `.env.example` file to a new file named `.env` (just rename it, dropping the `.example` part).
3. Open the `.env` file with Notepad and replace the line:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
   with your real key, for example:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
   ```
4. Save the file.

**Security note**: don't share this `.env` file with anyone, and don't post it online or send it in chat.

---

## Step 6: Copy your PDF/Word files into the right place

Copy the 5-10 PDF (or .docx) files you want to use for the demo into:

```
rag-chatbot-demo/data/pdfs/
```

---

## Step 7: Ingest documents into the vector database

Still in PowerShell (with venv activated), run:

```powershell
python ingest.py
```

- On the first run, the script will automatically **download the embedding model** (~80MB), which can take 1-2 minutes depending on your network.
- It then reads each file, splits it into chunks, and stores it in the vector database (the `chroma_db` folder will be created automatically).
- When finished, you'll see the line `✅ HOÀN TẤT` ("DONE").

**Every time you add new documents to the `data/pdfs` folder, re-run this command** to update the vector database.

---

## Step 8: Run the chatbot

```powershell
streamlit run app.py
```

This automatically opens a browser window with the chatbot at `http://localhost:8501`. If it doesn't open automatically, copy that address into your browser.

You can now chat and ask questions about the content of the PDF/Word files you ingested.

To stop the chatbot, go back to PowerShell and press `Ctrl + C`.

---

## Common issues

| Error | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'anthropic'` | venv not activated, or `pip install -r requirements.txt` not run yet | Redo Step 3 and Step 4 |
| `authentication_error` when chatting | Wrong API key, or no payment method added on console.anthropic.com | Check the `.env` file, check billing on the console |
| Vector DB reports 0 chunks | `python ingest.py` hasn't been run, or the PDF is a scanned image with no extractable text | Run `python ingest.py`, check whether the PDF is a scanned image |
| PowerShell "execution policy" error when activating venv | Windows blocks running scripts by default | Run the `Set-ExecutionPolicy` command from Step 3 |
| Chatbot replies "information not found" even though the document has it | The question is phrased very differently from the document, or the `DISTANCE_THRESHOLD` in `rag_chat.py` is too strict | Try rephrasing the question closer to the document's wording, or increase the `DISTANCE_THRESHOLD` value in `rag_chat.py` |

---

## Code structure, if you want to explore/modify it

- `document_processor.py` — reads PDF/Word files, splits them into chunks
- `vector_store.py` — embeds and stores/searches vectors in Chroma
- `ingest.py` — one-off script to ingest documents (re-run when there are new files)
- `rag_chat.py` — combines retrieval + calling Claude, with a system prompt that guards against making up information
- `chat_history.py` — manages storing conversations (sessions) in the `chat_sessions.db` file
- `inspect_db.py` — utility script to inspect what's been ingested into the vector DB
- `app.py` — multi-session Streamlit chat UI (similar to Claude/ChatGPT), this is the main file you run to use the chatbot

## About the multi-conversation history feature (similar to Claude/ChatGPT)

- Each conversation is stored in a **`chat_sessions.db`** file (created automatically in the project folder, using SQLite — completely separate from the `chroma_db` vector database)
- History is **saved permanently**: close Streamlit, restart your computer, reopen it — it's all still there
- The left sidebar shows the list of conversations, sorted by most recently used, with **➕ new** and **🗑️ delete** buttons
- Each conversation's name is **automatically set from the first question** you send in that session

**Want to clear all chat history and start fresh?** Close Streamlit, delete the `chat_sessions.db` file in the project folder, then run `streamlit run app.py` again — the file will be recreated automatically, empty.
