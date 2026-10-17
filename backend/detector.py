import os
import soundfile as sf
import numpy as np


def analyze_audio(file_path):
    """
    Analyse an audio file for possible synthetic speech.

    Returns a dictionary that can be consumed by
    the risk analysis module and the Streamlit UI.
    """

    if not os.path.isfile(file_path):
        return {
            "status": "error",
            "classification": "Inconclusive",
            "score": None,
            "limitations": ["Audio file not found."]
        }

    try:
        audio, sample_rate = sf.read(file_path)

        if audio.size == 0:
            return {
                "status": "error",
                "classification": "Inconclusive",
                "score": None,
                "limitations": ["Audio file is empty."]
            }

        if not np.isfinite(audio).all():
            return {
                "status": "error",
                "classification": "Inconclusive",
                "score": None,
                "limitations": ["Audio contains invalid numerical values."]
            }

        if audio.ndim == 2:
            audio = audio.mean(axis=1)

        duration = len(audio) / sample_rate

        if duration < 1:
            return {
                "status": "error",
                "classification": "Inconclusive",
                "score": None,
                "limitations": [
                    "Audio is too short for the configured detector."
                ]
            }

        # TODO: Run the pretrained AI detector here.
        # Do not classify audio using random rules.

        return {
            "status": "pending",
            "classification": "Inconclusive",
            "score": None,
            "limitations": [
                "Audio validation succeeded, but AI detection "
                "has not been connected yet."
            ],
            "audio_info": {
                "sample_rate": sample_rate,
                "duration_seconds": round(duration, 2)
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "classification": "Inconclusive",
            "score": None,
            "limitations": [
                f"Audio processing failed: {str(e)}"
            ]
        }