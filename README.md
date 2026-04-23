# I Hate PDFs

An all-in-one Flask toolkit for working with PDFs and document files.

It provides:
- PDF merge and split
- PDF <-> DOCX conversion
- PDF and DOCX compression
- AI summarization and quiz generation from PDFs
- JPEG to PDF conversion
- JPEG <-> PNG image conversion

---

## Table of Contents

1. [How the App Works](#how-the-app-works)
2. [Feature Set](#feature-set)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Quick Start](#quick-start)
6. [Environment Variables](#environment-variables)
7. [HTTP/API Endpoints](#httpapi-endpoints)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Known Limitations](#known-limitations)

---

## How the App Works

The app is built with Flask and server-rendered templates.

- `app.py` creates the Flask app and initializes `TaskManager`.
- `routes/*` handles request/response logic for each tool.
- `core/*` contains reusable processing engines.
- `templates/*` + `static/*` provide the frontend UI and behavior.

### Processing model

- Synchronous flows:
  - Merge, split, convert, compress, and image conversion return files directly.
- Asynchronous flows:
  - Summarize and quiz run in background threads using `TaskManager`.
  - Frontend polls `/api/status/<task_id>` and fetches output via `/api/download/<task_id>`.

### Task lifecycle (summarize/quiz)

1. User uploads a PDF and submits.
2. A background task is created in memory with an ID.
3. UI polls for progress.
4. On completion, result is fetched once from download endpoint.
5. Task results auto-expire based on TTL.

---

## Feature Set

### 1) Merge PDFs
- Combines multiple PDFs into one.
- Requires at least 2 files.
- Route: `/merge`

### 2) Split PDF
- Splits by ranges (example: `1-3,5,8-10`).
- `force` mode splits every page into separate files.
- Single range returns one PDF; multiple ranges return ZIP.
- Route: `/split`

### 3) Convert
- PDF -> DOCX (using `pdf2docx`)
- DOCX -> PDF (using `python-docx` + `fpdf2`)
- Route: `/convert`

### 4) Compress
- PDF compression (Ghostscript-based presets: low/medium/high)
- DOCX compression (optimizes media inside `.docx` package)
- Current route-level limit: max 12 pages for both PDF and DOCX compression flows.
- Routes:
  - `/compress/pdf`
  - `/compress/docx`

### 5) AI Summarize
- Upload PDF and generate structured summary output.
- Uses local summarization (`sumy`) and optional Groq refinement.
- UI currently fixed to one summarize action (no engine toggle).
- Route: `/summarize`

### 6) Flashcards & Quiz
- Generates flashcards and MCQs from PDF text.
- Uses Groq model when API key is available.
- Route: `/quiz`

### 7) JPEG to PDF
- Converts one or multiple JPEG files into a single PDF.
- Batch limit: up to 30 images per request.
- Route: `/jpeg-to-pdf`

### 8) JPEG <-> PNG
- JPEG -> PNG and PNG -> JPEG conversion.
- Handles alpha-safe conversion for JPEG output by flattening transparency.
- Route: `/image-convert`

---

## Tech Stack

- Backend: Flask
- PDF engine: PyMuPDF (`fitz`)
- PDF->DOCX: `pdf2docx`
- DOCX handling: `python-docx`
- DOCX->PDF rendering: `fpdf2`
- NLP summarization: `sumy`, `nltk`
- AI provider: Groq API (`requests`)
- Image processing: Pillow
- Frontend: Jinja templates + vanilla JS + Tailwind CDN

---

## Project Structure

```text
.
├── app.py
├── config.py
├── core/
│   ├── pdf_engine.py
│   ├── docx_engine.py
│   ├── summarizer.py
│   ├── quiz_generator.py
│   ├── image_engine.py
│   └── task_manager.py
├── routes/
│   ├── main.py
│   ├── merge.py
│   ├── split.py
│   ├── convert.py
│   ├── compress.py
│   ├── summarize.py
│   ├── quiz.py
│   ├── jpeg_to_pdf.py
│   ├── image_convert.py
│   └── api.py
├── templates/
├── static/
├── test.py
└── requirements.txt
```

---

## Quick Start

### 1) Clone and create virtual environment

```bash
git clone <your-repo-url>
cd <repo-folder>
python3 -m venv venv
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Optional `.env` setup

Create a `.env` file in project root if you want to provide API keys or custom runtime settings.

### 4) Run the app

```bash
python app.py
```

Open: `http://localhost:5000`

---

## Environment Variables

Configured in `config.py`:

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | Recommended | `""` | Flask secret/session signing |
| `TASK_POOL_WORKERS` | No | `2` | Background worker threads |
| `TASK_TTL_SECONDS` | No | `900` | Task/result retention in memory |
| `GROQ_API_KEY` | Required for AI features | `""` | Enables Groq-backed summarize/quiz |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq summarize model |
| `API_SECRET_KEY` | No | `""` | Protects `/api/*` endpoints with Bearer auth |
| `API_RATE_LIMIT` | No | `30` | Requests/minute limit for API routes |
| `FLASK_DEBUG` | No | `0` | Debug mode (`1` to enable) |

---

## HTTP/API Endpoints

### UI routes
- `GET /` dashboard
- `GET|POST /merge/`
- `GET|POST /split/`
- `POST /split/info`
- `GET|POST /convert/`
- `POST /convert/docx-to-pdf`
- `GET|POST /compress/pdf`
- `GET|POST /compress/docx`
- `GET|POST /summarize/`
- `GET|POST /quiz/`
- `GET|POST /jpeg-to-pdf/`
- `GET|POST /image-convert/`

### API routes
- `GET /api/health`
- `GET /api/status/<task_id>`
- `GET /api/download/<task_id>`
- `POST /api/summarize`
- `POST /api/merge`

Notes:
- If `API_SECRET_KEY` is set, API routes require:
  - `Authorization: Bearer <API_SECRET_KEY>`
- Same-origin browser requests are allowed without bearer token.

---

## Testing

Run unit tests:

```bash
python -m unittest test.py
```

Current test coverage includes:
- Merge behavior
- Split behavior
- Text extraction
- JPEG -> PDF conversion
- JPEG <-> PNG conversion

---

## Deployment

### Option A: Vercel (current repo includes starter config)

Files already present:
- `api/index.py`
- `vercel.json`
- `.vercelignore`

Basic flow:
1. Push repo to GitHub.
2. Import project into Vercel.
3. Add env vars (`SECRET_KEY`, `GROQ_API_KEY`, etc).
4. Deploy.

### Option B: Traditional server (recommended for full parity)

Run with Gunicorn:

```bash
gunicorn -w 2 -b 0.0.0.0:5000 "app:create_app()"
```

Use Nginx/Caddy as reverse proxy in front of Gunicorn for production.

---

## Known Limitations

1. **Ghostscript dependency for PDF compression**
   - `compress_pdf()` calls `gs` binary.
   - Environment must have Ghostscript installed.

2. **Asynchronous task state is in-memory**
   - On process restart, running/completed task state is lost.
   - For horizontal scaling, replace with shared job backend (Redis/Celery/RQ).

3. **First-time NLP warm-up**
   - NLTK resources may download on first summarize call if absent.

4. **Vercel/serverless constraints**
   - Heavy document jobs may hit runtime/time limits.
   - External binaries (like `gs`) may need additional strategy or alternate hosting.
