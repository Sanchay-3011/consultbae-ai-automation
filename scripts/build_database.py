import os
import sys
import sqlite3

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.migrate import init_db, get_connection
from pipeline.merge import run_merge_pipeline

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(base_dir, "data")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "consultbae.db")
    
    s1_path = os.path.join(base_dir, "data", "source1_naukri_applicants.csv")
    s2_path = os.path.join(base_dir, "data", "source2_gig_workers.csv")
    s3_path = os.path.join(base_dir, "data", "source3_cbnexus_contacts.csv")
    
    # 1. Initialize schema
    init_db(db_path)
    
    # 2. Open connection and execute inside a transaction
    conn = get_connection(db_path)
    try:
        summary = run_merge_pipeline(conn, s1_path, s2_path, s3_path)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error running pipeline, rolled back transaction: {e}")
        raise e
    finally:
        conn.close()
        
    resolver = summary["resolver"]
    
    # Calculate represented source counts
    two_plus_sources = 0
    three_sources = 0
    for person in resolver.persons:
        sources = set(r["source"] for r in person.records)
        if len(sources) >= 2:
            two_plus_sources += 1
        if len(sources) == 3:
            three_sources += 1
            
    linked_rows = summary["total_rows"] - summary["review_records"]
    
    # Print Merge Summary
    print("\n" + "=" * 50)
    print("MERGE PIPELINE SUMMARY")
    print("=" * 50)
    print(f"Source 1 rows: {summary['s1_rows']}")
    print(f"Source 2 rows: {summary['s2_rows']}")
    print(f"Source 3 rows: {summary['s3_rows']}")
    print(f"Total source rows: {summary['total_rows']}")
    print()
    print(f"Confirmed canonical people: {summary['confirmed_people']}")
    print(f"Confirmed MATCH records: {summary['confirmed_match']}")
    print(f"Confirmed NEW_PERSON records: {summary['confirmed_new']}")
    print(f"REVIEW records: {summary['review_records']}")
    print(f"Source rows linked to canonical people: {linked_rows}")
    print(f"Source rows pending review: {summary['review_records']}")
    print()
    print(f"People represented in 2+ sources: {two_plus_sources}")
    print(f"People represented in all 3 sources: {three_sources}")
    print()
    print(f"Source-level duplicates detected: {summary['source_level_duplicates']}")
    print()
    print(f"Database path: {db_path}")
    print("=" * 50)

if __name__ == '__main__':
    main()
