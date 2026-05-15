# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""File-based intent-case suite for ovos-skill-personal.

Cases live as plain text under ``test/end2end/cases/<lang>/`` — see
``ovoscope.intent_cases`` for the full file-layout contract. Adding a
phrase, intent or whole new language is a pure text edit; no Python
changes needed.

This module is a thin caller around ``register_intent_case_tests``: it
maps each intent name to its handler method, points at the cases
directory, and the helper synthesises one ``TestCase`` per pipeline
family (Padatious, Padacioso, M2V, plus the default full stack), each
containing one method per (lang, utterance).

Hand-curated pipeline divergence canaries (one-off cross-pipeline
borderline routing) live in the sibling ``test_personal.py`` and run
under the generic ovoscope workflow.
"""
from pathlib import Path

from ovoscope import register_intent_case_tests

SKILL_ID = "ovos-skill-personal.openvoiceos"

HANDLERS = {
    "WhoAreYou.intent": "PersonalSkill.handle_who_are_you_intent",
    "WhatAreYou.intent": "PersonalSkill.handle_what_are_you_intent",
    "WhenWereYouBorn.intent": "PersonalSkill.handle_when_were_you_born_intent",
    "WhereWereYouBorn.intent": "PersonalSkill.handle_where_were_you_born_intent",
    "WhoMadeYou.intent": "PersonalSkill.handle_who_made_you_intent",
}

register_intent_case_tests(
    globals(),
    skill_id=SKILL_ID,
    handlers=HANDLERS,
    cases_dir=Path(__file__).parent / "cases",
)

# Marker consumed by ovoscope's auto-discovery hook.
ovoscope_intent_cases = dict(skill_id=SKILL_ID, handlers=HANDLERS)
_ovoscope_intent_cases_registered = True
