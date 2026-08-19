import pytest
import os
import io
import wave
import numpy as np
import sqlite3
from database.migrate import init_db, get_connection
from database.repository import insert_person
from audio_app.audio_processing import analyze_audio
from audio_app.matching import resolve_person
from audio_app.database import initialize_audio_table, save_audio_submission, get_audio_submissions

def create_dummy_wav(duration=1.0, sample_rate=44100, num_channels=1, sample_width=2):
    f_io = io.BytesIO()
    with wave.open(f_io, 'wb') as w:
        w.setnchannels(num_channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        
        num_frames = int(duration * sample_rate)
        t = np.linspace(0, duration, num_frames, endpoint=False)
        # Generate 440Hz sine wave tone at -6 dBFS for first half, silence for second half
        data = np.zeros(num_frames)
        half_frames = num_frames // 2
        data[:half_frames] = 0.5 * np.sin(2 * np.pi * 440 * t[:half_frames])
        
        if sample_width == 1:
            data_bytes = ((data + 1.0) * 127).astype(np.uint8).tobytes()
        elif sample_width == 2:
            data_bytes = (data * 32767).astype(np.int16).tobytes()
        elif sample_width == 4:
            data_bytes = (data * 2147483647).astype(np.int32).tobytes()
        else:
            data_bytes = (data * 32767).astype(np.int16).tobytes()
            
        w.writeframes(data_bytes)
    return f_io.getvalue()

@pytest.fixture
def test_db():
    db_path = "test_audio_app.db"
    init_db(db_path)
    initialize_audio_table(db_path)
    conn = get_connection(db_path)
    yield db_path
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

def test_audio_metadata_extraction():
    # 1.0 second, 16kHz, mono, 16-bit
    wav_bytes = create_dummy_wav(duration=1.0, sample_rate=16000, num_channels=1, sample_width=2)
    analysis = analyze_audio(wav_bytes, "test.wav", "audio/wav")
    
    assert analysis["duration_seconds"] == 1.0
    assert analysis["sample_rate_khz"] == 16.0
    assert analysis["bitrate_kbps"] == 256.0 # 16000 * 2 * 8 * 1 / 1000
    # RMS of sine wave of amplitude A (first half) is A/sqrt(2) = 0.3535
    # Since second half is silence, average RMS of the whole file is 0.25
    # 20 * log10(0.25) = -12.04 dBFS
    assert abs(analysis["loudness_db"] - (-12.04)) < 1.0
    assert analysis["quality_score"] > 50.0
    assert isinstance(analysis["quality_label"], str)

def test_invalid_audio_rejection():
    with pytest.raises(ValueError):
        analyze_audio(b"not an audio file", "broken.wav", "audio/wav")

def test_person_resolution(test_db):
    conn = get_connection(test_db)
    # Insert canonical candidate
    insert_person(
        conn, "P001", "Tanvi Gupta", "tanvi gupta",
        "tanvi.gupta31@example.com", "tanvi.gupta31@example.com",
        "+919000000254", "9000000254", "Bengaluru", 4.2, 420000.0
    )
    conn.commit()
    conn.close()
    
    # 1. Matched person resolution (Exact phone + compatible name)
    pid, status = resolve_person(test_db, "Tanvi Gupta", "+919000000254")
    assert pid == "P001"
    assert status == "matched"
    
    # 2. Compatible name (initials)
    pid, status = resolve_person(test_db, "T. Gupta", "9000000254")
    assert pid == "P001"
    assert status == "matched"
    
    # 3. Unmatched person (no matching phone)
    pid, status = resolve_person(test_db, "Tanvi Gupta", "9999999999")
    assert pid is None
    assert status == "unmatched"
    
    # 4. Unmatched person (matching phone but incompatible name)
    pid, status = resolve_person(test_db, "Arjun Mishra", "9000000254")
    assert pid is None
    assert status == "unmatched"

def test_ambiguous_person_resolution(test_db):
    conn = get_connection(test_db)
    # Insert two canonical candidates with same phone but different names (or overlapping names)
    insert_person(
        conn, "P001", "Arjun Mehta", "arjun mehta",
        "arjun.mehta9@example.in", "arjun.mehta9@example.in",
        "9000000272", "9000000272", "Noida", 4.0, 400000.0
    )
    insert_person(
        conn, "P002", "Arjun Mehta", "arjun mehta",
        "arjun.mehta2@example.in", "arjun.mehta2@example.in",
        "9000000272", "9000000272", "Noida", 2.0, 300000.0
    )
    conn.commit()
    conn.close()
    
    # Matching name is compatible with both -> Ambiguous -> Returns None, unmatched
    pid, status = resolve_person(test_db, "Arjun Mehta", "9000000272")
    assert pid is None
    assert status == "unmatched"

def test_database_insertion_and_retrieval(test_db):
    wav_bytes = create_dummy_wav(duration=1.5, sample_rate=44100, num_channels=1, sample_width=2)
    analysis = analyze_audio(wav_bytes, "test.wav", "audio/wav")
    
    save_audio_submission(
        db_path=test_db,
        person_id=None,
        submitted_name="Tanvi Gupta",
        normalized_name="tanvi gupta",
        submitted_phone="9000000254",
        normalized_phone="9000000254",
        file_path="audio_app/storage/audio/dummy.wav",
        original_filename="test.wav",
        mime_type="audio/wav",
        file_size_bytes=len(wav_bytes),
        duration_seconds=analysis["duration_seconds"],
        sample_rate_khz=analysis["sample_rate_khz"],
        bitrate_kbps=analysis["bitrate_kbps"],
        loudness_db=analysis["loudness_db"],
        noise_level_db=analysis["noise_level_db"],
        quality_score=analysis["quality_score"],
        quality_label=analysis["quality_label"],
        match_status="unmatched"
    )
    
    subs = get_audio_submissions(test_db)
    assert len(subs) == 1
    assert subs[0]["submitted_name"] == "Tanvi Gupta"
    assert subs[0]["duration_seconds"] == 1.5
    assert subs[0]["sample_rate_khz"] == 44.1
    assert subs[0]["match_status"] == "unmatched"
    assert subs[0]["person_id"] is None
