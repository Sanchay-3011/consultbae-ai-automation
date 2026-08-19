# ConsultBae AI Automation Platform

An end-to-end data integration, identity resolution, audio analysis, and low-code skill categorization platform built for the ConsultBae AI Automation Take-Home Assignment.

---

## 🚀 Key Features

### 📊 Part 1: Dataset Merging & Entity Resolution
- **CSV Loaders**: Dynamically parses raw datasets, filtering out empty rows, correcting shifted columns (e.g. Source 2 Line 20), and filtering duplicate headers (e.g. Source 3 Line 16).
- **Deterministic Normalization**: Standardizes names, emails, phone numbers (handling `+91`, `91-`, leading `0`, and whitespace), cities (e.g. merging `Gurugram` and `Gurgaon`), and CTC values.
- **Confidence-Based Resolver**: Evaluates identity matches based on a hierarchy:
  - **HIGH**: Exact normalized email or phone match with no conflicts.
  - **MEDIUM**: Exact identifier match + compatible name.
  - **REVIEW**: Conflicting strong identifiers or name-only candidates. Kept unresolved and isolated in the database to prevent false-positives.

### 🤖 Part 2: Low-Code Automation Workflow (n8n + FastAPI)
- **FastAPI Core (`automation_api.py`)**: Exposes endpoints for managing gig worker profiles and updating AI skill categorization classifications.
- **n8n Workflow Integration**: Queries worker profiles, automatically evaluates skills, categorizes them into designated categories (e.g., `AI/ML`, `Software Development`), and synchronizes the categorization back to the database.

### 🎙️ Part 3: Streamlit Audio Collection Portal
- **Audio Submission**: Web portal for candidate voice recording (`st.audio_input`) or WAV uploads.
- **Audio Processing Heuristics**: Extracts actual duration, sample rate (kHz), bitrate, RMS dBFS loudness (`loudness_db`), noise floor (low-energy 50ms frames), and speech presence detection.
- **Candidate Linking**: Submissions are strictly verified against the database and linked to the canonical person ID only when the normalized phone and name uniquely resolve to a single person.

### 🔍 Part 4: Data Quality Issues Audit (ConsultBae_Task4_Data_Issues_Report.pdf)
- **Dataset Overview**: Ingested 103 raw rows (42 in Source 1, 31 in Source 2, 30 in Source 3) resolving to 53 canonical people, with 25 people in 2+ files and 15 in all three. 8 rows were flagged for manual review.
- **Source 1 Issues**:
  - *Phone Numbers*: Standardized from 4 formats (e.g. +91, leading 0, 10-digit) to a clean 10-digit string.
  - *Cities*: Standardized casing and mapped `Bangalore`/`Bengaluru` and `Gurgaon`/`Gurugram`. Kept `Delhi`, `New Delhi`, and `Delhi NCR` distinct as they do not affect matching.
  - *Current CTC*: Mixed units. Values < 100 are treated as LPA (multiplied by 100,000) while values >= 100 are treated as absolute INR.
  - *Applied Dates*: Standardized 4 formats into `YYYY-MM-DD` ISO format.
  - *Duplicates*: Merged shortened duplicate names (`R. Verma` vs `Rohit Verma` sharing email/phone) and flagged Nikhil Chopra's email conflict (same phone, different emails) for review.
- **Source 2 Issues**:
  - *Shifted Columns*: Shifted fields on Line 20 realigned (skills in email column, email in name, etc.) and merged with `Isha Chopra`.
  - *Rates*: Stored as separate amount and unit fields (`/hr` vs `/month`) to avoid making false hours-per-month conversions.
  - *Statuses & Casing*: Standardized cases; kept `paused` distinct from `inactive`.
- **Source 3 Issues**:
  - *Duplicate Header*: Line 16 repeated the header and was skipped.
  - *Verified Field*: Normalized variations (`Y`, `yes`, `No`, `N`, `Yes`) to Boolean `True`/`False`.
- **Cross-Source Challenges**:
  - *Same Name / Different People*: Names like `Arjun Mehta` and `Deepak Nair` appear multiple times with conflicting identifiers; resolved as separate canonical profiles or flagged as conflicts instead of incorrectly fusing them.
  - *No Shared Identifier*: Cases where candidates appear only in Source 2 (email-only) and Source 3 (phone-only) with matching names (e.g. `Manish Bhatia`, `Divya Chopra`, `Karan Chopra`, `Vikram Mehta`) are flagged for review.

### 📈 Part 5: Audio App Scaling Analysis (ConsultBae_Task5_Scale_Up_Analysis.pdf)
To scale the audio submission application to 5,000+ concurrent workers:
- **What Breaks First**:
  1. *SQLite Write Bottleneck*: SQLite allows only one writer at a time, resulting in connection timeouts under high concurrency.
  2. *Inline Processing Delay*: Running NumPy audio computations synchronously inside the request blocks server threads.
  3. *Local Storage Risks*: streamlit hosting filesystems do not persist across server restarts.
- **Core Scalability Recommendations**:
  *   **Object Storage (AWS S3)**: Move audio files directly to object storage immediately after upload.
  *   **PostgreSQL**: Replace SQLite with PostgreSQL to remove single-writer locks.
  *   **Decoupled Background Tasks**: Save uploaded audio files instantly and queue CPU-bound analysis to background worker processes (e.g. using Celery or RQ with Redis).
  *   **Idempotency & Retry**: Add duplicate checks per phone number and client-side upload retries for flaky connections.

---

## 🛠️ Getting Started

### 1. Installation
Install the necessary python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Build & Initialize the SQLite Database
Reset the database and execute the merge pipeline to ingest and resolve the CSV datasets:
```bash
python scripts/build_database.py
```

### 3. Run the Streamlit Audio Application
Start the Streamlit audio portal:
```bash
streamlit run audio_app/app.py
```

### 4. Run the Automation API
Start the local FastAPI server to expose endpoints for the n8n workflow:
```bash
uvicorn automation_api:app --reload
```

### 5. Running the Test Suite
Execute unit tests for normalization, entity resolution, database schemas, and audio processing:
```bash
pytest -q
```

---

## 🗄️ Database Schema & File Storage

*   **File Storage**: Uploaded files are renamed using secure, randomly generated UUIDs (e.g., `5b3e648f-9a1c-42b7-84a1-7c9802d33abf.wav`) to prevent path traversal and collision. They are stored under `audio_app/storage/audio/`.
*   **WAV Submissions Table**:
    ```sql
    CREATE TABLE audio_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT NULL,
        submitted_name TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        submitted_phone TEXT NOT NULL,
        normalized_phone TEXT NOT NULL,
        file_path TEXT NOT NULL,
        original_filename TEXT,
        mime_type TEXT,
        file_size_bytes INTEGER NOT NULL,
        duration_seconds REAL NOT NULL,
        sample_rate_khz REAL NOT NULL,
        bitrate_kbps REAL NOT NULL,
        loudness_db REAL NOT NULL,
        noise_level_db REAL,
        quality_score REAL,
        quality_label TEXT,
        match_status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (person_id) REFERENCES people(id)
    );
    ```
