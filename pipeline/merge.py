import json
from pipeline.loaders import load_source1, load_source2, load_source3
from pipeline.normalize import (
    normalize_name, normalize_email, normalize_phone, normalize_city,
    normalize_status, normalize_verified, parse_naukri_ctc, parse_gig_rate, parse_date
)
from pipeline.matching import EntityResolver
from database.repository import (
    insert_person, insert_source_record, insert_gig_worker_profile,
    insert_cbnexus_profile, insert_match_review
)

def run_merge_pipeline(conn, s1_path, s2_path, s3_path):
    # Load all records
    s1_records = load_source1(s1_path)
    s2_records = load_source2(s2_path)
    s3_records = load_source3(s3_path)
    
    all_records = s1_records + s2_records + s3_records
    
    resolver = EntityResolver()
    
    # Track metrics for merge summary
    confirmed_match = 0
    confirmed_new = 0
    review_count = 0
    
    # Process all records sequentially
    for record in all_records:
        decision_info = resolver.add_record(record)
        decision = decision_info["decision"]
        assigned_pid = decision_info["assigned_person_id"]
        
        # Extract normalization fields
        raw_name = record["data"].get("name", "")
        raw_email = record["data"].get("email", "")
        raw_phone = record["data"].get("phone", "")
        raw_city = record["data"].get("city", "")
        
        n_name = normalize_name(raw_name)
        n_email = normalize_email(raw_email)
        n_phone = normalize_phone(raw_phone)
        n_city = normalize_city(raw_city)
        
        # Serialize raw data for JSON field
        raw_json = json.dumps(record["data"])
        
        if decision == "MATCH":
            confirmed_match += 1
        elif decision == "NEW_PERSON":
            confirmed_new += 1
        elif decision == "REVIEW":
            review_count += 1
            
        # 1. Update/Insert into people table if resolved
        if assigned_pid:
            # Find the CanonicalPerson from resolver
            person = next(p for p in resolver.persons if p.person_id == assigned_pid)
            
            # Compute canonical attributes dynamically from all records in the person
            c_name = raw_name
            c_email = None
            c_phone = None
            c_city = None
            max_exp = 0.0
            max_ctc = 0.0
            
            for r in person.records:
                r_name = r["data"].get("name", "")
                r_email = r["data"].get("email", "")
                r_phone = r["data"].get("phone", "")
                r_city = r["data"].get("city", "")
                
                if r_name and not c_name:
                    c_name = r_name
                if r_email and not c_email:
                    c_email = r_email
                if r_phone and not c_phone:
                    c_phone = r_phone
                if r_city and not c_city:
                    c_city = r_city
                    
                # Calculate max experience
                exp_val = r["data"].get("experience", "")
                if exp_val:
                    try:
                        max_exp = max(max_exp, float(exp_val))
                    except ValueError:
                        pass
                
                # Calculate max CTC (from Source 1 only)
                ctc_val = r["data"].get("ctc", "")
                if ctc_val:
                    parsed_ctc = parse_naukri_ctc(ctc_val)["normalized_inr"]
                    if parsed_ctc:
                        max_ctc = max(max_ctc, parsed_ctc)
                        
            insert_person(
                conn,
                person.person_id,
                canonical_name=c_name,
                normalized_name=normalize_name(c_name),
                canonical_email=c_email,
                normalized_email=normalize_email(c_email),
                canonical_phone=c_phone,
                normalized_phone=normalize_phone(c_phone),
                canonical_city=c_city,
                experience_years=max_exp if max_exp > 0 else None,
                annual_ctc_inr=max_ctc if max_ctc > 0 else None
            )
            
        # 2. Insert into source_records
        src_rec_id = insert_source_record(
            conn,
            person_id=assigned_pid,
            source_name=record["source"],
            source_row_number=record["line_number"],
            raw_name=raw_name,
            normalized_name=n_name,
            raw_email=raw_email,
            normalized_email=n_email,
            raw_phone=raw_phone,
            normalized_phone=n_phone,
            raw_city=raw_city,
            normalized_city=n_city,
            raw_data_json=raw_json,
            match_decision=decision,
            match_confidence=decision_info["confidence"],
            match_type=decision_info["match_type"],
            match_reason=decision_info["reason"]
        )
        
        # 3. Handle REVIEW match_reviews table
        if decision == "REVIEW":
            insert_match_review(
                conn,
                source_record_id=src_rec_id,
                candidate_person_id=decision_info["candidate_person_id"],
                confidence=decision_info["confidence"],
                match_type=decision_info["match_type"],
                reason=decision_info["reason"]
            )
            
        # 4. Ingest extra profile tables (if linked to a confirmed person)
        if assigned_pid:
            if record["source"] == "source2_gig_workers.csv":
                rate_val = record["data"].get("rate", "")
                parsed_rate = parse_gig_rate(rate_val)
                status_val = normalize_status(record["data"].get("status", ""))
                skills_val = record["data"].get("skills", "")
                
                insert_gig_worker_profile(
                    conn,
                    person_id=assigned_pid,
                    source_record_id=src_rec_id,
                    rate_amount=parsed_rate["rate"],
                    rate_period=parsed_rate["unit"],
                    status=status_val,
                    skill_tags=skills_val
                )
                
            elif record["source"] == "source3_cbnexus_contacts.csv":
                verified_val = normalize_verified(record["data"].get("verified", ""))
                
                proj_val = record["data"].get("projects_completed", "")
                try:
                    projects = int(proj_val)
                except ValueError:
                    projects = 0
                    
                insert_cbnexus_profile(
                    conn,
                    person_id=assigned_pid,
                    source_record_id=src_rec_id,
                    verified=verified_val,
                    projects_completed=projects
                )
                
    # Calculate source-level duplicate metrics
    source_level_dupes = 0
    for person in resolver.persons:
        file_records = {}
        for r in person.records:
            file_records.setdefault(r["source"], []).append(r)
        for src, recs in file_records.items():
            if len(recs) > 1:
                source_level_dupes += (len(recs) - 1)
                
    return {
        "s1_rows": len(s1_records),
        "s2_rows": len(s2_records),
        "s3_rows": len(s3_records),
        "total_rows": len(all_records),
        "confirmed_people": len([p for p in resolver.persons if len(p.records) > 0]),
        "confirmed_match": confirmed_match,
        "confirmed_new": confirmed_new,
        "review_records": review_count,
        "linked_rows": sum(1 for a in all_records if any(p for p in resolver.persons if record in p.records)), # wait, let's keep it simple: total - review
        "source_level_duplicates": source_level_dupes,
        "resolver": resolver
    }
