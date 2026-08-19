import sqlite3
from database.schema import (
    CREATE_PEOPLE_TABLE,
    CREATE_SOURCE_RECORDS_TABLE,
    CREATE_GIG_WORKER_PROFILES_TABLE,
    CREATE_CBNEXUS_PROFILES_TABLE,
    CREATE_MATCH_REVIEWS_TABLE,
    CREATE_AUDIO_SUBMISSIONS_TABLE
)

def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Enable foreign key verification
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Drop tables if we want clean state (for builds)
    # Ordered to avoid foreign key violations on drop
    tables_to_drop = [
        "audio_submissions",
        "match_reviews",
        "cbnexus_profiles",
        "gig_worker_profiles",
        "source_records",
        "people"
    ]
    
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
    # Create tables
    cursor.execute(CREATE_PEOPLE_TABLE)
    cursor.execute(CREATE_SOURCE_RECORDS_TABLE)
    cursor.execute(CREATE_GIG_WORKER_PROFILES_TABLE)
    cursor.execute(CREATE_CBNEXUS_PROFILES_TABLE)
    cursor.execute(CREATE_MATCH_REVIEWS_TABLE)
    cursor.execute(CREATE_AUDIO_SUBMISSIONS_TABLE)
    
    conn.commit()
    conn.close()
