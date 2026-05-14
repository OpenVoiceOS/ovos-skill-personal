# Copyright 2024 OpenVoiceOS
# Licensed under the Apache License, Version 2.0
"""End-to-end tests for ovos-skill-personal using ovoscope.

Verifies that the five Padatious intents (WhoAreYou, WhatAreYou,
WhenWereYouBorn, WhereWereYouBorn, WhoMadeYou) are matched and the
corresponding handler fires with the expected bus message sequence,
across the three supported intent pipelines:

  - padatious   (ovos-padatious-pipeline-plugin-high)
  - padacioso   (ovos-padacioso-pipeline-plugin-high)
  - m2v         (ovos-m2v-pipeline-high)

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

# (utterance, intent_name, handler_method)
_INTENT_CASES = [
    ("who are you", "WhoAreYou.intent",
     "PersonalSkill.handle_who_are_you_intent"),
    ("what is your name", "WhoAreYou.intent",
     "PersonalSkill.handle_who_are_you_intent"),
    ("what are you", "WhatAreYou.intent",
     "PersonalSkill.handle_what_are_you_intent"),
    ("when were you born", "WhenWereYouBorn.intent",
     "PersonalSkill.handle_when_were_you_born_intent"),
    ("what is your date of birth", "WhenWereYouBorn.intent",
     "PersonalSkill.handle_when_were_you_born_intent"),
    ("where were you born", "WhereWereYouBorn.intent",
     "PersonalSkill.handle_where_were_you_born_intent"),
    ("where do you come from", "WhereWereYouBorn.intent",
     "PersonalSkill.handle_where_were_you_born_intent"),
    ("who made you", "WhoMadeYou.intent",
     "PersonalSkill.handle_who_made_you_intent"),
    ("who created you", "WhoMadeYou.intent",
     "PersonalSkill.handle_who_made_you_intent"),
]


class _PersonalE2EBase(TestCase):
    """Shared fixture: one minicroft per test class.

    Subclasses set ``PIPELINE`` to the pipeline plugin id under test.
    """

    PIPELINE: str = ""  # override in subclass

    @classmethod
    def setUpClass(cls):
        if cls is _PersonalE2EBase:
            raise TestCase.skipTest(cls, "base class")
        LOG.set_level("DEBUG")
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _assert_intent(self, utterance: str, intent_name: str, handler: str,
                       lang: str = "en-US") -> None:
        session = Session(f"personal-{self.PIPELINE}-{intent_name}")
        session.lang = lang
        session.pipeline = [self.PIPELINE]

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


def _make_test_method(utterance, intent_name, handler):
    def _test(self):
        self._assert_intent(utterance, intent_name, handler)
    _test.__doc__ = f"{intent_name} matched for '{utterance}'"
    return _test


def _attach_cases(cls):
    for utt, intent, handler in _INTENT_CASES:
        safe = utt.replace(" ", "_")
        cls_method = _make_test_method(utt, intent, handler)
        setattr(cls, f"test_{intent.replace('.', '_')}__{safe}", cls_method)
    return cls


@_attach_cases
class TestPadatiousPipeline(_PersonalE2EBase):
    """Intents matched via the Padatious pipeline."""
    PIPELINE = "ovos-padatious-pipeline-plugin-high"


@_attach_cases
class TestPadaciosoPipeline(_PersonalE2EBase):
    """Intents matched via the Padacioso pipeline."""
    PIPELINE = "ovos-padacioso-pipeline-plugin-high"


@_attach_cases
class TestM2VPipeline(_PersonalE2EBase):
    """Intents matched via the Model2Vec (m2v) pipeline."""
    PIPELINE = "ovos-m2v-pipeline-high"
