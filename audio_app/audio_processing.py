import wave
import io
import numpy as np


def _dbfs(rms, max_val):
    """Convert RMS amplitude to dBFS."""
    if rms <= 0 or max_val <= 0:
        return -100.0
    return float(20 * np.log10(rms / max_val))


def analyze_audio(file_bytes, filename, mime_type):
    """
    Analyze WAV audio and determine:
    - duration
    - sample rate
    - bitrate
    - RMS loudness
    - estimated noise floor
    - speech/activity presence
    - quality score
    - quality label
    """

    try:
        f_io = io.BytesIO(file_bytes)

        with wave.open(f_io, "rb") as w:
            sample_rate = w.getframerate()
            num_frames = w.getnframes()
            num_channels = w.getnchannels()
            sample_width = w.getsampwidth()

            if sample_rate <= 0:
                raise ValueError("Sample rate cannot be zero.")

            if num_frames <= 0:
                raise ValueError("Audio contains no frames.")

            duration = num_frames / sample_rate

            # PCM bitrate
            bitrate = (
                sample_rate
                * sample_width
                * 8
                * num_channels
            ) / 1000.0

            raw_data = w.readframes(num_frames)

            # ---------------------------------------------------------
            # Convert PCM bytes -> numpy samples
            # ---------------------------------------------------------

            if sample_width == 1:
                samples = (
                    np.frombuffer(
                        raw_data,
                        dtype=np.uint8
                    ).astype(np.float32)
                    - 128.0
                )
                max_val = 128.0

            elif sample_width == 2:
                samples = np.frombuffer(
                    raw_data,
                    dtype=np.int16
                ).astype(np.float32)
                max_val = 32768.0

            elif sample_width == 4:
                samples = np.frombuffer(
                    raw_data,
                    dtype=np.int32
                ).astype(np.float32)
                max_val = 2147483648.0

            else:
                raise ValueError(
                    f"Unsupported WAV sample width: {sample_width} bytes"
                )

            # Convert stereo/multi-channel -> mono
            if num_channels > 1 and len(samples) > 0:
                samples = samples.reshape(-1, num_channels)
                samples = np.mean(samples, axis=1)

            if len(samples) == 0:
                raise ValueError("Audio contains no samples.")

            # ---------------------------------------------------------
            # Overall loudness
            # ---------------------------------------------------------

            overall_rms = np.sqrt(np.mean(samples ** 2))
            loudness_db = _dbfs(overall_rms, max_val)

            # ---------------------------------------------------------
            # Frame-level analysis
            # ---------------------------------------------------------

            # 50 ms frames
            frame_size = max(1, int(sample_rate * 0.05))

            frame_db_values = []

            for start in range(0, len(samples), frame_size):
                frame = samples[start:start + frame_size]

                if len(frame) < frame_size // 2:
                    continue

                frame_rms = np.sqrt(np.mean(frame ** 2))
                frame_db = _dbfs(frame_rms, max_val)

                frame_db_values.append(frame_db)

            if not frame_db_values:
                frame_db_values = [loudness_db]

            frame_db_values = np.array(
                frame_db_values,
                dtype=np.float32
            )

            # ---------------------------------------------------------
            # Estimate noise floor
            # ---------------------------------------------------------

            # The quieter portion of the recording is used as
            # an approximate noise floor.
            noise_level_db = float(
                np.percentile(frame_db_values, 20)
            )

            # ---------------------------------------------------------
            # SPEECH / ACTIVITY DETECTION
            # ---------------------------------------------------------

            # A frame is considered potentially active when:
            # 1. It is above an absolute minimum level
            # 2. It is sufficiently above the estimated noise floor

            activity_threshold = max(
                noise_level_db + 6.0,
                -42.0
            )

            active_frames = (
                frame_db_values > activity_threshold
            )

            activity_ratio = float(
                np.mean(active_frames)
            )

            # Dynamic range tells us whether the recording actually
            # changes over time, rather than being constant noise.
            p10 = float(np.percentile(frame_db_values, 10))
            p90 = float(np.percentile(frame_db_values, 90))

            dynamic_range_db = p90 - p10

            # ---------------------------------------------------------
            # Determine whether speech/activity is present
            # ---------------------------------------------------------

            # Very quiet recording
            if loudness_db <= -55:
                speech_detected = False

            # Essentially constant signal/noise
            elif dynamic_range_db < 4.0 and activity_ratio < 0.20:
                speech_detected = False

            # Not enough energetic frames
            elif activity_ratio < 0.08:
                speech_detected = False

            else:
                speech_detected = True

            # ---------------------------------------------------------
            # Quality score
            # ---------------------------------------------------------

            if not speech_detected:

                # Do NOT call silence/no-speech "excellent".
                quality_score = 0.0
                quality_label = "No Speech Detected"

            else:

                # SNR-like estimate
                snr = loudness_db - noise_level_db

                quality_score = 100.0

                # Penalize weak speech level
                if loudness_db < -20:
                    quality_score -= (-20 - loudness_db) * 1.5

                # Penalize extremely loud/clipped recordings
                if loudness_db > -3:
                    quality_score -= (
                        loudness_db + 3
                    ) * 10

                # Penalize poor SNR
                if snr < 15:
                    quality_score -= (
                        15 - snr
                    ) * 3

                # Penalize weak speech activity
                if activity_ratio < 0.20:
                    quality_score -= (
                        0.20 - activity_ratio
                    ) * 100

                # Penalize very small dynamic range
                if dynamic_range_db < 10:
                    quality_score -= (
                        10 - dynamic_range_db
                    ) * 2

                quality_score = max(
                    0.0,
                    min(100.0, quality_score)
                )

                if quality_score >= 80:
                    quality_label = "Clean/Excellent"

                elif quality_score >= 50:
                    quality_label = "Moderate/Good"

                else:
                    quality_label = "Noisy/Poor"

            # ---------------------------------------------------------
            # Return analysis
            # ---------------------------------------------------------

            return {
                "duration_seconds": float(round(duration, 3)),
                "sample_rate_khz": float(
                    round(sample_rate / 1000.0, 1)
                ),
                "bitrate_kbps": float(
                    round(bitrate, 1)
                ),
                "loudness_db": float(
                    round(loudness_db, 2)
                ),
                "noise_level_db": float(
                    round(noise_level_db, 2)
                ),
                "activity_ratio": float(
                    round(activity_ratio, 3)
                ),
                "dynamic_range_db": float(
                    round(dynamic_range_db, 2)
                ),
                "speech_detected": bool(
                    speech_detected
                ),
                "quality_score": float(
                    round(quality_score, 1)
                ),
                "quality_label": quality_label
            }

    except Exception as e:
        raise ValueError(
            f"Could not decode audio: {e}"
        )