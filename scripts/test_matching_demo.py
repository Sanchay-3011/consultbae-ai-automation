import os
from pipeline.loaders import load_source1, load_source2, load_source3
from pipeline.matching import EntityResolver

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s1_path = os.path.join(base_dir, "data", "source1_naukri_applicants.csv")
    s2_path = os.path.join(base_dir, "data", "source2_gig_workers.csv")
    s3_path = os.path.join(base_dir, "data", "source3_cbnexus_contacts.csv")
    
    print("Loading datasets...")
    s1_records = load_source1(s1_path)
    s2_records = load_source2(s2_path)
    s3_records = load_source3(s3_path)
    
    print(f"Loaded {len(s1_records)} records from Source 1.")
    print(f"Loaded {len(s2_records)} records from Source 2.")
    print(f"Loaded {len(s3_records)} records from Source 3.")
    
    resolver = EntityResolver()
    
    # Let's run a demo of processing and matching
    print("\n" + "=" * 80)
    print("Entity Resolution Process Demo")
    print("=" * 80)
    
    # Combine some representative records to demonstrate matching
    # E.g. Tanvi Gupta, Varun Jain, Rohit Verma/R. Verma, Nikhil Chopra, etc.
    demo_names = {"Tanvi Gupta", "Varun Jain", "Rohit Verma", "R. Verma", "Nikhil Chopra", "Arjun Mehta"}
    
    all_records = s1_records + s2_records + s3_records
    
    # Sort them so they load sequentially
    # Source 1 is loaded first (creates canonical candidates)
    # Source 2 and 3 are matched against them.
    for record in all_records:
        name = record["data"].get("name", "")
        # Only process selected names for clean demo output
        if any(dn in name for dn in demo_names):
            decision = resolver.add_record(record)
            print(f"Source: {record['source']} (Line {record['line_number']})")
            print(f"  Raw: Name: '{name}', Email: '{record['data'].get('email', '')}', Phone: '{record['data'].get('phone', '')}'")
            print(f"  Decision: {decision['decision']}")
            print(f"  Assigned ID: {decision['assigned_person_id']}")
            print(f"  Confidence: {decision['confidence']}")
            print(f"  Reason: {decision['reason']}")
            print("-" * 50)
            
    print("\nCanonical Persons Summary:")
    print("=" * 80)
    for person in resolver.persons:
        if len(person.records) > 1:
            print(f"ID: {person.person_id}")
            print(f"  Names: {list(person.names)}")
            print(f"  Emails: {list(person.emails)}")
            print(f"  Phones: {list(person.phones)}")
            print(f"  Matched Records Count: {len(person.records)}")
            print("-" * 50)

if __name__ == '__main__':
    main()
