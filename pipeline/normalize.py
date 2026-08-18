import re
from datetime import datetime

def normalize_name(name):
    if not name or not isinstance(name, str):
        return ""
    # Remove dots and punctuation
    cleaned = name.replace(".", " ")
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    # Lowercase, strip, collapse multiple spaces
    cleaned = cleaned.lower().strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned

def normalize_email(email):
    if not email or not isinstance(email, str):
        return ""
    return email.strip().lower()

def normalize_phone(phone):
    if not phone or not isinstance(phone, str):
        return ""
    # Keep only digits
    digits = re.sub(r"\D", "", phone)
    # Strip 91 prefix if it leaves a 10-digit number
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    # Strip leading 0 if it leaves a 10-digit number
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits

def normalize_city(city):
    if not city or not isinstance(city, str):
        return ""
    cleaned = city.strip().lower()
    # Normalize trailing spaces or dots
    cleaned = re.sub(r"[^\w\s]", "", cleaned).strip()
    # Handle conservative aliases
    if cleaned in ("bangalore", "bengaluru"):
        return "bengaluru"
    if cleaned in ("gurgaon", "gurugram"):
        return "gurgaon"
    # Keep others (like Delhi, New Delhi, Noida, Pune) as is
    return cleaned

def normalize_status(status):
    if not status or not isinstance(status, str):
        return ""
    return status.strip().lower()

def normalize_verified(verified):
    if verified is None:
        return None
    if isinstance(verified, bool):
        return verified
    val = str(verified).strip().lower()
    if val in ("y", "yes", "true", "1"):
        return True
    if val in ("n", "no", "false", "0"):
        return False
    return None

def parse_naukri_ctc(ctc_val):
    if not ctc_val:
        return {"raw": "", "normalized_inr": None, "is_lpa": False}
    raw_str = str(ctc_val).strip()
    try:
        val = float(raw_str)
        # If float is small (< 100), treat as Lakhs Per Annum (LPA)
        if val < 100:
            return {"raw": raw_str, "normalized_inr": val * 100000.0, "is_lpa": True}
        else:
            return {"raw": raw_str, "normalized_inr": val, "is_lpa": False}
    except ValueError:
        return {"raw": raw_str, "normalized_inr": None, "is_lpa": False}

def parse_gig_rate(rate_val):
    if not rate_val:
        return {"raw": "", "rate": None, "unit": ""}
    raw_str = str(rate_val).strip()
    # Regex to capture value, optional 'k' multiplier, and unit (/hr or /month)
    match = re.search(r"([\d\.]+)\s*(k)?\s*/?\s*(hr|hour|month|mo)", raw_str, re.IGNORECASE)
    if match:
        val_str, k_mult, unit_str = match.groups()
        try:
            value = float(val_str)
            if k_mult and k_mult.lower() == 'k':
                value *= 1000.0
            
            unit = "hr"
            if unit_str.lower() in ("month", "mo"):
                unit = "month"
                
            return {"raw": raw_str, "rate": value, "unit": unit}
        except ValueError:
            pass
    return {"raw": raw_str, "rate": None, "unit": ""}

def parse_date(date_val):
    if not date_val:
        return ""
    raw_str = str(date_val).strip()
    formats = [
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y",
        "%m/%d/%Y",
        "%b %d %Y"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(raw_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # If no format matches, return raw string to preserve it
    return raw_str
