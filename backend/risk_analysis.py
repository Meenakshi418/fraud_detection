"""Transparent transcript-based financial risk flags for the MVP.

This module does not assess whether a voice is authentic and does not estimate
the probability of fraud. Its score is a deterministic heuristic from the
transcript only.
"""

from __future__ import annotations

import re
from typing import Any


# A feature adds points once, even if the transcript repeats it. The cap is
# 100. Thresholds: Low 0-19, Medium 20-44, High 45-100.
_RULES: tuple[tuple[str, int, re.Pattern[str]], ...] = (
    (
        "Urgent request to transfer or send money",
        30,
        re.compile(
            r"\b(?:urgent(?:ly)?|immediately|right now|asap|today|within\s+\d+\s+(?:minutes?|hours?))\b"
            r".{0,100}\b(?:transfer|send|wire|pay|payment|deposit)\b"
            r"|\b(?:transfer|send|wire|pay|payment|deposit)\b"
            r".{0,100}\b(?:urgent(?:ly)?|immediately|right now|asap|today)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Request to change or use new payment or bank details",
        30,
        re.compile(
            r"\b(?:change|update|replace|switch)\b"
            r".{0,70}\b(?:bank|account|payment|payee|beneficiar(?:y|ies)|routing|upi)\b"
            r"|\b(?:send|pay|transfer)\b.{0,50}\b(?:new|different|updated)\b"
            r".{0,30}\b(?:bank|account|payment|payee|beneficiar(?:y|ies)|routing|upi)\b"
            r"|\bnew\s+(?:bank\s+)?(?:account|payment\s+details|payee|beneficiar(?:y|ies))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Request for a password, PIN, OTP, or verification code",
        45,
        re.compile(
            r"\b(?:send|share|tell|give|provide|read|enter|confirm|need|asking\s+for)\b"
            r".{0,50}\b(?:password|passcode|pin|otp|one[- ]time\s+(?:password|code|passcode)|"
            r"verification\s+code|security\s+code)\b"
            r"|\b(?:password|passcode|pin|otp|one[- ]time\s+(?:password|code|passcode)|"
            r"verification\s+code|security\s+code)\b.{0,40}"
            r"\b(?:send|share|tell|give|provide|read|enter|confirm)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Speaker claims an authority or trusted identity",
        15,
        re.compile(
            r"\b(?:i am|i'm|this is)\s+(?:your\s+)?(?:boss|ceo|manager|bank(?:er)?|"
            r"bank(?:'s)?\s+(?:security|fraud)\s+(?:team|department)|it\s+support|"
            r"police|officer|government|tax\s+(?:office|department))\b"
            r"|\b(?:i am|i'm) (?:calling )?from (?:the )?(?:bank|police|government|tax office)\b"
            r"|\bcalling from (?:your )?(?:bank|police|government|tax office)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Request to bypass normal verification or approval",
        25,
        re.compile(
            r"\b(?:skip|bypass|ignore|disable|avoid)\b.{0,60}"
            r"\b(?:verification|approval|security|normal process|usual process|checks?)\b"
            r"|\bdo not verify\b|\bdon't verify\b|\bno need to (?:verify|confirm|check)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Secrecy request or threat/pressure",
        25,
        re.compile(
            r"\b(?:keep (?:this|it) (?:secret|confidential)|don't tell anyone|"
            r"do not tell anyone|tell nobody|keep this between us|"
            r"or else|you will be (?:fired|arrested)|account will be (?:closed|blocked))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Request to install or use remote-access software",
        35,
        re.compile(
            r"\b(?:install|download|open|use|launch|start|connect\s+to)\b.{0,60}"
            r"\b(?:anydesk|teamviewer|remote\s+desktop|remote\s+access|"
            r"screen\s+sharing|quick\s+assist|remote\s+support)\b"
            r"|\b(?:anydesk|teamviewer|quick\s+assist)\b.{0,40}"
            r"\b(?:install|download|open|use|launch|start|connect)\b",
            re.IGNORECASE,
        ),
    ),
)

_LIMITATIONS = [
    "The score is a rule-based heuristic, not a calibrated probability of fraud.",
    "Assessment uses transcript text only; it does not assess voice authenticity or prove intent.",
]


def analyze_risk(transcript: str) -> dict[str, Any]:
    """Return a deterministic risk assessment based on transcript wording.

    The score is an integer from 0 to 100 for usable transcript text, or None
    when the input is missing or unusable. Non-string values are handled as
    unusable input rather than raising an exception.
    """
    if not isinstance(transcript, str):
        return {
            "risk_level": "Inconclusive",
            "risk_score": None,
            "reasons": [],
            "limitations": ["No usable transcript text was provided."],
        }

    text = " ".join(transcript.split())
    if not text or not re.search(r"[A-Za-z0-9]", text):
        return {
            "risk_level": "Inconclusive",
            "risk_score": None,
            "reasons": [],
            "limitations": ["No usable transcript text was provided."],
        }

    reasons: list[str] = []
    score = 0
    for reason, points, pattern in _RULES:
        if pattern.search(text):
            reasons.append(reason)
            score += points

    score = max(0, min(100, score))
    if score >= 45:
        level = "High"
    elif score >= 20:
        level = "Medium"
    else:
        level = "Low"

    return {
        "risk_level": level,
        "risk_score": score,
        "reasons": reasons,
        "limitations": list(_LIMITATIONS),
    }
