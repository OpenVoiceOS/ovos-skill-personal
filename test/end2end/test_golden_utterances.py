"""Golden-utterance end-to-end coverage for ovos-skill-personal (en-US).

The master ovoscope corpus carries no rows for
``ovos-skill-personal.openvoiceos``, so ``golden_utterances.jsonl`` is
derived entirely from this skill's 5 well-populated Padatious intent files
(``WhoAreYou``, ``WhatAreYou``, ``WhoMadeYou``, ``WhenWereYouBorn``,
``WhereWereYouBorn``).

Intent-name matching reuses ``_matches_intent`` from the existing
``test_intents_en_us.py`` (kept unchanged): different pipeline plugins
(padatious vs padacioso) register the matched intent under different
normalizations of the ``.intent`` filename basename, so comparison is
case/format tolerant rather than pinned to one wire format.

Run:
    uv run pytest test/end2end/test_golden_utterances.py -v
"""
import json
import re
from pathlib import Path

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "ovos-skill-personal.openvoiceos"
LANG = "en-US"

_PIPELINE = [
    "ovos-adapt-pipeline-plugin-high",
    "ovos-padatious-pipeline-plugin-high",
    "ovos-padacioso-pipeline-plugin-high",
    "ovos-adapt-pipeline-plugin-medium",
    "ovos-padacioso-pipeline-plugin-medium",
    "ovos-adapt-pipeline-plugin-low",
]

GOLDEN_PATH = Path(__file__).parent / "golden_utterances.jsonl"

# Confusables from other skills' domains, picked for lexical overlap with
# "who/what/when/where" identity-question phrasing.
NEGATIVE_UTTERANCES = [
    ("who is confucius", "ovos-skill-confucius-quotes.openvoiceos"),
    ("what's the weather", "ovos-skill-weather.openvoiceos"),
    ("when is my next alarm", "ovos-skill-alerts.openvoiceos"),
    ("where am i", "ovos-skill-homeassistant.openvoiceos"),
    ("who is albert einstein", "ovos-skill-wikipedia.openvoiceos"),
    ("play some music", "ovos-skill-music.openvoiceos"),
    ("search the web for cats", "ovos-skill-ddg.openvoiceos"),
]


def _matches_intent(msg_type: str, skill_id: str, intent_file: str) -> bool:
    # Deliberate drift tolerance: normalizes both sides to a bare lowercase
    # token so "WhoAreYou" (PascalCase, no extension) and "who_are_you.intent"
    # (snake_case, extension kept) are treated as equivalent -- this is an
    # intentional naming-format tolerance, not a bug.
    prefix = f"{skill_id}:"
    if not msg_type.startswith(prefix):
        return False
    observed = msg_type[len(prefix):]
    observed_base = observed.rsplit(".", 1)[0] if observed.endswith(".intent") else observed
    expected_base = intent_file.rsplit(".", 1)[0]
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    return norm(observed_base) == norm(expected_base)


def _load_golden_rows():
    rows = []
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("needs_manual"):
                continue
            rows.append(row)
    return rows


GOLDEN_ROWS = [pytest.param(r, id=r["utterance"]) for r in _load_golden_rows()]


@pytest.fixture(scope="module")
def minicroft():
    mc = get_minicroft([SKILL_ID])
    yield mc
    mc.stop()


def _capture(mc, text, session_id):
    session = Session(session_id)
    session.lang = LANG
    session.pipeline = list(_PIPELINE)
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": LANG},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(mc)
    capture.capture(utterance, timeout=30)
    return capture.finish()


@pytest.mark.timeout(60)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=lambda r: r["utterance"])
def test_golden_utterance(minicroft, row):
    intent_file = f"{row['intent_label']}.intent"
    messages = _capture(minicroft, row["utterance"], f"golden-{row['utterance']}")
    types = [m.msg_type for m in messages]
    assert any(_matches_intent(t, SKILL_ID, intent_file) for t in types), (
        f"{row['utterance']!r}: expected {SKILL_ID}:{intent_file}, got {types!r}"
    )
    assert any("speak" in t for t in types), (
        f"{row['utterance']!r}: expected a spoken response, got {types!r}"
    )


@pytest.mark.timeout(60)
@pytest.mark.parametrize("negative", NEGATIVE_UTTERANCES, ids=lambda n: n[0])
def test_negative_confusable_not_claimed(minicroft, negative):
    text, source_skill = negative
    messages = _capture(minicroft, text, f"negative-{text}")
    types = [m.msg_type for m in messages]
    claimed = any(t.startswith(f"{SKILL_ID}:") for t in types)
    assert not claimed, f"{text!r} (from {source_skill}) was incorrectly claimed by {SKILL_ID}: {types!r}"
