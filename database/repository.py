import sqlite3
import json
from datetime import datetime

def insert_person(conn, person_id, canonical_name, normalized_name, 
                  canonical_email, normalized_email, canonical_phone, 
                  normalized_phone, canonical_city, experience_years, annual_ctc_inr):
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    
    # Check if person already exists to update or insert
    cursor.execute("SELECT id FROM people WHERE id = ?", (person_id,))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
            UPDATE people 
            SET canonical_name = ?, normalized_name = ?, 
                canonical_email = ?, normalized_email = ?, 
                canonical_phone = ?, normalized_phone = ?, 
                canonical_city = ?, experience_years = ?, 
                annual_ctc_inr = ?, updated_at = ?
            WHERE id = ?
        """, (canonical_name, normalized_name, canonical_email, normalized_email,
              canonical_phone, normalized_phone, canonical_city, experience_years,
              annual_ctc_inr, now_str, person_id))
    else:
        cursor.execute("""
            INSERT INTO people (
                id, canonical_name, normalized_name, canonical_email, 
                normalized_email, canonical_phone, normalized_phone, 
                canonical_city, experience_years, annual_ctc_inr, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (person_id, canonical_name, normalized_name, canonical_email,
              normalized_email, canonical_phone, normalized_phone,
              canonical_city, experience_years, annual_ctc_inr, now_str, now_str))

def insert_source_record(conn, person_id, source_name, source_row_number,
                         raw_name, normalized_name, raw_email, normalized_email,
                         raw_phone, normalized_phone, raw_city, normalized_city,
                         raw_data_json, match_decision, match_confidence,
                         match_type, match_reason):
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO source_records (
            person_id, source_name, source_row_number, raw_name, 
            normalized_name, raw_email, normalized_email, raw_phone, 
            normalized_phone, raw_city, normalized_city, raw_data_json, 
            match_decision, match_confidence, match_type, match_reason, 
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (person_id, source_name, source_row_number, raw_name,
          normalized_name, raw_email, normalized_email, raw_phone,
          normalized_phone, raw_city, normalized_city, raw_data_json,
          match_decision, match_confidence, match_type, match_reason, now_str))
    
    return cursor.lastrowid

def insert_gig_worker_profile(conn, person_id, source_record_id,
                             rate_amount, rate_period, status, skill_tags):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO gig_worker_profiles (
            person_id, source_record_id, rate_amount, rate_period, status, skill_tags
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (person_id, source_record_id, rate_amount, rate_period, status, skill_tags))

def insert_cbnexus_profile(conn, person_id, source_record_id,
                           verified, projects_completed):
    cursor = conn.cursor()
    # verified should be integer (1 for True, 0 for False, NULL if None)
    v_int = 1 if verified is True else (0 if verified is False else None)
    
    cursor.execute("""
        INSERT INTO cbnexus_profiles (
            person_id, source_record_id, verified, projects_completed
        ) VALUES (?, ?, ?, ?)
    """, (person_id, source_record_id, v_int, projects_completed))

def insert_match_review(conn, source_record_id, candidate_person_id,
                        confidence, match_type, reason):
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO match_reviews (
            source_record_id, candidate_person_id, confidence, 
            match_type, reason, status, created_at
        ) VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
    """, (source_record_id, candidate_person_id, confidence,
          match_type, reason, now_str))
