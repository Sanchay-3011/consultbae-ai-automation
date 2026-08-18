import pytest
from pipeline.matching import EntityResolver, CanonicalPerson

def test_exact_email_matching():
    resolver = EntityResolver()
    
    rec1 = {
        "source": "source1.csv",
        "data": {
            "name": "Tanvi Gupta",
            "email": "tanvi.gupta31@example.com",
            "phone": "9000000254"
        }
    }
    decision1 = resolver.add_record(rec1)
    assert decision1["decision"] == "NEW_PERSON"
    
    rec2 = {
        "source": "source2.csv",
        "data": {
            "name": "Tanvi Gupta",
            "email": "tanvi.gupta31@example.com",
            "phone": ""
        }
    }
    decision2 = resolver.add_record(rec2)
    assert decision2["decision"] == "MATCH"
    assert decision2["confidence"] == "HIGH"
    assert decision2["assigned_person_id"] == decision1["assigned_person_id"]

def test_exact_phone_matching():
    resolver = EntityResolver()
    
    rec1 = {
        "source": "source1.csv",
        "data": {
            "name": "Varun Jain",
            "email": "varun.jain29@example.com",
            "phone": "9000000263"
        }
    }
    resolver.add_record(rec1)
    
    rec2 = {
        "source": "source3.csv",
        "data": {
            "name": "Varun Jain",
            "email": "",
            "phone": "919000000263"
        }
    }
    decision2 = resolver.add_record(rec2)
    assert decision2["decision"] == "MATCH"
    assert decision2["confidence"] == "HIGH"

def test_name_only_matching():
    resolver = EntityResolver()
    
    rec1 = {
        "source": "source2.csv",
        "data": {
            "name": "Arjun Mehta",
            "email": "arjun.mehta77@mailtest.example.org",
            "phone": ""
        }
    }
    resolver.add_record(rec1)
    
    # Another record with same name, but different details (no email/phone overlap)
    rec2 = {
        "source": "source3.csv",
        "data": {
            "name": "Arjun Mehta",
            "email": "",
            "phone": "9000000272"
        }
    }
    decision2 = resolver.add_record(rec2)
    # Name matches, but no strong identifier overlaps -> REVIEW
    assert decision2["decision"] == "REVIEW"
    assert decision2["confidence"] == "LOW"

def test_conflicting_identity_fields():
    resolver = EntityResolver()
    
    # Person 1
    rec1 = {
        "source": "source1.csv",
        "data": {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "phone": "1111111111"
        }
    }
    resolver.add_record(rec1)
    
    # Person 2
    rec2 = {
        "source": "source1.csv",
        "data": {
            "name": "Bob Jones",
            "email": "bob@example.com",
            "phone": "2222222222"
        }
    }
    resolver.add_record(rec2)
    
    # Conflicting record: Alice's email but Bob's phone
    rec3 = {
        "source": "source2.csv",
        "data": {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "phone": "2222222222"
        }
    }
    decision3 = resolver.resolve_record(rec3)
    assert decision3["decision"] == "REVIEW"
    assert decision3["confidence"] == "LOW"
    assert "conflict" in decision3["match_type"]
