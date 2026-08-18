from pipeline.normalize import normalize_name, normalize_email, normalize_phone, normalize_city

def are_names_compatible(n1, n2):
    """
    Checks if two normalized names are compatible (e.g. 'r verma' and 'rohit verma').
    """
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
        
    t1 = n1.split()
    t2 = n2.split()
    if not t1 or not t2:
        return False
        
    # Check if they share the last name and have compatible first names/initials
    if len(t1) > 1 and len(t2) > 1 and t1[-1] == t2[-1]:
        f1, f2 = t1[0], t2[0]
        if f1 == f2 or (len(f1) == 1 and f2.startswith(f1)) or (len(f2) == 1 and f1.startswith(f2)):
            return True
            
    # Check if one is a substring of the other (e.g., 'rohit verma' and 'rohit')
    if n1 in n2 or n2 in n1:
        return True
        
    return False

class CanonicalPerson:
    def __init__(self, person_id):
        self.person_id = person_id
        self.emails = set()
        self.phones = set()
        self.names = set()
        self.cities = set()
        self.records = []

    def to_dict(self):
        return {
            "person_id": self.person_id,
            "emails": list(self.emails),
            "phones": list(self.phones),
            "names": list(self.names),
            "cities": list(self.cities),
            "records_count": len(self.records)
        }

class EntityResolver:
    def __init__(self):
        self.persons = []
        self.person_counter = 0

    def get_next_person_id(self):
        self.person_counter += 1
        return f"P{self.person_counter:03d}"

    def resolve_record(self, record):
        """
        Resolves a single raw record against existing CanonicalPersons.
        Does NOT modify the list of persons (read-only matching check).
        """
        raw_name = record["data"].get("name", "")
        raw_email = record["data"].get("email", "")
        raw_phone = record["data"].get("phone", "")
        raw_city = record["data"].get("city", "")
        
        n_name = normalize_name(raw_name)
        n_email = normalize_email(raw_email)
        n_phone = normalize_phone(raw_phone)
        
        candidates = []
        
        for person in self.persons:
            email_match = n_email and (n_email in person.emails)
            phone_match = n_phone and (n_phone in person.phones)
            
            # Check name compatibility with all known names of the person
            name_match = False
            for p_name in person.names:
                if are_names_compatible(n_name, p_name):
                    name_match = True
                    break
            
            if email_match or phone_match or name_match:
                candidates.append({
                    "person": person,
                    "email_match": email_match,
                    "phone_match": phone_match,
                    "name_match": name_match
                })
                
        # If no candidates match at all
        if not candidates:
            return {
                "source": record["source"],
                "source_row": record,
                "candidate_person": None,
                "match_type": "none",
                "confidence": "LOW",
                "reason": "No matching email, phone, or name found.",
                "decision": "NEW_PERSON"
            }
            
        # Detect if there are conflicts (e.g. matches multiple distinct persons)
        if len(candidates) > 1:
            # Check if any matches are based on email or phone (strong identifiers)
            strong_matches = [c for c in candidates if c["email_match"] or c["phone_match"]]
            if len(strong_matches) > 1:
                # Multiple strong matches to DIFFERENT canonical persons! Conflicting identity.
                return {
                    "source": record["source"],
                    "source_row": record,
                    "candidate_person": strong_matches[0]["person"],
                    "match_type": "conflict",
                    "confidence": "LOW",
                    "reason": f"Conflicting identity fields match multiple existing persons: {[c['person'].person_id for c in strong_matches]}.",
                    "decision": "REVIEW"
                }
            # Otherwise fallback to the single strong match, or review
            best_candidate = strong_matches[0] if strong_matches else candidates[0]
        else:
            best_candidate = candidates[0]
            
        person = best_candidate["person"]
        email_match = best_candidate["email_match"]
        phone_match = best_candidate["phone_match"]
        name_match = best_candidate["name_match"]
        
        # Check conflicts inside the single matched person
        # Check for Email conflict: record has email and person has emails, but they differ
        email_conflict = n_email and person.emails and (n_email not in person.emails)
        # Check for Phone conflict: record has phone and person has phones, but they differ
        phone_conflict = n_phone and person.phones and (n_phone not in person.phones)
        
        if email_conflict or phone_conflict:
            return {
                "source": record["source"],
                "source_row": record,
                "candidate_person": person,
                "match_type": "identifier_conflict",
                "confidence": "LOW",
                "reason": f"Identifier conflict: email_conflict={email_conflict}, phone_conflict={phone_conflict}.",
                "decision": "REVIEW"
            }
            
        # High Confidence Match
        if (email_match and not phone_conflict) or (phone_match and not email_conflict):
            # Check if names are also compatible
            if name_match:
                return {
                    "source": record["source"],
                    "source_row": record,
                    "candidate_person": person,
                    "match_type": "email_or_phone_and_name",
                    "confidence": "HIGH",
                    "reason": "Exact match on email/phone and compatible name.",
                    "decision": "MATCH"
                }
            else:
                # E.g. email matches but name is incompatible
                return {
                    "source": record["source"],
                    "source_row": record,
                    "candidate_person": person,
                    "match_type": "email_or_phone_name_mismatch",
                    "confidence": "MEDIUM",
                    "reason": "Exact match on email/phone but name is not compatible.",
                    "decision": "REVIEW"
                }
                
        # Medium/High: Exact phone + compatible name OR exact email + compatible name
        # (This is handled by high confidence above if there is no conflict, but let's be explicit)
        
        # Low/Review: Name-only match
        if name_match and not email_match and not phone_match:
            # Never automatically merge solely because names are identical when multiple candidates exist
            # If name matches but email/phone are different/not empty, or simply empty
            if n_email or n_phone:
                # Record has email or phone, but person also has them, and they didn't match (already handled by conflicts, but just in case)
                return {
                    "source": record["source"],
                    "source_row": record,
                    "candidate_person": person,
                    "match_type": "name_only_identifier_mismatch",
                    "confidence": "LOW",
                    "reason": "Name matches but strong identifiers do not match.",
                    "decision": "REVIEW"
                }
            else:
                return {
                    "source": record["source"],
                    "source_row": record,
                    "candidate_person": person,
                    "match_type": "name_only",
                    "confidence": "LOW",
                    "reason": "Name matches exactly/compatibly, but no email/phone overlap exists.",
                    "decision": "REVIEW"
                }
                
        return {
            "source": record["source"],
            "source_row": record,
            "candidate_person": None,
            "match_type": "unknown",
            "confidence": "LOW",
            "reason": "No match rules satisfied.",
            "decision": "NEW_PERSON"
        }

    def add_record(self, record):
        """
        Resolves the record, updates the canonical person list, and returns the decision.
        """
        decision_info = self.resolve_record(record)
        decision = decision_info["decision"]
        
        raw_name = record["data"].get("name", "")
        raw_email = record["data"].get("email", "")
        raw_phone = record["data"].get("phone", "")
        raw_city = record["data"].get("city", "")
        
        n_name = normalize_name(raw_name)
        n_email = normalize_email(raw_email)
        n_phone = normalize_phone(raw_phone)
        n_city = normalize_city(raw_city)
        
        decision_info["candidate_person_id"] = (
            decision_info["candidate_person"].person_id if decision_info.get("candidate_person") else None
        )

        if decision == "MATCH":
            person = decision_info["candidate_person"]
            # Add values to the selected person
            if n_email:
                person.emails.add(n_email)
            if n_phone:
                person.phones.add(n_phone)
            if n_name:
                person.names.add(n_name)
            if n_city:
                person.cities.add(n_city)
            person.records.append(record)
            decision_info["assigned_person_id"] = person.person_id
        elif decision == "NEW_PERSON":
            person = CanonicalPerson(self.get_next_person_id())
            self.persons.append(person)
            decision_info["created_person"] = person
            # Add values to the selected person
            if n_email:
                person.emails.add(n_email)
            if n_phone:
                person.phones.add(n_phone)
            if n_name:
                person.names.add(n_name)
            if n_city:
                person.cities.add(n_city)
            person.records.append(record)
            decision_info["assigned_person_id"] = person.person_id
        else: # REVIEW
            decision_info["assigned_person_id"] = None
            
        return decision_info
