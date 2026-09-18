"""
RailOpt AI — Intent Classifier
================================

Maps a user's natural-language message to a structured Intent.

This is a KEYWORD-BASED classifier — no LLM call, no network, no latency.
It runs synchronously before the provider is invoked, allowing early routing
and permission checks.

When a live provider is connected, the classifier can be enhanced to use
the LLM for ambiguous cases, with this keyword classifier as a fast fallback.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .schemas import Intent, ClassifiedIntent


# ---------------------------------------------------------------------------
# Keyword pattern maps (ordered — first match wins)
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: List[Tuple[Intent, List[str]]] = [
    # EXPLAIN — "why", "explain", "reason", "how was", "decision"
    (Intent.EXPLAIN, [
        r"\bwhy\b",
        r"\bexplain\b",
        r"\breason\b",
        r"\bhow was\b",
        r"\bdecision\b",
        r"\bdeferred\b.*\bwhy\b",
        r"\bscheduled\b.*\bwhy\b",
        r"\baudit\b",
    ]),
    # WHAT_IF — "what if", "what happens if", "delay", "disruption", "simulate"
    (Intent.WHAT_IF, [
        r"\bwhat.?if\b",
        r"\bwhat happens if\b",
        r"\bsimulat\b",
        r"\bdisruption\b",
        r"\bscenario\b",
        r"\bdelayed by\b",
        r"\bdelay of\b",
    ]),
    # OPTIMIZE — "run", "optimize", "solve", "generate plan", "block plan"
    (Intent.OPTIMIZE, [
        r"\brun\b.*\bplan\b",
        r"\boptimiz\b",
        r"\bsolv\b",
        r"\bgenerate\b.*\bplan\b",
        r"\bblock plan\b",
        r"\brun optimization\b",
        r"\bschedule\b.*\bjobs\b",
    ]),
    # REPORT — "report", "analytics", "statistics", "show me", "summary"
    (Intent.REPORT, [
        r"\breport\b",
        r"\banalytics\b",
        r"\bstatistic\b",
        r"\bsummary\b",
        r"\bperformance\b",
        r"\bkpi\b",
    ]),
    # NAVIGATION — "go to", "open", "navigate", "take me", "show page"
    (Intent.NAVIGATION, [
        r"\bgo to\b",
        r"\bopen\b.*\bpage\b",
        r"\bnavigate\b",
        r"\btake me\b",
        r"\bshow.*\bgantt\b",
        r"\bopen.*\bgantt\b",
        r"\bopen.*\bplanning\b",
        r"\bopen.*\breport\b",
    ]),
    # QUERY — "show", "list", "what", "which", "get", "find", "how many"
    (Intent.QUERY, [
        r"\bshow\b",
        r"\blist\b",
        r"\bwhat\b",
        r"\bwhere\b",
        r"\bwhich\b",
        r"\bget\b",
        r"\bfind\b",
        r"\bhow many\b",
        r"\bpending\b",
        r"\bunscheduled\b",
        r"\bjobs?\b",
        r"\bstatus\b",
        r"\bdelayed\b",
        r"\bposition\b",
        r"\bdashboard\b",
    ]),
]

# Entity extraction patterns
_JOB_CODE_PATTERN = re.compile(r"\b(JOB-[A-Z]+-\d+)\b", re.IGNORECASE)
_TRAIN_NUMBER_PATTERN = re.compile(r"\b(\d{4,5})\b")
_DELAY_PATTERN = re.compile(r"(\d+)\s*(?:minutes?|mins?)", re.IGNORECASE)
_DEPT_PATTERN = re.compile(r"\b(ENG|TRD|S[_&]T|civil|traction|signal)\b", re.IGNORECASE)


class IntentClassifier:
    """
    Fast, deterministic keyword-based intent classifier.
    No LLM call, no network dependency, no latency.
    """

    def classify(self, message: str) -> ClassifiedIntent:
        """
        Classify a natural-language message into a structured Intent.

        Returns ClassifiedIntent with intent, confidence, and extracted entities.
        """
        lowered = message.lower()
        entities = self._extract_entities(message)

        for intent, patterns in _INTENT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, lowered):
                    return ClassifiedIntent(
                        intent=intent,
                        confidence=0.75,
                        extracted_entities=entities,
                    )

        return ClassifiedIntent(
            intent=Intent.UNKNOWN,
            confidence=0.0,
            extracted_entities=entities,
        )

    def _extract_entities(self, message: str) -> Dict[str, object]:
        """Extract structured entities from the raw message."""
        entities: Dict[str, object] = {}

        job_codes = _JOB_CODE_PATTERN.findall(message)
        if job_codes:
            entities["job_code"] = job_codes[0].upper()

        # Extract delay BEFORE train numbers to avoid short numbers being captured as train IDs
        delays = _DELAY_PATTERN.findall(message)
        if delays:
            entities["delay_minutes"] = int(delays[0])

        # Only capture 4-5 digit numbers NOT already captured as delay_minutes
        used_numbers = {str(entities["delay_minutes"])} if "delay_minutes" in entities else set()
        trains = [t for t in _TRAIN_NUMBER_PATTERN.findall(message) if t not in used_numbers]
        if trains:
            entities["train_number"] = trains[0]

        depts = _DEPT_PATTERN.findall(message)
        if depts:
            raw = depts[0].upper()
            dept_map = {"CIVIL": "ENG", "TRACTION": "TRD", "SIGNAL": "S_T", "S&T": "S_T", "S_T": "S_T"}
            entities["department_code"] = dept_map.get(raw, raw)

        return entities
