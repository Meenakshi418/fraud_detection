"""Small orchestration layer joining the independent analysis modules."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any

from backend.detector import analyze_audio
from backend.risk_analysis import analyze_risk


_VOICE_LABELS = {"Likely Genuine", "Suspicious", "Inconclusive"}
_RISK_LABELS = {"Low", "Medium", "High", "Inconclusive"}


def _as_text_list(value: Any) -> list[str]:
    """Keep only displayable text from optional backend lists."""
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _voice_fallback(message: str, status: str = "error") -> dict[str, Any]:
    return {
        "status": status,
        "classification": "Inconclusive",
        "score": None,
        "limitations": [message],
        "audio_info": {},
    }


def _normalize_voice_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return _voice_fallback("The detector returned an unreadable result.")

    classification = result.get("classification")
    limitations = _as_text_list(result.get("limitations"))
    if not isinstance(classification, str) or classification not in _VOICE_LABELS:
        classification = "Inconclusive"
        limitations.append("The detector did not provide a recognized classification.")

    audio_info = result.get("audio_info")
    if not isinstance(audio_info, dict):
        audio_info = {}

    status = result.get("status")
    if not isinstance(status, str):
        status = "unknown"

    return {
        "status": status,
        "classification": classification,
        # The detector score has no shared semantics yet; keep it in the
        # backend result but the UI does not present it as a probability.
        "score": result.get("score"),
        "limitations": limitations,
        "audio_info": audio_info,
    }


def _normalize_risk_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {
            "risk_level": "Inconclusive",
            "risk_score": None,
            "reasons": [],
            "limitations": ["The financial risk module returned an unreadable result."],
        }

    risk_level = result.get("risk_level")
    if not isinstance(risk_level, str) or risk_level not in _RISK_LABELS:
        risk_level = "Inconclusive"

    risk_score = result.get("risk_score")
    if not isinstance(risk_score, int) or isinstance(risk_score, bool):
        risk_score = None
    else:
        risk_score = max(0, min(100, risk_score))

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "reasons": _as_text_list(result.get("reasons")),
        "limitations": _as_text_list(result.get("limitations")),
    }


def analyze_recording(
    file_name: str,
    audio_bytes: bytes,
    transcript: str | None = None,
) -> dict[str, Any]:
    """Analyze WAV audio and optional transcript without coupling the results.

    The uploaded bytes are written to a temporary WAV file because the detector
    accepts a filesystem path. The temporary file is removed on success or
    failure. Transcript-based risk analysis still runs if audio analysis fails.
    """
    try:
        if isinstance(transcript, str) and transcript.strip():
            raw_risk = analyze_risk(transcript)
        else:
            # Missing transcript must remain explicitly inconclusive.
            raw_risk = analyze_risk(None)
        risk_result = _normalize_risk_result(raw_risk)
    except Exception as exc:
        risk_result = {
            "risk_level": "Inconclusive",
            "risk_score": None,
            "reasons": [],
            "limitations": [f"Financial risk analysis failed: {exc}"],
        }

    if not isinstance(file_name, str) or Path(file_name).suffix.lower() != ".wav":
        voice_result = _voice_fallback("Please upload a WAV audio file.")
    elif not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
        voice_result = _voice_fallback("The uploaded WAV file is empty or unreadable.")
    else:
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary_file:
                temporary_file.write(audio_bytes)
                temporary_path = temporary_file.name
            voice_result = _normalize_voice_result(analyze_audio(temporary_path))
        except Exception as exc:
            voice_result = _voice_fallback(f"Audio analysis failed: {exc}")
        finally:
            if temporary_path is not None:
                try:
                    Path(temporary_path).unlink(missing_ok=True)
                except OSError:
                    # Cleanup trouble should not discard either analysis result.
                    pass

    return {"voice": voice_result, "risk": risk_result}
