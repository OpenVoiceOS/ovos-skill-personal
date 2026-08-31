"""Per-utterance intent-routing assertions for the identity intents.

Positive routing:
    Each ``cases/<lang>/<Intent>.intent.test`` file lists utterances that
    must route to that intent. Every ``(lang, utterance)`` pair discovered
    via ovoscope's ``register_intent_case_tests`` becomes its own generated
    test method on ``TestPadatious``. Adding coverage is a pure text edit to
    the ``cases/`` files — no Python.

Negative routing:
    ``TestNoIdentityIntentMatch`` fires unrelated utterances and asserts
    that none of this skill's intent handlers is triggered. It watches the
    concrete ``<skill_id>:<intent>`` topics directly rather than the
    pipeline's failure signal, so it is immune to the failure topic being
    renamed (``complete_intent_failure`` -> ``ovos.intent.unmatched``).
"""
from pathlib import Path
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils.log import LOG

from ovoscope import PADATIOUS_PIPELINE, get_minicroft
from ovoscope.intent_cases import (DEFAULT_IGNORE_MESSAGES,
                                   canonical_intent,
                                   register_intent_case_tests)

SKILL_ID = "ovos-skill-personal.openvoiceos"

# {"<IntentName>.intent": "<Class>.<handler_method>"} for every intent
# referenced by the case files.
HANDLERS = {
    "what_are_you.intent": "PersonalSkill.handle_what_are_you_intent",
    "who_are_you.intent": "PersonalSkill.handle_who_are_you_intent",
    "who_made_you.intent": "PersonalSkill.handle_who_made_you_intent",
    "when_were_you_born.intent": "PersonalSkill.handle_when_were_you_born_intent",
    "where_were_you_born.intent": "PersonalSkill.handle_where_were_you_born_intent",
}

# ovos-core emits book-keeping around the concrete intent trigger that is not
# part of the routing contract under test; keep the assertion focused on which
# intent handler the utterance reaches.
IGNORED = list(DEFAULT_IGNORE_MESSAGES) + [
    "ovos.utterance.speak",
    "recognizer_loop:audio_output_start",
    "recognizer_loop:audio_output_end",
    "ovos.intent.matched",
    "ovos.intent.handler.start",
    "ovos.intent.handler.complete",
]

# The skill ships padatious ``.intent`` files, so only the padatious pipeline
# family is exercised here.
register_intent_case_tests(
    globals(),
    skill_id=SKILL_ID,
    handlers=HANDLERS,
    cases_dir=Path(__file__).parent / "cases",
    pipelines={"Padatious": PADATIOUS_PIPELINE},
    ignore_messages=IGNORED,
)


# Utterances unrelated to the identity intents; none must reach this skill.
NO_MATCH_UTTERANCES = [
    "what time is it",
    "tell me a joke",
    "set an alarm for seven am",
    "what is the weather like today",
]

# the concrete intent-trigger topics this skill would emit on a match
_INTENT_TOPICS = [f"{SKILL_ID}:{canonical_intent(name)}" for name in HANDLERS]


class TestNoIdentityIntentMatch(TestCase):
    """Assert unrelated utterances do not trigger any identity intent."""

    @classmethod
    def setUpClass(cls):
        LOG.set_level("CRITICAL")
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if cls.minicroft:
            cls.minicroft.stop()

    def _assert_no_match(self, utterance):
        import threading

        matched = []
        handled = threading.Event()

        def on_intent(msg):
            matched.append(msg.msg_type)

        def on_handled(_):
            handled.set()

        for topic in _INTENT_TOPICS:
            self.minicroft.bus.on(topic, on_intent)
        self.minicroft.bus.on("ovos.utterance.handled", on_handled)
        try:
            session = Session("no-match")
            session.pipeline = list(PADATIOUS_PIPELINE)
            self.minicroft.bus.emit(Message(
                "recognizer_loop:utterance",
                {"utterances": [utterance], "lang": "en-US"},
                {"session": session.serialize()}))
            handled.wait(timeout=15)
        finally:
            for topic in _INTENT_TOPICS:
                self.minicroft.bus.remove(topic, on_intent)
            self.minicroft.bus.remove("ovos.utterance.handled", on_handled)

        self.assertEqual(
            matched, [],
            f"{utterance!r} unexpectedly triggered identity intent(s): {matched}")

    def test_no_match(self):
        for utterance in NO_MATCH_UTTERANCES:
            with self.subTest(utterance=utterance):
                self._assert_no_match(utterance)
