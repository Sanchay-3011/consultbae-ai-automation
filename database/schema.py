# DDL schemas for ConsultBae database

CREATE_PEOPLE_TABLE = """
CREATE TABLE IF NOT EXISTS people (
    id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    canonical_email TEXT,
    normalized_email TEXT,
    canonical_phone TEXT,
    normalized_phone TEXT,
    canonical_city TEXT,
    experience_years REAL,
    annual_ctc_inr REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_SOURCE_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS source_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NULL,
    source_name TEXT NOT NULL,
    source_row_number INTEGER NOT NULL,
    raw_name TEXT,
    normalized_name TEXT,
    raw_email TEXT,
    normalized_email TEXT,
    raw_phone TEXT,
    normalized_phone TEXT,
    raw_city TEXT,
    normalized_city TEXT,
    raw_data_json TEXT NOT NULL,
    match_decision TEXT NOT NULL,
    match_confidence TEXT,
    match_type TEXT,
    match_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(person_id) REFERENCES people(id),
    UNIQUE(source_name, source_row_number)
);
"""

CREATE_GIG_WORKER_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS gig_worker_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    source_record_id INTEGER NOT NULL,
    rate_amount REAL,
    rate_period TEXT,
    status TEXT,
    skill_tags TEXT,
    skill_category TEXT,
    FOREIGN KEY(person_id) REFERENCES people(id),
    FOREIGN KEY(source_record_id) REFERENCES source_records(id)
);
"""

CREATE_CBNEXUS_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS cbnexus_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    source_record_id INTEGER NOT NULL,
    verified INTEGER,
    projects_completed INTEGER,
    FOREIGN KEY(person_id) REFERENCES people(id),
    FOREIGN KEY(source_record_id) REFERENCES source_records(id)
);
"""

CREATE_MATCH_REVIEWS_TABLE = """
CREATE TABLE IF NOT EXISTS match_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_record_id INTEGER NOT NULL,
    candidate_person_id TEXT,
    decision TEXT NOT NULL DEFAULT 'REVIEW',
    confidence TEXT,
    match_type TEXT,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    FOREIGN KEY(source_record_id) REFERENCES source_records(id),
    FOREIGN KEY(candidate_person_id) REFERENCES people(id)
);
"""

CREATE_AUDIO_SUBMISSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS audio_submissions (
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
"""

