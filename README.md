# ConsultBae AI Automation Take-Home Assignment

This repository contains the solution for the ConsultBae AI Automation Take-Home Assignment. The project involves merging three messy candidate/worker datasets, establishing entity resolution, building an n8n automation workflow, and building a mini audio collection web application.

## Current Status

**Task 3: Streamlit Audio Collection Application** is fully implemented and tested.

---

## Task 3 - Audio Collection Application

A lightweight web application built using **Streamlit** to collect, analyze, validate, and store worker voice submissions.

### How to Run the App

1.  Ensure all dependencies are installed:
    ```bash
    pip install -r requirements.txt
    ```
2.  Start the Streamlit application:
    ```bash
    streamlit run audio_app/app.py
    ```

### App Functionality & User Guide

1.  **Submit Audio View**:
    *   Enter the worker's **Name** and **Phone Number**.
    *   Either **Record audio** directly using the web browser recording widget (`st.audio_input`) or **Upload a WAV audio file** using the file uploader.
    *   If both inputs are provided, the browser recording is preferred.
    *   View file metadata (size, detected MIME type, filename) and preview/listen to the audio before submitting.
    *   Click **Submit Audio** to validate the fields, analyze quality, and save.
2.  **Submissions View**:
    *   View all historical audio submissions with details such as name, phone, canonical candidate link ID, metrics, and timestamp.
    *   Play back the saved audio files natively inside the browser via the embedded player.

### Audio Metadata & Quality Analysis Heuristics

*   **Duration**: Dynamically extracted from header properties of parsed WAV file frames.
*   **Sample Rate**: Extracted directly and represented in kHz (e.g. `16.0 kHz` or `44.1 kHz`).
*   **Bitrate**: Calculated using the raw WAV header parameters. Fallback formula is `(file_size_bytes * 8) / duration_seconds` if headers are unavailable.
*   **Loudness**: Calculated using the Root-Mean-Square (RMS) amplitude of all digitized samples and represented in decibels relative to full scale (**dBFS**). It is labeled as `loudness_db`.
*   **Noise Floor & Quality**: Estimated from the lowest-energy 50ms frames in the recording. SNR is calculated to grade the quality into `Clean/Excellent`, `Moderate/Good`, or `Noisy/Poor`.

### Matching & Data Integrity Rules

*   **Identity Verification**: Submissions are matched against the canonical database of merged candidates based on two criteria:
    1.  Exact matching of normalized phone number.
    2.  Compatibility validation of name using the `are_names_compatible` helper.
*   **Constraint Policy**: "Audio is linked only when the submitted name and normalized phone resolve to one canonical person. Ambiguous or unmatched submissions are preserved with person_id NULL rather than guessed."

### Storage and Database Schema

*   **File Storage**: Uploaded files are renamed using secure, randomly generated UUIDs (e.g., `5b3e648f-9a1c-42b7-84a1-7c9802d33abf.wav`) to prevent path traversal and collision. They are stored under [audio_app/storage/audio/](file:///c:/Users/roysa/OneDrive/Desktop/consultbae-ai-automation/audio_app/storage/audio/).
*   **Database Table**: Metadata is stored in SQLite under `audio_submissions`:
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
