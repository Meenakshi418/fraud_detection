"""Streamlit presentation for the voice authenticity MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from backend.pipeline import analyze_recording


def _load_styles() -> None:
    css_path = Path(__file__).with_name("style.css")
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _show_items(title: str, items: list[str], empty_message: str) -> None:
    st.markdown(f"**{title}**")
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption(empty_message)


def _show_audio_info(audio_info: Any) -> None:
    if not isinstance(audio_info, dict):
        return
    details: list[str] = []
    sample_rate = audio_info.get("sample_rate")
    duration = audio_info.get("duration_seconds")
    channels = audio_info.get("channels")
    if isinstance(sample_rate, (int, float)) and sample_rate > 0:
        details.append(f"Sample rate: {sample_rate / 1000:g} kHz")
    if isinstance(duration, (int, float)) and duration >= 0:
        details.append(f"Duration: {duration:g} seconds")
    if isinstance(channels, int) and channels > 0:
        details.append(f"Channels: {channels}")
    if details:
        st.caption("Audio details · " + " · ".join(details))


def _render_voice_result(result: dict[str, Any]) -> None:
    st.subheader("Voice authenticity")
    classification = result.get("classification", "Inconclusive")
    st.markdown(
        f'<div class="result-badge">{classification}</div>',
        unsafe_allow_html=True,
    )

    status = result.get("status")
    if status == "pending":
        st.warning(
            "Audio validation completed, but the pretrained AI detector is not "
            "connected yet. This is Inconclusive; no voice prediction was made."
        )
    elif status == "error":
        st.error("The audio detector could not analyze this recording.")
    elif status not in ("success", "pending", "error"):
        st.info("The detector returned an unknown status. Treat this result as inconclusive.")

    limitations = result.get("limitations", [])
    if isinstance(limitations, list) and limitations:
        _show_items("Evidence and limitations", limitations, "")
    _show_audio_info(result.get("audio_info"))
    st.caption(
        "A detector result is decision support only. It cannot prove that a voice is genuine or fake."
    )


def _render_risk_result(result: dict[str, Any]) -> None:
    st.subheader("Financial instruction risk")
    level = result.get("risk_level", "Inconclusive")
    st.markdown(f'<div class="result-badge">{level}</div>', unsafe_allow_html=True)

    score = result.get("risk_score")
    if isinstance(score, int) and not isinstance(score, bool):
        st.caption(f"Rule score: {score}/100 heuristic points · not a fraud probability")

    reasons = result.get("reasons", [])
    if isinstance(reasons, list) and reasons:
        _show_items("Why this was flagged", reasons, "")
    else:
        st.caption("No configured risk indicators were found in the provided transcript.")

    limitations = result.get("limitations", [])
    if isinstance(limitations, list) and limitations:
        _show_items("Limitations", limitations, "")

    if level == "High":
        st.warning(
            "Before acting, verify through a trusted contact method you choose yourself."
        )
    elif level in ("Medium", "Inconclusive"):
        st.info(
            "If the request involves money or sensitive information, verify it "
            "through a trusted, separate contact method."
        )


def _render_results(results: dict[str, Any]) -> None:
    voice_col, risk_col = st.columns(2, gap="large")
    with voice_col:
        with st.container(border=True):
            _render_voice_result(results.get("voice", {}))
    with risk_col:
        with st.container(border=True):
            _render_risk_result(results.get("risk", {}))


def render_app() -> None:
    _load_styles()
    st.title("AI-Powered Voice Authenticity Check")
    st.write(
        "Review an audio recording for possible voice manipulation and check an "
        "optional transcript for sensitive financial instructions."
    )
    st.warning(
        "Hackathon prototype · Results are not proof of authenticity or fraud. "
        "Verify sensitive financial requests using a trusted, separate channel."
    )

    uploaded_file = st.file_uploader(
        "Upload a WAV recording",
        type=["wav"],
        accept_multiple_files=False,
        help="Only WAV files are accepted.",
    )

    if uploaded_file is not None:
        st.audio(uploaded_file.getvalue(), format="audio/wav")

    transcript = st.text_area(
        "Optional transcript for financial-risk checks",
        placeholder="Paste a transcript if available. Leave blank to show financial risk as Inconclusive.",
        height=110,
        help="This text is used only by the financial-risk rules; it does not affect voice authenticity.",
    )

    if st.button("Analyze recording", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.error("Choose a WAV recording before starting the analysis.")
            return

        try:
            audio_bytes = uploaded_file.getvalue()
            with st.spinner("Analyzing the recording…"):
                results = analyze_recording(
                    file_name=uploaded_file.name,
                    audio_bytes=audio_bytes,
                    transcript=transcript,
                )
            _render_results(results)
        except Exception as exc:
            st.error(f"The application could not complete the analysis: {exc}")
