import os
import sys
import sqlite3

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "consultbae.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE INSPECTION")
    print("=" * 60)
    
    # Table counts
    tables = ["people", "source_records", "gig_worker_profiles", "cbnexus_profiles", "match_reviews", "audio_submissions"]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Table '{table}' row count: {count}")
        
    # Sample Canonical People
    print("\nSample Canonical People (First 3):")
    cursor.execute("SELECT id, canonical_name, canonical_email, canonical_phone, annual_ctc_inr FROM people LIMIT 3")
    for row in cursor.fetchall():
        print(f"  ID: {row[0]} | Name: {row[1]} | Email: {row[2]} | Phone: {row[3]} | CTC: {row[4]}")
        
    # Match Reviews
    print("\nPending Match Reviews:")
    cursor.execute("""
        SELECT r.id, r.candidate_person_id, s.source_name, s.source_row_number, s.raw_name, r.match_type, r.reason 
        FROM match_reviews r
        JOIN source_records s ON r.source_record_id = s.id
        WHERE r.status = 'PENDING'
    """)
    for row in cursor.fetchall():
        print(f"  ReviewID: {row[0]} | Candidate: {row[1]} | Src: {row[2]} (Line {row[3]}) | Name: {row[4]} | MatchType: {row[5]} | Reason: {row[6]}")
        
    conn.close()

if __name__ == '__main__':
    main()
