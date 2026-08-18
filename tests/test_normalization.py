import pytest
from pipeline.normalize import (
    normalize_name,
    normalize_email,
    normalize_phone,
    normalize_city,
    normalize_status,
    normalize_verified,
    parse_naukri_ctc,
    parse_gig_rate,
    parse_date
)

def test_normalize_name():
    assert normalize_name("Tanvi Gupta") == "tanvi gupta"
    assert normalize_name("R. Verma") == "r verma"
    assert normalize_name("  Rohit   Verma  ") == "rohit verma"
    assert normalize_name(None) == ""

def test_normalize_email():
    assert normalize_email("tanvi.gupta31@example.com") == "tanvi.gupta31@example.com"
    test_email = normalize_email(" ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG ")
    assert test_email == "isha.chopra95@mailtest.example.org"
    assert normalize_email(None) == ""

def test_normalize_phone():
    # Observed formats: +91, raw 10-digit, leading 0, with dash (+91-), starts with 91
    assert normalize_phone("+919000000254") == "9000000254"
    assert normalize_phone("9000000237") == "9000000237"
    assert normalize_phone("09000000287") == "9000000287"
    assert normalize_phone("+91-9000000131") == "9000000131"
    assert normalize_phone("919000000231") == "9000000231"
    assert normalize_phone(None) == ""

def test_normalize_city():
    assert normalize_city("Noida ") == "noida"
    assert normalize_city("gurugram ") == "gurgaon"
    assert normalize_city("bangalore") == "bengaluru"
    assert normalize_city("Bengaluru") == "bengaluru"
    assert normalize_city("GURGAON") == "gurgaon"
    assert normalize_city("Delhi NCR") == "delhi ncr"
    assert normalize_city(None) == ""

def test_normalize_status():
    assert normalize_status("Active") == "active"
    assert normalize_status("ACTIVE") == "active"
    assert normalize_status("paused") == "paused"
    assert normalize_status(None) == ""

def test_normalize_verified():
    assert normalize_verified("Y") is True
    assert normalize_verified("yes") is True
    assert normalize_verified("Yes") is True
    assert normalize_verified("N") is False
    assert normalize_verified("No") is False
    assert normalize_verified("Noo") is None
    assert normalize_verified(None) is None

def test_parse_naukri_ctc():
    # Absolute INR vs LPA
    res1 = parse_naukri_ctc("417964")
    assert res1["normalized_inr"] == 417964.0
    assert res1["is_lpa"] is False
    
    res2 = parse_naukri_ctc("4.2")
    assert res2["normalized_inr"] == 420000.0
    assert res2["is_lpa"] is True
    
    assert parse_naukri_ctc(None)["normalized_inr"] is None

def test_parse_gig_rate():
    # Hourly / monthly
    res1 = parse_gig_rate("1415/hr")
    assert res1["rate"] == 1415.0
    assert res1["unit"] == "hr"
    
    res2 = parse_gig_rate("15k/month")
    assert res2["rate"] == 15000.0
    assert res2["unit"] == "month"
    
    res3 = parse_gig_rate("72k/month")
    assert res3["rate"] == 72000.0
    assert res3["unit"] == "month"
    
    assert parse_gig_rate(None)["rate"] is None

def test_parse_date():
    assert parse_date("24-07-2026") == "2026-07-24"
    assert parse_date("2026-08-08") == "2026-08-08"
    assert parse_date("7 Jul 2026") == "2026-07-07"
    assert parse_date("07/13/2026") == "2026-07-13"
    assert parse_date("19 Jul 2026") == "2026-07-19"
