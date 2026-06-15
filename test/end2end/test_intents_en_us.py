"""E2E intent-routing tests for ovos-skill-personal.

Run: pytest test/end2end/ -v
"""
from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import End2EndTest, get_minicroft

SKILL_ID = "ovos-skill-personal.openvoiceos"
LANG = "en-US"


class _IntentRoutingMixin:
    """Shared MiniCroft setup."""

    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'minicroft', None):
            cls.minicroft.stop()

    def _assert_padacioso(self, utterance: str, intent_file: str):
        intent_msg_type = f"{SKILL_ID}:{intent_file}"
        session = Session(f"e2e-en_us-{intent_file}-{hash(utterance)}")
        session.lang = LANG
        session.pipeline = ["ovos-padacioso-pipeline-plugin-medium"]
        message = Message(
            "recognizer_loop:utterance",
            {"utterances": [utterance], "lang": LANG},
            {"session": session.serialize()},
        )
        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            source_message=message,
            activation_points=[intent_msg_type],
            test_msg_context=False,
            ignore_messages=["speak", "mycroft.audio.play_sound"],
            test_message_number=False,
            expected_messages=[
                message,
                Message(f"{SKILL_ID}.activate", {}, {"skill_id": SKILL_ID}),
                Message(intent_msg_type, {}, {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.start", {}, {"skill_id": SKILL_ID}),
                Message("mycroft.skill.handler.complete", {}, {"skill_id": SKILL_ID}),
                Message("ovos.utterance.handled", {}, {"skill_id": SKILL_ID}),
            ],
        )
        test.execute(timeout=30)


class TestPadacioso1_WhatAreYou_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: WhatAreYou.intent"""
    def test_what_are_you(self):
        self._assert_padacioso(r"what are you", r"WhatAreYou.intent")

    def test_define_yourself(self):
        self._assert_padacioso(r"define yourself", r"WhatAreYou.intent")

    def test_what_is_your_nature(self):
        self._assert_padacioso(r"what is your nature", r"WhatAreYou.intent")


class TestPadacioso2_WhoAreYou_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: WhoAreYou.intent"""
    def test_who_are_you(self):
        self._assert_padacioso(r"who are you", r"WhoAreYou.intent")

    def test_what_is_your_name(self):
        self._assert_padacioso(r"what is your name", r"WhoAreYou.intent")

    def test_tell_me_about_yourself(self):
        self._assert_padacioso(r"tell me about yourself", r"WhoAreYou.intent")


class TestPadacioso3_WhoMadeYou_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: WhoMadeYou.intent"""
    def test_who_made_you(self):
        self._assert_padacioso(r"Who made you", r"WhoMadeYou.intent")

    def test_who_created_you(self):
        self._assert_padacioso(r"Who created you", r"WhoMadeYou.intent")

    def test_who_is_your_creator(self):
        self._assert_padacioso(r"Who is your creator", r"WhoMadeYou.intent")


class TestPadacioso4_WhenWereYouBorn_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: WhenWereYouBorn.intent"""
    def test_when_were_you_born(self):
        self._assert_padacioso(r"when were you born", r"WhenWereYouBorn.intent")

    def test_when_were_you_created(self):
        self._assert_padacioso(r"when were you created", r"WhenWereYouBorn.intent")

    def test_what_is_your_date_of_birth(self):
        self._assert_padacioso(r"what is your date of birth", r"WhenWereYouBorn.intent")


class TestPadacioso5_WhereWereYouBorn_intent(_IntentRoutingMixin, TestCase):
    """Padacioso intent: WhereWereYouBorn.intent"""
    def test_where_were_you_born(self):
        self._assert_padacioso(r"where were you born", r"WhereWereYouBorn.intent")

    def test_where_were_you_created(self):
        self._assert_padacioso(r"where were you created", r"WhereWereYouBorn.intent")

    def test_where_do_you_come_from(self):
        self._assert_padacioso(r"where do you come from", r"WhereWereYouBorn.intent")
