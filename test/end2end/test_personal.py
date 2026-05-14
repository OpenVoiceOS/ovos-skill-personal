# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""End-to-end intent tests for ovos-skill-personal using ovoscope.

==============================================================================
 HOW IT WORKS  —  copy-paste this pattern to any other OVOS skill
==============================================================================

Cases live in plain-text files under ``test/end2end/cases/<lang>/``:

    cases/<lang>/<IntentName>.intent.test    one utterance per line, expected
                                             to match <IntentName>
    cases/<lang>/no_match.test               one utterance per line, expected
                                             to match NO intent of this skill

`#` comments and blank lines are ignored. To add coverage, add a line. To
localize, drop a new ``cases/<lang>/`` folder with the same filenames. No
Python changes needed.

Each utterance becomes 4 generated tests:

  - one against ovos-padatious-pipeline-plugin (high+medium+low tiers)
  - one against ovos-padacioso-pipeline-plugin (high+medium+low tiers)
  - one against ovos-m2v-pipeline           (high+medium+low tiers)
  - one against the default full OVOS pipeline stack

A test passes if **any** tier of the pipeline family routes the utterance
to the expected intent. That lets a -low tier rescue a -high miss, which
is the realistic production behaviour.

To copy this to another skill:

  1. Copy ``test/end2end/`` wholesale.
  2. Edit ``SKILL_ID`` and ``INTENT_TO_HANDLER`` below.
  3. Replace the ``.intent.test`` files with your skill's intents.

The skill emits non-deterministic ``speak`` content, so ``speak`` messages
are ignored; routing + handler lifecycle are asserted instead.

==============================================================================
"""
import time
from copy import deepcopy
from pathlib import Path
from typing import Iterator, Optional
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils.log import LOG
from ovoscope import (DEFAULT_TEST_PIPELINE, End2EndTest, M2V_PIPELINE,
                      PADACIOSO_PIPELINE, PADATIOUS_PIPELINE, get_minicroft)

# ---------------------------------------------------------------------------
# Skill-specific config — edit these three for a different skill.
# ---------------------------------------------------------------------------
SKILL_ID = "ovos-skill-personal.openvoiceos"

INTENT_TO_HANDLER = {
    "WhoAreYou.intent": "PersonalSkill.handle_who_are_you_intent",
    "WhatAreYou.intent": "PersonalSkill.handle_what_are_you_intent",
    "WhenWereYouBorn.intent": "PersonalSkill.handle_when_were_you_born_intent",
    "WhereWereYouBorn.intent": "PersonalSkill.handle_where_were_you_born_intent",
    "WhoMadeYou.intent": "PersonalSkill.handle_who_made_you_intent",
}

# Messages whose content is non-deterministic or noisy for routing tests.
_IGNORE = [
    "speak",
    "mycroft.audio.play_sound",
    "ovos.common_play.stop.response",
    "common_query.openvoiceos.stop.response",
    "persona.openvoiceos.stop.response",
    "ovos-hivemind-pipeline-plugin.stop.response",
    "stop.openvoiceos.stop.response",
]

# ---------------------------------------------------------------------------
# Case-file discovery
# ---------------------------------------------------------------------------
CASES_DIR = Path(__file__).parent / "cases"


def _read_cases(path: Path) -> list[str]:
    """Return all non-comment, non-blank lines from ``path``."""
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def _discover_cases() -> Iterator[tuple[str, Optional[str], str]]:
    """Yield ``(lang, expected_intent_or_None, utterance)`` for every case.

    ``expected_intent_or_None`` is ``None`` for ``no_match.test`` lines.
    """
    if not CASES_DIR.is_dir():
        return
    for lang_dir in sorted(CASES_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue
        for case_file in sorted(lang_dir.glob("*.test")):
            stem = case_file.stem  # e.g. "WhoAreYou.intent" or "no_match"
            if case_file.name == "no_match.test":
                expected: Optional[str] = None
            elif stem.endswith(".intent"):
                expected = stem  # "<IntentName>.intent"
                if expected not in INTENT_TO_HANDLER:
                    raise AssertionError(
                        f"Case file {case_file} targets unknown intent "
                        f"{expected!r}. Add it to INTENT_TO_HANDLER.")
            else:
                continue
            for utt in _read_cases(case_file):
                yield lang_dir.name, expected, utt


# ---------------------------------------------------------------------------
# Shared minicroft — booted once, reused across every test.
# ---------------------------------------------------------------------------
_MINICROFT = None


def _all_case_langs() -> list[str]:
    """Languages discovered under cases/<lang>/, except en-US."""
    if not CASES_DIR.is_dir():
        return []
    out = []
    for p in sorted(CASES_DIR.iterdir()):
        if p.is_dir() and p.name != "en-US":
            out.append(p.name)
    return out


def _shared_minicroft():
    """Lazily create one minicroft with every locale-under-test enabled.

    The m2v pipeline only learns the skill's labels after it sees the
    ``padatious:register_intent`` events emitted at skill load. Without a
    short grace period the first m2v call logs
    ``"No model classes match registered intents"`` and falls through.
    """
    global _MINICROFT
    if _MINICROFT is None:
        LOG.set_level("CRITICAL")
        _MINICROFT = get_minicroft(
            [SKILL_ID], secondary_langs=_all_case_langs())
        # Nudge m2v to rebuild its label index now that intents are loaded.
        _MINICROFT.bus.emit(Message("mycroft.ready", {}, {}))
        time.sleep(10)
    return _MINICROFT


# ---------------------------------------------------------------------------
# Single-utterance assertion
# ---------------------------------------------------------------------------
def _assert_match(utterance: str, pipeline: list[str],
                  expected_intent: Optional[str], lang: str) -> None:
    """Fire ``utterance`` through ``pipeline`` and check the route.

    A pipeline is a list of stage ids (high/medium/low tiers of one
    family, or a full default stack). ``expected_intent`` is ``None`` to
    assert the utterance falls through to ``complete_intent_failure``.
    """
    minicroft = _shared_minicroft()
    session = Session(f"e2e-{utterance[:20]}")
    session.lang = lang
    session.pipeline = list(pipeline)

    source = Message(
        "recognizer_loop:utterance",
        {"utterances": [utterance], "lang": lang},
        {"session": session.serialize()},
    )

    if expected_intent is None:
        final_session = deepcopy(session)
        expected_messages = [
            source,
            Message("complete_intent_failure",
                    {"utterances": [utterance], "lang": lang}, {}),
            Message("ovos.utterance.handled", {}, {}),
        ]
        test = End2EndTest(
            minicroft=minicroft,
            skill_ids=[SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=_IGNORE,
            source_message=source,
            final_session=final_session,
            expected_messages=expected_messages,
            test_msg_data=False,
            test_msg_context=False,
        )
    else:
        handler = INTENT_TO_HANDLER[expected_intent]
        final_session = deepcopy(session)
        final_session.active_skills = [(SKILL_ID, 0.0)]
        expected_messages = [
            source,
            Message(f"{SKILL_ID}.activate", {}, {"skill_id": SKILL_ID}),
            Message(f"{SKILL_ID}:{expected_intent}",
                    {"utterance": utterance, "lang": lang},
                    {"skill_id": SKILL_ID}),
            Message("mycroft.skill.handler.start",
                    {"name": handler}, {"skill_id": SKILL_ID}),
            Message("mycroft.skill.handler.complete",
                    {"name": handler}, {"skill_id": SKILL_ID}),
            Message("ovos.utterance.handled", {}, {"skill_id": SKILL_ID}),
        ]
        test = End2EndTest(
            minicroft=minicroft,
            skill_ids=[SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=_IGNORE,
            source_message=source,
            final_session=final_session,
            activation_points=[f"{SKILL_ID}:{expected_intent}"],
            expected_messages=expected_messages,
        )
    test.execute(timeout=30)


# ---------------------------------------------------------------------------
# Test-class generator
# ---------------------------------------------------------------------------
def _slug(s: str) -> str:
    return (s.replace(" ", "_").replace("'", "")
             .replace("?", "").replace("-", "_"))


def _build_test_class(class_name: str, pipeline: list[str], doc: str) -> type:
    """Build a TestCase subclass with one method per discovered case."""

    def _make(utt, pipe, exp, lang):
        def _test(self):
            _assert_match(utt, pipe, exp, lang)
        _test.__doc__ = (
            f"[{lang}] {utt!r} -> "
            f"{exp if exp else 'no match'}  ({class_name})")
        return _test

    body = {"__doc__": doc}
    for lang, expected, utt in _discover_cases():
        label = expected.split(".")[0] if expected else "no_match"
        name = f"test_{lang.replace('-', '_')}__{label}__{_slug(utt)}"
        body[name] = _make(utt, pipeline, expected, lang)
    return type(class_name, (TestCase,), body)


# ---------------------------------------------------------------------------
# Generated test classes — one per pipeline family + one for the full stack.
# ---------------------------------------------------------------------------
TestPadatious = _build_test_class(
    "TestPadatious", PADATIOUS_PIPELINE,
    "Routing via ovos-padatious-pipeline-plugin (all 3 tiers).")

TestPadacioso = _build_test_class(
    "TestPadacioso", PADACIOSO_PIPELINE,
    "Routing via ovos-padacioso-pipeline-plugin (all 3 tiers).")

TestM2V = _build_test_class(
    "TestM2V", M2V_PIPELINE,
    "Routing via ovos-m2v-pipeline (all 3 tiers).")

TestDefaultPipeline = _build_test_class(
    "TestDefaultPipeline", DEFAULT_TEST_PIPELINE,
    "Routing via the default full OVOS pipeline stack.")


# ---------------------------------------------------------------------------
# Hand-curated cross-pipeline divergence tests.
#
# These were observed by probing every utterance from the .test files
# against every pipeline/tier combination on this skill's locale. They act
# as canaries: a pipeline upgrade that changes the routing of one of these
# borderline utterances will make a divergence test fail and force a
# conscious decision rather than silently changing skill behaviour.
# ---------------------------------------------------------------------------
WHO = "WhoAreYou.intent"
WHAT = "WhatAreYou.intent"
WHEN = "WhenWereYouBorn.intent"
WHERE = "WhereWereYouBorn.intent"
MADE = "WhoMadeYou.intent"

P_HIGH = ["ovos-padatious-pipeline-plugin-high"]
P_MED = ["ovos-padatious-pipeline-plugin-medium"]
P_LOW = ["ovos-padatious-pipeline-plugin-low"]
PC_HIGH = ["ovos-padacioso-pipeline-plugin-high"]
PC_MED = ["ovos-padacioso-pipeline-plugin-medium"]
M_HIGH = ["ovos-m2v-pipeline-high"]
M_MED = ["ovos-m2v-pipeline-medium"]
M_LOW = ["ovos-m2v-pipeline-low"]


class TestPipelineDivergence(TestCase):
    """Borderline utterances whose routing differs across pipelines/tiers.

    Documenting these makes the differences visible in the test suite and
    catches behaviour changes from upstream pipeline upgrades.
    """

    def test_who_made_you__padacioso_high_misses__medium_rescues(self):
        """``who made you`` is rejected by padacioso-high (confidence too
        low) but accepted by padacioso-medium and padacioso-low.
        Padatious matches it at every tier."""
        _assert_match("who made you", PC_HIGH, None, "en-US")
        _assert_match("who made you", PC_MED, MADE, "en-US")
        _assert_match("who made you", P_HIGH, MADE, "en-US")

    def test_who_are_you__m2v_misroutes_to_WhoMadeYou(self):
        """Embedding similarity (m2v) finds ``who are you`` closer to the
        WhoMadeYou intent samples than the WhoAreYou ones. Padatious and
        padacioso route it correctly."""
        _assert_match("who are you", P_HIGH, WHO, "en-US")
        _assert_match("who are you", PC_HIGH, WHO, "en-US")
        _assert_match("who are you", M_HIGH, MADE, "en-US")

    def test_introduce_yourself__padatious_low_only(self):
        """Short ``introduce yourself`` is too brief for padatious-high
        and -medium and absent from padacioso samples — only padatious-low
        and m2v match it."""
        _assert_match("introduce yourself", P_HIGH, None, "en-US")
        _assert_match("introduce yourself", P_MED, None, "en-US")
        _assert_match("introduce yourself", P_LOW, WHO, "en-US")
        _assert_match("introduce yourself", PC_HIGH, None, "en-US")
        _assert_match("introduce yourself", M_HIGH, WHO, "en-US")

    def test_what_is_your_date_of_birth__unsupported_by_m2v(self):
        """``what is your date of birth`` is unique enough in word choice
        that m2v misses it at every tier; padatious/padacioso match it."""
        _assert_match("what is your date of birth", P_HIGH, WHEN, "en-US")
        _assert_match("what is your date of birth", PC_HIGH, WHEN, "en-US")
        _assert_match("what is your date of birth", M_HIGH, None, "en-US")
        _assert_match("what is your date of birth", M_LOW, None, "en-US")

    def test_when_did_you_come_into_existence__m2v_medium_rescues_high(self):
        """m2v-high misses this paraphrase; m2v-medium recovers it.
        Documents the value of cascading m2v tiers."""
        _assert_match("when did you come into existence", M_HIGH, None, "en-US")
        _assert_match("when did you come into existence", M_MED, WHEN, "en-US")
