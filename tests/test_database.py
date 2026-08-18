import pytest
import sqlite3
import os
import json
from database.migrate import init_db, get_connection
from database.repository import (
    insert_person, insert_source_record, insert_gig_worker_profile,
    insert_cbnexus_profile, insert_match_review
)
from pipeline.merge import run_merge_pipeline

@pytest.fixture
def temp_db():
    db_path = "test_consultbae.db"
    # Recreate clean schema
    init_db(db_path)
    conn = get_connection(db_path)
    yield conn
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

def test_schema_creation(temp_db):
    cursor = temp_db.cursor()
    # Check that tables exist
    tables = ["people", "source_records", "gig_worker_profiles", "cbnexus_profiles", "match_reviews"]
    for table in tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        assert cursor.fetchone() is not None

def test_foreign_keys(temp_db):
    cursor = temp_db.cursor()
    # Insert source record referencing non-existent person ID should fail if FK is active
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO source_records (
                person_id, source_name, source_row_number, raw_data_json, match_decision, created_at
            ) VALUES ('P999', 'source1.csv', 10, '{}', 'MATCH', '2026-08-18')
        """)

def test_source_record_preservation(temp_db):
    insert_person(
        temp_db, "P001", "Tanvi Gupta", "tanvi gupta",
        "tanvi@example.com", "tanvi@example.com", "9000000254", "9000000254", "Bengaluru", 4.2, 420000.0
    )
    src_id = insert_source_record(
        temp_db, "P001", "source1.csv", 2, "Tanvi Gupta", "tanvi gupta",
        "tanvi@example.com", "tanvi@example.com", "9000000254", "9000000254", "Bengaluru", "bengaluru",
        '{"test": 1}', "MATCH", "HIGH", "email", "Exact match"
    )
    assert src_id is not None
    cursor = temp_db.cursor()
    cursor.execute("SELECT person_id, source_name, raw_data_json FROM source_records WHERE id=?", (src_id,))
    row = cursor.fetchone()
    assert row[0] == "P001"
    assert row[1] == "source1.csv"
    assert json.loads(row[2]) == {"test": 1}

def test_confirmed_match_creates_one_person(temp_db):
    # If we run the pipeline, MATCH should update/use existing person ID.
    # We can test this by running a mock or mini pipeline.
    # Let's test by manually calling insert_person on same ID
    insert_person(temp_db, "P001", "Tanvi Gupta", "tanvi gupta", None, None, None, None, None, None, None)
    insert_person(temp_db, "P001", "Tanvi Gupta", "tanvi gupta", "tanvi@example.com", "tanvi@example.com", None, None, None, None, None)
    
    cursor = temp_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM people")
    assert cursor.fetchone()[0] == 1

def test_new_person_creates_one_person(temp_db):
    insert_person(temp_db, "P001", "Tanvi Gupta", "tanvi gupta", None, None, None, None, None, None, None)
    insert_person(temp_db, "P002", "Varun Jain", "varun jain", None, None, None, None, None, None, None)
    
    cursor = temp_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM people")
    assert cursor.fetchone()[0] == 2

def test_review_does_not_create_a_person(temp_db):
    # Insert source record with person_id = NULL (REVIEW)
    src_id = insert_source_record(
        temp_db, None, "source1.csv", 2, "Tanvi Gupta", "tanvi gupta",
        None, None, None, None, None, None,
        '{}', "REVIEW", "LOW", "name_only", "No email/phone"
    )
    insert_match_review(temp_db, src_id, None, "LOW", "name_only", "No email/phone")
    
    cursor = temp_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM people")
    assert cursor.fetchone()[0] == 0
    
    cursor.execute("SELECT COUNT(*) FROM match_reviews")
    assert cursor.fetchone()[0] == 1

def test_duplicate_source_row_handling(temp_db):
    # UNIQUE constraint on (source_name, source_row_number)
    insert_source_record(
        temp_db, None, "source1.csv", 2, "Tanvi Gupta", "tanvi gupta",
        None, None, None, None, None, None, '{}', "NEW_PERSON", "LOW", "", ""
    )
    with pytest.raises(sqlite3.IntegrityError):
        insert_source_record(
            temp_db, None, "source1.csv", 2, "Tanvi Gupta Duplicate", "tanvi gupta",
            None, None, None, None, None, None, '{}', "NEW_PERSON", "LOW", "", ""
        )

def test_conflicting_identifiers_remain_in_source_records(temp_db):
    # Create canonical person
    insert_person(temp_db, "P001", "Arjun Mehta", "arjun mehta", "arjun.mehta9@example.in", "arjun.mehta9@example.in", None, None, None, None, None)
    
    # Store conflicting record: email is arjun.mehta77@mailtest.example.org (different), decision REVIEW
    src_id = insert_source_record(
        temp_db, None, "source2.csv", 18, "Arjun Mehta", "arjun mehta",
        "arjun.mehta77@mailtest.example.org", "arjun.mehta77@mailtest.example.org", None, None, None, None,
        '{}', "REVIEW", "LOW", "conflict", "Email conflict"
    )
    
    # Conflicting email should NOT overwrite P001 canonical email
    cursor = temp_db.cursor()
    cursor.execute("SELECT canonical_email FROM people WHERE id='P001'")
    assert cursor.fetchone()[0] == "arjun.mehta9@example.in"
    
    # But remains in source_records
    cursor.execute("SELECT raw_email FROM source_records WHERE id=?", (src_id,))
    assert cursor.fetchone()[0] == "arjun.mehta77@mailtest.example.org"
