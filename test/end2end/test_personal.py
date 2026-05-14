# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""End-to-end tests for ovos-skill-personal using ovoscope.

Verifies that the four Padatious intents (WhoAreYou, WhatAreYou,
WhenWereYouBorn, WhereWereYouBorn, WhoMadeYou) are matched and the
corresponding handler fires with the expected bus message sequence.

The skill emits non-deterministic ``speak`` content (dialogs contain
alternative phrasings), so ``speak`` messages are ignored and only the
intent-routing / handler-lifecycle messages are asserted.

Run:
    uv run pytest test/end2end/ -v
"""
from copy import deepcopy
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils.log import LOG
from ovoscope import End2EndTest, get_minicroft

SKILL_ID = "ovos-skill-personal.openvoiceos"

_IGNORE = [
    "speak",
    "ovos.common_play.stop.response",
    "common_query.openvoiceos.stop.response",
    "persona.openvoiceos.stop.response",
    "ovos-hivemind-pipeline-plugin.stop.response",
    "stop.openvoiceos.stop.response",
]


class _PersonalE2EBase(TestCase):
    """Shared fixture: one minicroft per test class with Padatious enabled."""

    @classmethod
    def setUpClass(cls):
        LOG.set_level("DEBUG")
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if cls.minicroft:
            cls.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _assert_intent(self, utterance: str, intent_name: str, handler: str,
                       lang: str = "en-US") -> None:
        session = Session(f"personal-{intent_name}")
        session.lang = lang
        session.pipeline = ["ovos-padatious-pipeline-plugin-high"]

        message = Message(
            "recognizer_loop:utterance",
            {"utterances": [utterance], "lang": lang},
            {"session": session.serialize()},
        )

        final_session = deepcopy(session)
        final_session.active_skills = [(SKILL_ID, 0.0)]

        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=_IGNORE,
            source_message=message,
            final_session=final_session,
            activation_points=[f"{SKILL_ID}:{intent_name}"],
            expected_messages=[
                message,
                Message(f"{SKILL_ID}.activate", {}, {"skill_id": SKILL_ID}),
                Message(f"{SKILL_ID}:{intent_name}",
                        {"utterance": utterance, "lang": lang},
                        {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.start",
                        {"name": handler},
                        {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.complete",
                        {"name": handler},
                        {"skill_id": SKILL_ID}),
                Message("ovos.utterance.handled", {}, {"skill_id": SKILL_ID}),
            ],
        )
        test.execute(timeout=30)


class TestWhoAreYou(_PersonalE2EBase):
    def test_who_are_you(self):
        self._assert_intent(
            "who are you",
            "WhoAreYou.intent",
            "PersonalSkill.handle_who_are_you_intent",
        )

    def test_what_is_your_name(self):
        self._assert_intent(
            "what is your name",
            "WhoAreYou.intent",
            "PersonalSkill.handle_who_are_you_intent",
        )


class TestWhatAreYou(_PersonalE2EBase):
    def test_what_are_you(self):
        self._assert_intent(
            "what are you",
            "WhatAreYou.intent",
            "PersonalSkill.handle_what_are_you_intent",
        )


class TestWhenWereYouBorn(_PersonalE2EBase):
    def test_when_were_you_born(self):
        self._assert_intent(
            "when were you born",
            "WhenWereYouBorn.intent",
            "PersonalSkill.handle_when_were_you_born_intent",
        )

    def test_what_is_your_date_of_birth(self):
        self._assert_intent(
            "what is your date of birth",
            "WhenWereYouBorn.intent",
            "PersonalSkill.handle_when_were_you_born_intent",
        )


class TestWhereWereYouBorn(_PersonalE2EBase):
    def test_where_were_you_born(self):
        self._assert_intent(
            "where were you born",
            "WhereWereYouBorn.intent",
            "PersonalSkill.handle_where_were_you_born_intent",
        )

    def test_where_do_you_come_from(self):
        self._assert_intent(
            "where do you come from",
            "WhereWereYouBorn.intent",
            "PersonalSkill.handle_where_were_you_born_intent",
        )


class TestWhoMadeYou(_PersonalE2EBase):
    def test_who_made_you(self):
        self._assert_intent(
            "who made you",
            "WhoMadeYou.intent",
            "PersonalSkill.handle_who_made_you_intent",
        )

    def test_who_created_you(self):
        self._assert_intent(
            "who created you",
            "WhoMadeYou.intent",
            "PersonalSkill.handle_who_made_you_intent",
        )
