import streamlit as st
import os
import uuid
from pathlib import Path
from pipeline.normalize import normalize_name, normalize_phone
from audio_app.audio_processing import analyze_audio
from audio_app.matching import resolve_person
from audio_app.audio_database import initialize_audio_table, save_audio_submission, get_audio_submissions

# Set up page configurations
st.set_page_config(page_title="ConsultBae Audio Portal", layout="wide")

# Determine paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.path.join(BASE_DIR, "data", "consultbae.db")
STORAGE_DIR = os.path.join(BASE_DIR, "audio_app", "storage", "audio")

# Initialize database table and storage directories
os.makedirs(STORAGE_DIR, exist_ok=True)
initialize_audio_table(DB_PATH)

# Sidebar Navigation
st.sidebar.title("Navigation")
view = st.sidebar.radio("Go to:", ["Submit Audio", "Submissions"])

if view == "Submit Audio":
    st.title("ConsultBae Audio Collection")
    st.write("Submit voice samples to verify candidate identity and perform quality profiling.")
    
    # Inputs
    name = st.text_input("Full Name", placeholder="e.g. Tanvi Gupta")
    phone = st.text_input("Phone Number", placeholder="e.g. +91 90000 00254")
    
    st.subheader("Audio Source")
    st.write("Record audio from your browser or upload a pre-recorded WAV file.")
    
    # Recording input (Streamlit st.audio_input)
    recorded_file = None
    if hasattr(st, "audio_input"):
        recorded_file = st.audio_input("Record audio sample")
    else:
        st.info("Browser audio recording is supported in newer Streamlit versions via st.audio_input.")
        
    # File uploader
    uploaded_file = st.file_uploader("Or upload WAV audio file", type=["wav"])
    
    selected_file = None
    source_method = ""
    
    if recorded_file and uploaded_file:
        st.warning("Both browser recording and file upload were provided. Preferring browser recording.")
        selected_file = recorded_file
        source_method = "recorded"
    elif recorded_file:
        selected_file = recorded_file
        source_method = "recorded"
    elif uploaded_file:
        selected_file = uploaded_file
        source_method = "uploaded"
        
    if selected_file:
        st.subheader("Audio Preview & Info")
        st.audio(selected_file)
        
        # Display file metadata
        file_bytes = selected_file.getvalue()
        file_size = len(file_bytes)
        file_size_mb = file_size / (1024.0 * 1024.0)
        mime_type = selected_file.type if hasattr(selected_file, "type") else "audio/wav"
        filename = selected_file.name if hasattr(selected_file, "name") else "recorded.wav"
        
        st.write(f"**Filename:** {filename}")
        st.write(f"**File Size:** {file_size_mb:.2f} MB")
        st.write(f"**MIME Type:** {mime_type}")
        
        # Submit button
        if st.button("Submit Audio", type="primary"):
            # Validation
            if not name.strip():
                st.error("Submission failed: Name is required.")
            elif not phone.strip():
                st.error("Submission failed: Phone number is required.")
            elif len(normalize_phone(phone)) < 10:
                st.error(f"Submission failed: Phone number '{phone}' is not plausible (must contain at least 10 digits).")
            elif file_size == 0:
                st.error("Submission failed: Audio file is empty.")
            elif file_size_mb > 10.0:
                st.error("Submission failed: Audio file exceeds 10MB limit.")
            else:
                try:
                    # Try parsing/decoding and analyzing audio
                    analysis = analyze_audio(file_bytes, filename, mime_type)

                    if not analysis["speech_detected"]:
                        st.error(
                            "⚠️ No speech detected in this recording. "
                            "Please record again and make sure your microphone is working."
                        )
                    else:
                        st.success(
                            f"Speech detected — "
                            f"{analysis['activity_ratio'] * 100:.1f}% active audio."
                        )
                    
                    # Run identity matching
                    person_id, match_status = resolve_person(DB_PATH, name, phone)
                    
                    # Generate UUID filename
                    file_ext = Path(filename).suffix if filename else ".wav"
                    if not file_ext:
                        file_ext = ".wav"
                    unique_filename = f"{uuid.uuid4()}{file_ext}"
                    dest_path = os.path.join(STORAGE_DIR, unique_filename)
                    
                    # Save audio file to storage path
                    with open(dest_path, "wb") as f:
                        f.write(file_bytes)
                        
                    # Save metadata in SQLite
                    save_audio_submission(
                        db_path=DB_PATH,
                        person_id=person_id,
                        submitted_name=name,
                        normalized_name=normalize_name(name),
                        submitted_phone=phone,
                        normalized_phone=normalize_phone(phone),
                        file_path=os.path.join("audio_app", "storage", "audio", unique_filename),
                        original_filename=filename,
                        mime_type=mime_type,
                        file_size_bytes=file_size,
                        duration_seconds=analysis["duration_seconds"],
                        sample_rate_khz=analysis["sample_rate_khz"],
                        bitrate_kbps=analysis["bitrate_kbps"],
                        loudness_db=analysis["loudness_db"],
                        noise_level_db=analysis["noise_level_db"],
                        quality_score=analysis["quality_score"],
                        quality_label=analysis["quality_label"],
                        match_status=match_status
                    )
                    
                    st.success("Audio submitted and parsed successfully!")
                    st.write(f"**Identity Match:** {match_status.upper()}")
                    if person_id:
                        st.write(f"**Linked Canonical Person ID:** {person_id}")
                    else:
                        st.write("**Linked Canonical Person ID:** None (Unresolved)")
                        
                    st.json(analysis)
                    
                except ValueError as val_err:
                    st.error(f"Validation failed: The audio file is corrupted or could not be decoded. Detail: {val_err}")
                except Exception as ex:
                    st.error(f"An unexpected error occurred: {ex}")

else:
    st.title("Submissions View")
    st.write("Browse and listen to submitted worker audio files alongside their verified profiles.")
    
    submissions = get_audio_submissions(DB_PATH)
    
    if not submissions:
        st.info("No audio submissions found.")
    else:
        for sub in submissions:
            # Render each submission inside a clean card/container
            with st.container():
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    st.markdown(f"### Submission #{sub['id']}")
                    st.markdown(f"**Worker Name:** {sub['submitted_name']}")
                    st.markdown(f"**Phone Number:** {sub['submitted_phone']}")
                    
                    m_status = sub['match_status']
                    if m_status == 'matched':
                        st.success(f"Matched (ID: {sub['person_id']})")
                    else:
                        st.warning("Unmatched / Ambiguous")
                        
                    st.markdown(f"**Timestamp:** {sub['created_at']}")
                    
                with col2:
                    st.markdown("**Audio Metrics:**")
                    m_col1, m_col2, m_col3 = st.columns(3)
                    m_col1.metric("Duration", f"{sub['duration_seconds']:.2f}s")
                    m_col2.metric("Sample Rate", f"{sub['sample_rate_khz']:.1f} kHz")
                    m_col3.metric("Bitrate", f"{sub['bitrate_kbps']:.1f} kbps")
                    
                    l_col1, l_col2 = st.columns(2)
                    l_col1.metric("Loudness (RMS dBFS)", f"{sub['loudness_db']:.2f} dB")
                    l_col2.metric("Quality Score", f"{sub['quality_score']:.1f}% ({sub['quality_label']})")
                    
                    # Expose audio playback
                    # Read from local storage path (prevent path traversal by using basename)
                    filename = os.path.basename(sub['file_path'])
                    local_audio_path = os.path.join(STORAGE_DIR, filename)
                    
                    if os.path.exists(local_audio_path):
                        with open(local_audio_path, "rb") as audio_file:
                            st.audio(audio_file.read(), format=sub['mime_type'])
                    else:
                        st.error("Audio file could not be found in storage.")
                        
            st.divider()
