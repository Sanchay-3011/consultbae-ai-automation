import sqlite3
from pipeline.normalize import normalize_name, normalize_phone
from pipeline.matching import are_names_compatible

def resolve_person(db_path, name, phone):
    """
    Resolves the submitted name and phone against the SQLite canonical people table.
    Matching rules:
    1. Exact normalized phone match.
    2. Verified compatible normalized name.
    
    If exactly one matches: returns (person_id, "matched")
    Otherwise returns (None, "unmatched")
    """
    n_name = normalize_name(name)
    n_phone = normalize_phone(phone)
    
    if not n_phone or not n_name:
        return None, "unmatched"
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Select all candidates with matching phone
    cursor.execute("""
        SELECT id, canonical_name, normalized_name, canonical_phone, normalized_phone 
        FROM people 
        WHERE normalized_phone = ?
    """, (n_phone,))
    
    candidates = cursor.fetchall()
    conn.close()
    
    matching_ids = []
    for cand in candidates:
        cand_id, _, cand_norm_name, _, _ = cand
        if are_names_compatible(n_name, cand_norm_name):
            matching_ids.append(cand_id)
            
    if len(matching_ids) == 1:
        return matching_ids[0], "matched"
        
    return None, "unmatched"
