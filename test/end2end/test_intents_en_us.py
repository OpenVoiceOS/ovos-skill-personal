"""End-to-end intent routing tests for the en-US locale.

Each canonical utterance is fired through a real MiniCroft and asserted to
route to the expected intent handler and produce a spoken response. The reply
text depends on runtime configuration, so assertions cover the intent binding
and the presence of a ``speak`` response, not the dialog content.
"""
import re
import unittest

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "ovos-skill-personal.openvoiceos"


def _matches_intent(msg_type: str, skill_id: str, intent_file: str) -> bool:
    """Check whether ``msg_type`` is the matched-intent event for
    ``intent_file`` (eg. ``WhoAreYou.intent``), tolerant of which pipeline
    plugin matched it.

    Different pipeline plugins (padatious vs padacioso) register intents
    under different normalizations of the ``.intent`` filename basename —
    observed variants include the literal PascalCase basename with no
    extension (``WhoAreYou``) and the snake_case basename with the
    extension kept (``who_are_you.intent``). Rather than pin one wire
    format (which breaks the moment the matching plugin or its version
    changes), compare case-insensitively against the basename with the
    extension stripped from both sides.
    """
    prefix = f"{skill_id}:"
    if not msg_type.startswith(prefix):
        return False
    observed = msg_type[len(prefix):]
    observed_base = observed.rsplit(".", 1)[0] if observed.endswith(".intent") else observed
    expected_base = intent_file.rsplit(".", 1)[0]
    # normalize PascalCase/snake_case to a bare lowercase token for comparison
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    return norm(observed_base) == norm(expected_base)


class TestPersonalIntentsEnUS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        cls.minicroft.stop()

    def _run(self, text):
        session = Session("test-session")
        session.pipeline = [
            "ovos-adapt-pipeline-plugin-high",
            "ovos-padatious-pipeline-plugin-high",
            "ovos-padacioso-pipeline-plugin-high",
            "ovos-adapt-pipeline-plugin-medium",
            "ovos-padacioso-pipeline-plugin-medium",
            "ovos-adapt-pipeline-plugin-low",
        ]
        utterance = Message(
            "recognizer_loop:utterance",
            {"utterances": [text], "lang": "en-US"},
            {"session": session.serialize(), "source": "A", "destination": "B"},
        )
        capture = CaptureSession(self.minicroft)
        capture.capture(utterance, timeout=30)
        return capture.finish()

    def _assert_intent(self, text, intent):
        messages = self._run(text)
        types = [m.msg_type for m in messages]
        self.assertTrue(
            any(_matches_intent(t, SKILL_ID, intent) for t in types),
            f"no message routed to {SKILL_ID}:{intent} ({types})",
        )
        self.assertTrue(any("speak" in t for t in types))

    def test_who_are_you(self):
        self._assert_intent("tell me about yourself", "WhoAreYou.intent")

    def test_what_are_you(self):
        self._assert_intent("describe what you are", "WhatAreYou.intent")

    def test_who_made_you(self):
        self._assert_intent("by whom were you created", "WhoMadeYou.intent")

    def test_when_were_you_born(self):
        self._assert_intent("what is your date of birth", "WhenWereYouBorn.intent")

    def test_where_were_you_born(self):
        self._assert_intent("where do you come from", "WhereWereYouBorn.intent")


if __name__ == "__main__":
    unittest.main()
