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

### 📈 Part 4: Data Quality Profiling & Auditing Reports
- **Data Profiler**: Programmatically generates missing-value counts, CTC formats, phone distribution, and near-duplicates.
- **Auditing Tool**: Generates a complete record resolution summary and stores it in `matching_report.txt`.

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

---

## 📈 Part 5: Scalability & Design for 5,000+ Workers

If the system scales to 5,000+ concurrent workers submitting audio:
1.  **Audio Processing Queues**: Move audio analysis off the web server onto asynchronous worker tasks using Celery or RQ, backed by Redis.
2.  **Object Storage**: Transition from storing audio files in the local filesystem to using cloud-native storage like AWS S3 or Google Cloud Storage, with CDN delivery for playback.
3.  **Database Scaling**: Migrate from SQLite to a highly concurrent relational database like PostgreSQL. Index columns like `normalized_phone` and `normalized_email` to ensure sub-millisecond query performance during entity resolution.
4.  **Audio Pre-compression**: Compress audio client-side (e.g. to MP3 or OGG/Opus) prior to upload to optimize bandwidth and network utilization.
