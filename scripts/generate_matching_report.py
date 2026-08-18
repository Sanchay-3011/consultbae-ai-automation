import os
import sys

# Ensure project root is in path for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.loaders import load_source1, load_source2, load_source3
from pipeline.normalize import normalize_name, normalize_email, normalize_phone
from pipeline.matching import EntityResolver, are_names_compatible

def generate_report():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s1_path = os.path.join(base_dir, "data", "source1_naukri_applicants.csv")
    s2_path = os.path.join(base_dir, "data", "source2_gig_workers.csv")
    s3_path = os.path.join(base_dir, "data", "source3_cbnexus_contacts.csv")
    
    # Load all records
    s1_records = load_source1(s1_path)
    s2_records = load_source2(s2_path)
    s3_records = load_source3(s3_path)
    
    all_records = s1_records + s2_records + s3_records
    
    resolver = EntityResolver()
    audit_trail = []
    
    # Resolve all records
    for rec in all_records:
        decision_info = resolver.add_record(rec)
        
        audit_trail.append({
            "source": rec["source"],
            "line_number": rec["line_number"],
            "orig_name": rec["data"].get("name", ""),
            "norm_name": normalize_name(rec["data"].get("name", "")),
            "orig_email": rec["data"].get("email", ""),
            "norm_email": normalize_email(rec["data"].get("email", "")),
            "orig_phone": rec["data"].get("phone", ""),
            "norm_phone": normalize_phone(rec["data"].get("phone", "")),
            "decision": decision_info["decision"],
            "assigned_person_id": decision_info["assigned_person_id"],
            "confidence": decision_info["confidence"],
            "match_type": decision_info["match_type"],
            "reason": decision_info["reason"]
        })
        
    # Open report file
    report_path = os.path.join(base_dir, "matching_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        
        def log(msg):
            print(msg)
            f.write(msg + "\n")
            
        log("=" * 80)
        log("CONSULTBAE ENTITY RESOLUTION AUDIT REPORT")
        log("=" * 80)
        
        # 1. Individual Record Audit
        log("\n--- PART 1: INDIVIDUAL RECORD AUDIT TRAIL ---")
        for a in audit_trail:
            log(f"Rec: {a['source']} | Line {a['line_number']} | Assigned ID: {a['assigned_person_id']}")
            log(f"  Name: '{a['orig_name']}' -> '{a['norm_name']}'")
            log(f"  Email: '{a['orig_email']}' -> '{a['norm_email']}'")
            log(f"  Phone: '{a['orig_phone']}' -> '{a['norm_phone']}'")
            log(f"  Decision: {a['decision']} | Confidence: {a['confidence']} | Type: {a['match_type']}")
            log(f"  Reason: {a['reason']}")
            log("-" * 60)
            
        # Summary Statistics Calculations
        total_source = len(all_records)
        s1_count = len(s1_records)
        s2_count = len(s2_records)
        s3_count = len(s3_records)
        
        match_count = sum(1 for a in audit_trail if a["decision"] == "MATCH")
        new_person_count = sum(1 for a in audit_trail if a["decision"] == "NEW_PERSON")
        review_count = sum(1 for a in audit_trail if a["decision"] == "REVIEW")
        
        num_canonical = len(resolver.persons)
        
        # Calculate represented sources per person
        two_plus_sources = 0
        three_sources = 0
        multi_source_people = []
        multi_email_people = []
        multi_phone_people = []
        
        for person in resolver.persons:
            sources = set(r["source"] for r in person.records)
            if len(sources) >= 2:
                two_plus_sources += 1
                multi_source_people.append(person)
            if len(sources) == 3:
                three_sources += 1
                
            if len(person.emails) > 1:
                multi_email_people.append(person)
            if len(person.phones) > 1:
                multi_phone_people.append(person)
                
        # Log Summary statistics
        log("\n" + "=" * 80)
        log("SUMMARY STATISTICS")
        log("=" * 80)
        log(f"1. Total source records: {total_source}")
        log(f"2. Source 1 record count: {s1_count}")
        log(f"3. Source 2 record count: {s2_count}")
        log(f"4. Source 3 record count: {s3_count}")
        log(f"5. MATCH count: {match_count}")
        log(f"6. NEW_PERSON count: {new_person_count}")
        log(f"7. REVIEW count: {review_count}")
        log(f"8. Number of canonical people: {num_canonical}")
        log(f"9. Number of canonical people represented in 2+ sources: {two_plus_sources}")
        log(f"10. Number of canonical people represented in all 3 sources: {three_sources}")
        
        # A. All REVIEW records
        log("\n" + "=" * 80)
        log("A. ALL REVIEW RECORDS")
        log("=" * 80)
        review_records = [a for a in audit_trail if a["decision"] == "REVIEW"]
        for r in review_records:
            log(f"ID: {r['assigned_person_id']} | Source: {r['source']} (Line {r['line_number']})")
            log(f"  Name: '{r['orig_name']}' | Email: '{r['orig_email']}' | Phone: '{r['orig_phone']}'")
            log(f"  Match Type: {r['match_type']} | Reason: {r['reason']}")
            log("-" * 60)
            
        # B. Conflicting strong identifiers
        log("\n" + "=" * 80)
        log("B. ALL RECORDS WITH CONFLICTING STRONG IDENTIFIERS")
        log("=" * 80)
        conflict_records = [a for a in audit_trail if a["match_type"] in ("conflict", "identifier_conflict")]
        for r in conflict_records:
            log(f"ID: {r['assigned_person_id']} | Source: {r['source']} (Line {r['line_number']})")
            log(f"  Name: '{r['orig_name']}' | Email: '{r['orig_email']}' | Phone: '{r['orig_phone']}'")
            log(f"  Reason: {r['reason']}")
            log("-" * 60)
            
        # C. Canonical people with more than one email
        log("\n" + "=" * 80)
        log("C. CANONICAL PEOPLE WITH MORE THAN ONE EMAIL")
        log("=" * 80)
        for p in multi_email_people:
            log(f"Person ID: {p.person_id} | Names: {list(p.names)}")
            log(f"  Emails: {list(p.emails)}")
            log(f"  Matched records: {[(r['source'], r['line_number']) for r in p.records]}")
            log("-" * 60)
            
        # D. Canonical people with more than one phone
        log("\n" + "=" * 80)
        log("D. CANONICAL PEOPLE WITH MORE THAN ONE PHONE")
        log("=" * 80)
        for p in multi_phone_people:
            log(f"Person ID: {p.person_id} | Names: {list(p.names)}")
            log(f"  Phones: {list(p.phones)}")
            log(f"  Matched records: {[(r['source'], r['line_number']) for r in p.records]}")
            log("-" * 60)
            
        # E. Canonical people containing records from multiple sources
        log("\n" + "=" * 80)
        log("E. CANONICAL PEOPLE CONTAINING RECORDS FROM MULTIPLE SOURCES")
        log("=" * 80)
        for p in multi_source_people:
            sources_present = sorted(list(set(r["source"] for r in p.records)))
            log(f"Person ID: {p.person_id} | Names: {list(p.names)}")
            log(f"  Sources: {sources_present}")
            log(f"  Records: {[(r['source'], r['line_number'], r['data'].get('name')) for r in p.records]}")
            log("-" * 60)
            
        # F. Source-level duplicates / suspicious duplicates
        log("\n" + "=" * 80)
        log("F. SOURCE-LEVEL DUPLICATES / SUSPICIOUS DUPLICATES")
        log("=" * 80)
        
        # We search for records in the same file that resolve to the same person, or share identifiers
        # E.g. Same source file, resolved to the same CanonicalPerson ID
        for p in resolver.persons:
            file_records = {}
            for r in p.records:
                file_records.setdefault(r["source"], []).append(r)
            for src, recs in file_records.items():
                if len(recs) > 1:
                    log(f"Suspicious duplicate in {src} grouped under Canonical ID: {p.person_id}")
                    for r in recs:
                        log(f"  Line {r['line_number']}: Name: '{r['data'].get('name')}', Email: '{r['data'].get('email')}', Phone: '{r['data'].get('phone')}'")
                    log("-" * 60)

if __name__ == '__main__':
    generate_report()
