import sqlite3
from datetime import datetime
from database.schema import CREATE_AUDIO_SUBMISSIONS_TABLE

def initialize_audio_table(db_path):
    """
    Ensures the audio_submissions table is created in the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute(CREATE_AUDIO_SUBMISSIONS_TABLE)
    conn.commit()
    conn.close()

def save_audio_submission(db_path, person_id, submitted_name, normalized_name,
                          submitted_phone, normalized_phone, file_path,
                          original_filename, mime_type, file_size_bytes,
                          duration_seconds, sample_rate_khz, bitrate_kbps,
                          loudness_db, noise_level_db=None, quality_score=None,
                          quality_label=None, match_status="unmatched"):
    """
    Saves metadata of an audio submission to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    now_str = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO audio_submissions (
            person_id, submitted_name, normalized_name, submitted_phone,
            normalized_phone, file_path, original_filename, mime_type,
            file_size_bytes, duration_seconds, sample_rate_khz, bitrate_kbps,
            loudness_db, noise_level_db, quality_score, quality_label,
            match_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (person_id, submitted_name, normalized_name, submitted_phone,
          normalized_phone, file_path, original_filename, mime_type,
          file_size_bytes, duration_seconds, sample_rate_khz, bitrate_kbps,
          loudness_db, noise_level_db, quality_score, quality_label,
          match_status, now_str))
          
    conn.commit()
    conn.close()

def get_audio_submissions(db_path):
    """
    Retrieves all audio submissions from the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, person_id, submitted_name, normalized_name, submitted_phone,
               normalized_phone, file_path, original_filename, mime_type,
               file_size_bytes, duration_seconds, sample_rate_khz, bitrate_kbps,
               loudness_db, noise_level_db, quality_score, quality_label,
               match_status, created_at
        FROM audio_submissions
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    submissions = []
    for r in rows:
        submissions.append({
            "id": r[0],
            "person_id": r[1],
            "submitted_name": r[2],
            "normalized_name": r[3],
            "submitted_phone": r[4],
            "normalized_phone": r[5],
            "file_path": r[6],
            "original_filename": r[7],
            "mime_type": r[8],
            "file_size_bytes": r[9],
            "duration_seconds": r[10],
            "sample_rate_khz": r[11],
            "bitrate_kbps": r[12],
            "loudness_db": r[13],
            "noise_level_db": r[14],
            "quality_score": r[15],
            "quality_label": r[16],
            "match_status": r[17],
            "created_at": r[18]
        })
    return submissions
