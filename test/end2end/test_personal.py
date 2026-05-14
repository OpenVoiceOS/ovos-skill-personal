# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""End-to-end intent tests for ovos-skill-personal.

Cases live as plain text under ``test/end2end/cases/<lang>/`` — see
``ovoscope.intent_cases`` for the full file-layout contract. Adding a
phrase, intent or whole new language is a pure text edit; no Python
changes needed.

This module is a thin caller around ``register_intent_case_tests``: it
maps each intent name to its handler method, points at the cases
directory, and the helper synthesises one ``TestCase`` per pipeline
family (Padatious, Padacioso, M2V, plus the default full stack), each
containing one method per (lang, utterance).

A separate ``TestPipelineDivergence`` class hand-curates borderline
utterances that route differently across pipelines/tiers, acting as
regression canaries against upstream pipeline model upgrades.
"""
from pathlib import Path
from unittest import TestCase

from ovoscope import (M2V_PIPELINE, PADACIOSO_PIPELINE, PADATIOUS_PIPELINE,
                      assert_intent_case, get_minicroft,
                      register_intent_case_tests)
from ovoscope.intent_cases import IntentCase

SKILL_ID = "ovos-skill-personal.openvoiceos"

HANDLERS = {
    "WhoAreYou.intent": "PersonalSkill.handle_who_are_you_intent",
    "WhatAreYou.intent": "PersonalSkill.handle_what_are_you_intent",
    "WhenWereYouBorn.intent": "PersonalSkill.handle_when_were_you_born_intent",
    "WhereWereYouBorn.intent": "PersonalSkill.handle_where_were_you_born_intent",
    "WhoMadeYou.intent": "PersonalSkill.handle_who_made_you_intent",
}

# Generates TestPadatious / TestPadacioso / TestM2V / TestDefaultPipeline in
# this module's namespace, each with one method per (lang, utterance) case.
register_intent_case_tests(
    globals(),
    skill_id=SKILL_ID,
    handlers=HANDLERS,
    cases_dir=Path(__file__).parent / "cases",
)


# ---------------------------------------------------------------------------
# Hand-curated cross-pipeline divergence canaries.
#
# These were observed by probing every utterance from the .test files
# against every pipeline/tier on this skill's locale. They document
# borderline routing differences so an upstream pipeline upgrade that
# silently changes the behaviour shows up as a failing test instead.
# ---------------------------------------------------------------------------
WHO = "WhoAreYou.intent"
WHEN = "WhenWereYouBorn.intent"
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
    """Borderline utterances whose routing differs across pipelines/tiers."""

    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if cls.minicroft:
            cls.minicroft.stop()

    def _run(self, utt, pipeline, expected):
        assert_intent_case(
            self.minicroft, SKILL_ID, HANDLERS,
            IntentCase(lang="en-US", utterance=utt, intent=expected,
                       source=Path("divergence")),
            pipeline)

    def test_who_made_you__padacioso_high_misses__medium_rescues(self):
        """padacioso-high is too strict for ``who made you``; -medium accepts."""
        self._run("who made you", PC_HIGH, None)
        self._run("who made you", PC_MED, MADE)
        self._run("who made you", P_HIGH, MADE)

    def test_who_are_you__m2v_misroutes_to_WhoMadeYou(self):
        """m2v embedding similarity routes ``who are you`` to WhoMadeYou."""
        self._run("who are you", P_HIGH, WHO)
        self._run("who are you", PC_HIGH, WHO)
        self._run("who are you", M_HIGH, MADE)

    def test_introduce_yourself__padatious_low_only(self):
        """Too short for padatious-high/-medium and absent from padacioso."""
        self._run("introduce yourself", P_HIGH, None)
        self._run("introduce yourself", P_MED, None)
        self._run("introduce yourself", P_LOW, WHO)
        self._run("introduce yourself", PC_HIGH, None)
        self._run("introduce yourself", M_HIGH, WHO)

    def test_what_is_your_date_of_birth__unsupported_by_m2v(self):
        """Unique enough in word choice that m2v misses at every tier."""
        self._run("what is your date of birth", P_HIGH, WHEN)
        self._run("what is your date of birth", PC_HIGH, WHEN)
        self._run("what is your date of birth", M_HIGH, None)
        self._run("what is your date of birth", M_LOW, None)

    def test_when_did_you_come_into_existence__m2v_medium_rescues_high(self):
        """m2v-high misses this paraphrase; m2v-medium recovers it."""
        self._run("when did you come into existence", M_HIGH, None)
        self._run("when did you come into existence", M_MED, WHEN)
