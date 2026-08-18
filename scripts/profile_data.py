import os
import re
import csv
from collections import Counter

def clean_phone(phone_str):
    if not phone_str or not isinstance(phone_str, str):
        return ""
    # Remove all non-numeric characters
    digits = re.sub(r'\D', '', phone_str)
    # If it starts with 91 and has 12 digits, strip the 91 prefix
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    # If it starts with 0 and has 11 digits, strip the 0 prefix
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    return digits

def clean_email(email_str):
    if not email_str or not isinstance(email_str, str):
        return ""
    return email_str.strip().lower()

def clean_name(name_str):
    if not name_str or not isinstance(name_str, str):
        return ""
    # Simplify and normalize name (lowercase, strip extra spaces, remove dots)
    name = name_str.strip().lower()
    name = re.sub(r'\s+', ' ', name)
    name = name.replace('.', '')
    return name

def profile_source1(file_path):
    print("=" * 60)
    print(f"Profiling: {os.path.basename(file_path)}")
    print("=" * 60)
    
    rows = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if not row or all(x.strip() == '' for x in row):
                continue
            rows.append((i, row))
            
    print(f"Total Rows (excluding header & empty rows): {len(rows)}")
    print(f"Columns: {', '.join(header)}")
    
    # Analyze data types & missing values
    missing_counts = {col: 0 for col in header}
    ctc_types = []
    phone_formats = []
    city_formats = []
    date_formats = []
    
    for line_num, row in rows:
        # Check field counts
        if len(row) < len(header):
            print(f"  Line {line_num}: Suspiciously short row (fewer columns than header)")
            continue
            
        for col_name, val in zip(header, row):
            if not val.strip():
                missing_counts[col_name] += 1
                
        # CTC inspection
        ctc_val = row[header.index("Current CTC")].strip()
        if ctc_val:
            try:
                ctc_num = float(ctc_val)
                if ctc_num < 100:  # e.g., 4.2 or 6.1
                    ctc_types.append("LPA (Float)")
                else:
                    ctc_types.append("Absolute (INR)")
            except ValueError:
                ctc_types.append("Non-numeric")
                
        # Phone inspection
        phone_val = row[header.index("Phone")].strip()
        if phone_val:
            if phone_val.startswith('+91'):
                phone_formats.append("Preceded by +91")
            elif phone_val.startswith('0'):
                phone_formats.append("Preceded by 0")
            elif len(phone_val) == 10 and phone_val.isdigit():
                phone_formats.append("10-digit raw")
            else:
                phone_formats.append("Other format")
                
        # City inspection
        city_val = row[header.index("City")].strip()
        if city_val:
            city_formats.append(city_val)
            
        # Date inspection
        date_val = row[header.index("Applied Date")].strip()
        if date_val:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_val):
                date_formats.append("YYYY-MM-DD")
            elif re.match(r'^\d{2}-\d{2}-\d{4}$', date_val):
                date_formats.append("DD-MM-YYYY")
            elif re.match(r'^\d{2}/\d{2}/\d{4}$', date_val):
                date_formats.append("MM/DD/YYYY")
            elif re.match(r'^\d+\s+[A-Za-z]+\s+\d{4}$', date_val):
                date_formats.append("D MMM YYYY")
            else:
                date_formats.append("Other")

    print("\nInferred Data Types (approx):")
    for col in header:
        print(f"  - {col}: String/Text (Parsed standard fields)")
        
    print("\nMissing-value counts:")
    for col, count in missing_counts.items():
        print(f"  - {col}: {count}")
        
    print("\nFormatting Inconsistencies & Anomalies:")
    print(f"  - CTC representation styles: {dict(Counter(ctc_types))}")
    print(f"  - Phone format distribution: {dict(Counter(phone_formats))}")
    print(f"  - City values (unique): {sorted(list(set(city_formats)))}")
    print(f"  - Applied Date formats: {dict(Counter(date_formats))}")
    
    # Check duplicate rows
    seen_rows = []
    duplicates = []
    seen_emails = {}
    seen_phones = {}
    
    for line_num, row in rows:
        row_tuple = tuple(row)
        if row_tuple in seen_rows:
            duplicates.append((line_num, row))
        else:
            seen_rows.append(row_tuple)
            
        # Cross-field checks (emails/phones)
        email = clean_email(row[header.index("Email")])
        phone = clean_phone(row[header.index("Phone")])
        name = row[header.index("Full Name")].strip()
        
        if email:
            if email in seen_emails:
                seen_emails[email].append((line_num, name))
            else:
                seen_emails[email] = [(line_num, name)]
        if phone:
            if phone in seen_phones:
                seen_phones[phone].append((line_num, name))
            else:
                seen_phones[phone] = [(line_num, name)]
                
    print(f"\nDuplicate Rows count: {len(duplicates)}")
    for line_num, d_row in duplicates:
        print(f"  - Line {line_num} is a duplicate of a previous row: {d_row}")
        
    print("\nNear-Duplicates / Shared Identity Fields within Source 1:")
    for email, occurrences in seen_emails.items():
        if len(occurrences) > 1:
            print(f"  - Shared Email '{email}': {occurrences}")
    for phone, occurrences in seen_phones.items():
        if len(occurrences) > 1:
            print(f"  - Shared Phone '{phone}': {occurrences}")
            
    return rows, header

def profile_source2(file_path):
    print("\n" + "=" * 60)
    print(f"Profiling: {os.path.basename(file_path)}")
    print("=" * 60)
    
    rows = []
    empty_lines = []
    malformed_rows = []
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if not row or all(x.strip() == '' for x in row):
                empty_lines.append(i)
                continue
            
            # Identify shifted row: email_id has no '@' and status/skill columns are shifted
            # Specifically line 20: email_id="react, javascript, mysql" (no @, looks like skills)
            email_val = row[0].strip()
            if '@' not in email_val and len(row) >= 6:
                malformed_rows.append((i, row, "Shifted columns / fields misaligned"))
                # Re-align line 20 fields for local profiling logic
                aligned_row = [row[1], row[2], row[3], row[4], row[5], row[0]]
                rows.append((i, aligned_row))
            else:
                rows.append((i, row))
                
    print(f"Total Rows (excluding header & empty rows): {len(rows)}")
    print(f"Empty rows count: {len(empty_lines)} (Lines: {empty_lines})")
    print(f"Malformed/Shifted rows count: {len(malformed_rows)}")
    for line_num, r, reason in malformed_rows:
        print(f"  - Line {line_num}: {reason}. Content: {r}")
        
    # Stats
    missing_counts = {col: 0 for col in header}
    rate_types = []
    status_values = []
    
    for line_num, row in rows:
        for col_name, val in zip(header, row):
            if not val.strip():
                missing_counts[col_name] += 1
                
        rate = row[header.index("rate")].strip()
        if rate:
            if '/hr' in rate:
                rate_types.append("Hourly (/hr)")
            elif '/month' in rate:
                rate_types.append("Monthly (/month)")
            else:
                rate_types.append("Other")
                
        status = row[header.index("status")].strip()
        if status:
            status_values.append(status)
            
    print("\nMissing-value counts:")
    for col, count in missing_counts.items():
        print(f"  - {col}: {count}")
        
    print("\nFormatting Inconsistencies & Anomalies:")
    print(f"  - Rate representations: {dict(Counter(rate_types))}")
    print(f"  - Status values (unique case variations): {sorted(list(set(status_values)))}")
    
    return rows, header

def profile_source3(file_path):
    print("\n" + "=" * 60)
    print(f"Profiling: {os.path.basename(file_path)}")
    print("=" * 60)
    
    rows = []
    duplicate_headers = []
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if not row or all(x.strip() == '' for x in row):
                continue
            # Identify repeated header
            if row == header:
                duplicate_headers.append(i)
                continue
            rows.append((i, row))
            
    print(f"Total Rows (excluding headers & empty rows): {len(rows)}")
    print(f"Duplicate Header rows count: {len(duplicate_headers)} (Lines: {duplicate_headers})")
    
    missing_counts = {col: 0 for col in header}
    verified_values = []
    phone_formats = []
    
    for line_num, row in rows:
        for col_name, val in zip(header, row):
            if not val.strip():
                missing_counts[col_name] += 1
                
        verified = row[header.index("Verified")].strip()
        if verified:
            verified_values.append(verified)
            
        phone = row[header.index("Phone Number")].strip()
        if phone:
            if phone.startswith('+91-'):
                phone_formats.append("Starts with +91-")
            elif phone.startswith('91') and len(phone) == 12:
                phone_formats.append("Starts with 91")
            elif len(phone) == 10 and phone.isdigit():
                phone_formats.append("10-digit raw")
            else:
                phone_formats.append("Other")
                
    print("\nMissing-value counts:")
    for col, count in missing_counts.items():
        print(f"  - {col}: {count}")
        
    print("\nFormatting Inconsistencies & Anomalies:")
    print(f"  - Verified representations: {dict(Counter(verified_values))}")
    print(f"  - Phone format distribution: {dict(Counter(phone_formats))}")
    
    return rows, header

def analyze_cross_source_matches(s1_data, s1_hdr, s2_data, s2_hdr, s3_data, s3_hdr):
    print("\n" + "=" * 60)
    print("Cross-Source Identity Matches Analysis")
    print("=" * 60)
    
    s1_by_email = {}
    s1_by_phone = {}
    
    for line_num, row in s1_data:
        email = clean_email(row[s1_hdr.index("Email")])
        phone = clean_phone(row[s1_hdr.index("Phone")])
        name = row[s1_hdr.index("Full Name")].strip()
        record_info = {"line": line_num, "name": name, "source": "source1"}
        
        if email:
            s1_by_email.setdefault(email, []).append(record_info)
        if phone:
            s1_by_phone.setdefault(phone, []).append(record_info)
            
    s2_by_email = {}
    for line_num, row in s2_data:
        email = clean_email(row[s2_hdr.index("email_id")])
        name = row[s2_hdr.index("worker_name")].strip()
        record_info = {"line": line_num, "name": name, "source": "source2"}
        if email:
            s2_by_email.setdefault(email, []).append(record_info)
            
    s3_by_phone = {}
    s3_by_name = {}
    for line_num, row in s3_data:
        phone = clean_phone(row[s3_hdr.index("Phone Number")])
        name = row[s3_hdr.index("Name")].strip()
        record_info = {"line": line_num, "name": name, "source": "source3"}
        if phone:
            s3_by_phone.setdefault(phone, []).append(record_info)
        cleaned_name = clean_name(name)
        if cleaned_name:
            s3_by_name.setdefault(cleaned_name, []).append(record_info)

    # 1. Matches by Email between Source 1 and Source 2
    email_matches = set(s1_by_email.keys()) & set(s2_by_email.keys())
    print(f"\n1. Matches by Email (Source 1 <-> Source 2): {len(email_matches)} matches")
    for email in sorted(email_matches):
        s1_recs = [f"{r['name']} (L{r['line']})" for r in s1_by_email[email]]
        s2_recs = [f"{r['name']} (L{r['line']})" for r in s2_by_email[email]]
        print(f"  - Email '{email}': Source1: {s1_recs} <-> Source2: {s2_recs}")

    # 2. Matches by Phone between Source 1 and Source 3
    phone_matches = set(s1_by_phone.keys()) & set(s3_by_phone.keys())
    print(f"\n2. Matches by Phone (Source 1 <-> Source 3): {len(phone_matches)} matches")
    for phone in sorted(phone_matches):
        s1_recs = [f"{r['name']} (L{r['line']})" for r in s1_by_phone[phone]]
        s3_recs = [f"{r['name']} (L{r['line']})" for r in s3_by_phone[phone]]
        print(f"  - Phone '{phone}': Source1: {s1_recs} <-> Source3: {s3_recs}")

    # 3. Matches by Name between Source 2 and Source 3 (Since Source 2 has no phone, and Source 3 has no email)
    s2_names = {clean_name(r[s2_hdr.index("worker_name")]): r[s2_hdr.index("worker_name")] for _, r in s2_data}
    name_matches = set(s2_names.keys()) & set(s3_by_name.keys())
    print(f"\n3. Matches by Name (Source 2 <-> Source 3) [No direct Phone/Email link]: {len(name_matches)} matches")
    for c_name in sorted(name_matches):
        s2_recs = [f"L{line}" for line, r in s2_data if clean_name(r[s2_hdr.index("worker_name")]) == c_name]
        s3_recs = [f"{r['name']} (L{r['line']})" for r in s3_by_name[c_name]]
        print(f"  - Name '{s2_names[c_name]}': Source2: {s2_recs} <-> Source3: {s3_recs}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s1_path = os.path.join(base_dir, "data", "source1_naukri_applicants.csv")
    s2_path = os.path.join(base_dir, "data", "source2_gig_workers.csv")
    s3_path = os.path.join(base_dir, "data", "source3_cbnexus_contacts.csv")
    
    s1_data, s1_hdr = profile_source1(s1_path)
    s2_data, s2_hdr = profile_source2(s2_path)
    s3_data, s3_hdr = profile_source3(s3_path)
    
    analyze_cross_source_matches(s1_data, s1_hdr, s2_data, s2_hdr, s3_data, s3_hdr)
