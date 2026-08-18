import os
import csv

def load_source1(file_path):
    """
    Loads source1_naukri_applicants.csv.
    Columns: Full Name,Email,Phone,City,Experience (Years),Current CTC,Applied Date,Skills
    """
    records = []
    if not os.path.exists(file_path):
        return records
        
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if not row or all(x.strip() == '' for x in row):
                continue  # skip empty lines
                
            record = {
                "source": "source1_naukri_applicants.csv",
                "line_number": i,
                "raw_row": row,
                "data": {
                    "name": row[0].strip(),
                    "email": row[1].strip(),
                    "phone": row[2].strip(),
                    "city": row[3].strip(),
                    "experience": row[4].strip(),
                    "ctc": row[5].strip(),
                    "applied_date": row[6].strip(),
                    "skills": row[7].strip() if len(row) > 7 else ""
                }
            }
            records.append(record)
    return records

def load_source2(file_path):
    """
    Loads source2_gig_workers.csv.
    Columns: email_id,worker_name,rate,location,status,skill_tags
    Detects and corrects malformed/shifted row at line 20.
    """
    records = []
    if not os.path.exists(file_path):
        return records
        
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if not row or all(x.strip() == '' for x in row):
                continue  # skip empty lines
                
            # Detect shifted/malformed row
            # If the first field has no '@' and we have at least 6 fields, it's shifted
            if '@' not in row[0] and len(row) >= 6:
                # Re-align: original row has skills in email_id, email in worker_name, etc.
                # Aligned mapping:
                # email_id = row[1], worker_name = row[2], rate = row[3], location = row[4], status = row[5], skill_tags = row[0]
                aligned_data = {
                    "email": row[1].strip(),
                    "name": row[2].strip(),
                    "rate": row[3].strip(),
                    "city": row[4].strip(),
                    "status": row[5].strip(),
                    "skills": row[0].strip()
                }
                is_malformed = True
            else:
                aligned_data = {
                    "email": row[0].strip(),
                    "name": row[1].strip(),
                    "rate": row[2].strip(),
                    "city": row[3].strip(),
                    "status": row[4].strip(),
                    "skills": row[5].strip() if len(row) > 5 else ""
                }
                is_malformed = False
                
            record = {
                "source": "source2_gig_workers.csv",
                "line_number": i,
                "raw_row": row,
                "is_malformed_shifted": is_malformed,
                "data": aligned_data
            }
            records.append(record)
    return records

def load_source3(file_path):
    """
    Loads source3_cbnexus_contacts.csv.
    Columns: Name,Phone Number,City,Verified,Projects Completed
    Detects and skips the duplicate header row.
    """
    records = []
    if not os.path.exists(file_path):
        return records
        
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if not row or all(x.strip() == '' for x in row):
                continue  # skip empty lines
                
            # Skip duplicate header row
            if row == header:
                continue
                
            record = {
                "source": "source3_cbnexus_contacts.csv",
                "line_number": i,
                "raw_row": row,
                "data": {
                    "name": row[0].strip(),
                    "phone": row[1].strip(),
                    "city": row[2].strip(),
                    "verified": row[3].strip(),
                    "projects_completed": row[4].strip()
                }
            }
            records.append(record)
    return records
