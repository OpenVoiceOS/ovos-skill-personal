from unittest import TestCase

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovos_utils.log import LOG

from ovoscope import End2EndTest, get_minicroft

SKILL_ID = "ovos-skill-personal.openvoiceos"

# one representative utterance per identity intent, paired with the handler it
# must reach. Each utterance is a distinct expansion branch of its .intent file.
CASES = [
    ("what_are_you", "handle_what_are_you_intent", "what kind of thing are you"),
    ("who_are_you", "handle_who_are_you_intent", "what is your name"),
    ("who_made_you", "handle_who_made_you_intent", "who created you"),
    ("when_were_you_born", "handle_when_were_you_born_intent", "how old are you"),
    ("where_were_you_born", "handle_where_were_you_born_intent", "where do you come from"),
]

# the assistant's spoken answer and its audio-output signalling are not asserted
# here; this test pins only intent routing to the correct handler
IGNORED = [
    "speak",
    "ovos.utterance.speak",
    "recognizer_loop:audio_output_start",
    "recognizer_loop:audio_output_end",
    # pipeline bookkeeping around the concrete skill intent trigger
    "ovos.intent.matched",
    "ovos.intent.handler.start",
    "ovos.intent.handler.complete",
]


class TestPersonalIntents(TestCase):

    def setUp(self):
        LOG.set_level("DEBUG")
        self.minicroft = get_minicroft([SKILL_ID])

    def tearDown(self):
        if self.minicroft:
            self.minicroft.stop()
        LOG.set_level("CRITICAL")

    def _run(self, intent_name, handler, utterance):
        session = Session("test")
        session.pipeline = ["ovos-padatious-pipeline-plugin-high"]
        message = Message("recognizer_loop:utterance",
                          {"utterances": [utterance], "lang": "en-US"},
                          {"session": session.serialize()})
        test = End2EndTest(
            minicroft=self.minicroft,
            skill_ids=[SKILL_ID],
            eof_msgs=["ovos.utterance.handled"],
            flip_points=["recognizer_loop:utterance"],
            ignore_messages=IGNORED,
            source_message=message,
            expected_messages=[
                message,
                Message(f"{SKILL_ID}.activate", {}),
                # ovos-padatious >= 2.0 emits the OVOS-INTENT-4 canonical
                # suffixless intent id on match (folded at registration time).
                Message(f"{SKILL_ID}:{intent_name}", {}),
                Message("mycroft.skill.handler.start",
                        {"name": f"PersonalSkill.{handler}"}),
                Message("mycroft.skill.handler.complete",
                        {"name": f"PersonalSkill.{handler}"}),
                Message("ovos.utterance.handled", {}),
            ],
        )
        test.execute()

    def test_intents(self):
        for intent_name, handler, utterance in CASES:
            with self.subTest(intent=intent_name):
                self._run(intent_name, handler, utterance)
