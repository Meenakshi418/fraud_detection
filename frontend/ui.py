"""Streamlit presentation for the voice authenticity MVP."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from backend.pipeline import analyze_recording


_VOICE_BADGES = {
    "Likely Genuine": "badge-good",
    "Suspicious": "badge-high",
    "Inconclusive": "badge-unknown",
}
_RISK_BADGES = {
    "Low": "badge-good",
    "Medium": "badge-medium",
    "High": "badge-high",
    "Inconclusive": "badge-unknown",
}


def _load_styles() -> None:
    css_path = Path(__file__).with_name("style.css")
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _badge(label: str, class_name: str) -> None:
    st.markdown(
        f'<span class="result-badge {class_name}">{label}</span>',
        unsafe_allow_html=True,
    )


def _show_items(title: str, items: list[str], empty_message: str = "") -> None:
    st.markdown(f'<div class="list-heading">{title}</div>', unsafe_allow_html=True)
    if items:
        for item in items:
            st.markdown(
                f'<div class="evidence-item">{escape(item)}</div>',
                unsafe_allow_html=True,
            )
    elif empty_message:
        st.caption(empty_message)


def _render_voice_result(result: dict[str, Any]) -> None:
    classification = result.get("classification", "Inconclusive")
    if not isinstance(classification, str) or classification not in _VOICE_BADGES:
        classification = "Inconclusive"

    st.markdown(
        '<div class="result-overline">01 / AUDIO SIGNAL</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Voice authenticity")
    _badge(classification, _VOICE_BADGES[classification])

    status = result.get("status")
    if status == "pending":
        st.markdown(
            '<div class="status-note status-pending"><strong>Detector not connected</strong>'
            "<br>Audio validation ran, but the pretrained AI inference is not connected yet. "
            "This result is inconclusive; no voice prediction was made.</div>",
            unsafe_allow_html=True,
        )
    elif status == "error":
        st.markdown(
            '<div class="status-note status-error"><strong>Could not analyze this audio</strong>'
            "<br>Check that the upload is a readable WAV recording.</div>",
            unsafe_allow_html=True,
        )
    elif status not in ("success", "pending", "error"):
        st.markdown(
            '<div class="status-note status-pending">Detector status is unknown. Treat the result as inconclusive.</div>',
            unsafe_allow_html=True,
        )

    audio_info = result.get("audio_info")
    if isinstance(audio_info, dict):
        metrics: list[tuple[str, str]] = []
        sample_rate = audio_info.get("sample_rate")
        duration = audio_info.get("duration_seconds")
        channels = audio_info.get("channels")
        if isinstance(sample_rate, (int, float)) and sample_rate > 0:
            metrics.append(("SAMPLE RATE", f"{sample_rate / 1000:g} kHz"))
        if isinstance(duration, (int, float)) and duration >= 0:
            metrics.append(("DURATION", f"{duration:g} sec"))
        if isinstance(channels, int) and channels > 0:
            metrics.append(("CHANNELS", str(channels)))
        if metrics:
            metric_cols = st.columns(len(metrics))
            for col, (label, value) in zip(metric_cols, metrics):
                with col:
                    st.markdown(
                        f'<div class="audio-metric"><span>{label}</span><strong>{value}</strong></div>',
                        unsafe_allow_html=True,
                    )

    limitations = result.get("limitations", [])
    if isinstance(limitations, list) and limitations:
        _show_items("What to keep in mind", limitations)
    st.markdown(
        '<div class="micro-note">Decision support only · a model result cannot prove that a voice is genuine or fake.</div>',
        unsafe_allow_html=True,
    )


def _render_risk_result(result: dict[str, Any]) -> None:
    level = result.get("risk_level", "Inconclusive")
    if not isinstance(level, str) or level not in _RISK_BADGES:
        level = "Inconclusive"

    st.markdown(
        '<div class="result-overline">02 / REQUEST CONTENT</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Financial instruction risk")
    _badge(level, _RISK_BADGES[level])

    score = result.get("risk_score")
    if isinstance(score, int) and not isinstance(score, bool):
        score = max(0, min(100, score))
        st.markdown(
            f'<div class="score-label"><span>RULE SIGNAL</span><span>{score} / 100</span></div>'
            f'<div class="score-track"><div class="score-fill" style="width:{score}%"></div></div>'
            '<div class="micro-note">Heuristic points, not a probability of fraud.</div>',
            unsafe_allow_html=True,
        )

    reasons = result.get("reasons", [])
    if isinstance(reasons, list) and reasons:
        _show_items("Signals found", reasons)
    else:
        st.markdown(
            '<div class="status-note status-neutral">No configured risk indicators were found in the transcript. This does not guarantee a request is safe.</div>',
            unsafe_allow_html=True,
        )

    limitations = result.get("limitations", [])
    if isinstance(limitations, list) and limitations:
        _show_items("Limitations", limitations)

    if level == "High":
        st.markdown(
            '<div class="next-step next-step-high"><span>RECOMMENDED NEXT STEP</span>'
            "Pause. Verify through a trusted contact method you choose yourself before sending money or sharing sensitive information.</div>",
            unsafe_allow_html=True,
        )
    elif level in ("Medium", "Inconclusive"):
        st.markdown(
            '<div class="next-step"><span>RECOMMENDED NEXT STEP</span>'
            "For financial instructions, confirm the request through a trusted, separate channel.</div>",
            unsafe_allow_html=True,
        )


def _render_results(results: dict[str, Any]) -> None:
    st.markdown(
        '<div class="section-heading"><span>ANALYSIS REPORT</span><p>Two independent views of the same request.</p></div>',
        unsafe_allow_html=True,
    )
    voice_col, risk_col = st.columns(2, gap="large")
    with voice_col:
        with st.container(key="voice_result"):
            _render_voice_result(results.get("voice", {}))
    with risk_col:
        with st.container(key="risk_result"):
            _render_risk_result(results.get("risk", {}))


def render_app() -> None:
    _load_styles()

    st.markdown(
        '<div class="hero-card">'
        '<div class="hero-copy">'
        '<div class="hero-kicker"><span class="live-dot"></span> TECHTREK · FRAUD PREVENTION</div>'
        '<h1>Trust the person.<br><em>Verify the voice.</em></h1>'
        '<p>Check an audio recording for signs of synthetic speech, and review financial instructions with a separate set of transparent rules.</p>'
        '<div class="hero-tags"><span>VOICE SIGNAL</span><span>TRANSACTION RISK</span><span>HUMAN REVIEW</span></div>'
        '</div>'
        '<div class="hero-art"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>'
        '<div class="mic-core">🎙</div><div class="wave wave-one"></div><div class="wave wave-two"></div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="prototype-banner"><span>⚠</span><div><strong>Prototype decision support</strong>'
        "<br>Results are not proof of authenticity or fraud. Always verify sensitive financial requests independently.</div></div>",
        unsafe_allow_html=True,
    )

    with st.container(key="upload_panel"):
        st.markdown(
            '<div class="panel-heading"><div><span class="panel-step">STEP 01</span>'
            '<h3>Add a recording</h3><p>WAV audio is processed by the project detector.</p></div>'
            '<div class="file-chip">WAV · AUDIO</div></div>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Choose a WAV file",
            type=["wav"],
            accept_multiple_files=False,
            help="Only WAV recordings are accepted.",
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            st.audio(uploaded_file.getvalue(), format="audio/wav")

        transcript = st.text_area(
            "Optional transcript",
            placeholder="Paste the words spoken in the recording, if you have them. Leave blank to mark content risk Inconclusive.",
            height=100,
            help="Transcript text is used only for financial-risk rules. It does not affect voice authenticity.",
        )
        st.markdown(
            '<div class="privacy-note"><span>↗</span> Transcript is optional. No text is inferred when it is left blank.</div>',
            unsafe_allow_html=True,
        )
        analyze_clicked = st.button(
            "Analyze recording  →",
            type="primary",
            use_container_width=True,
        )

    if analyze_clicked:
        if uploaded_file is None:
            st.error("Add a WAV recording before starting the analysis.")
            return
        try:
            with st.spinner("Reviewing the audio and transcript…"):
                results = analyze_recording(
                    file_name=uploaded_file.name,
                    audio_bytes=uploaded_file.getvalue(),
                    transcript=transcript,
                )
            _render_results(results)
        except Exception as exc:
            st.error(f"The application could not complete the analysis: {exc}")
