# write your first unittest!
import unittest
from os.path import join, dirname
import os
from ovos_utils.bracket_expansion import expand_parentheses, expand_options

from adapt.engine import IntentDeterminationEngine
from adapt.intent import IntentBuilder
from ovos_skill_personal import PersonalSkill
from ovos_plugin_manager.skills import find_skill_plugins
from ovos_utils.messagebus import FakeBus
from mycroft.skills.skill_loader import PluginSkillLoader, SkillLoader


class TestSkillLoading(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.skill_id = "ovos-skill-personal.openvoiceos"
        self.path = dirname(dirname(dirname(__file__)))

    def test_from_class(self):
        bus = FakeBus()
        skill = PersonalSkill()
        skill._startup(bus, self.skill_id)
        self.assertEqual(skill.bus, bus)
        self.assertEqual(skill.skill_id, self.skill_id)

    def test_from_plugin(self):
        bus = FakeBus()
        for skill_id, plug in find_skill_plugins().items():
            if skill_id == self.skill_id:
                skill = plug()
                skill._startup(bus, self.skill_id)
                self.assertEqual(skill.bus, bus)
                self.assertEqual(skill.skill_id, self.skill_id)
                break
        else:
            raise RuntimeError("plugin not found")

    def test_from_plugin_loader(self):
        bus = FakeBus()
        loader = PluginSkillLoader(bus, self.skill_id)
        for skill_id, plug in find_skill_plugins().items():
            if skill_id == self.skill_id:
                loader.load(plug)
                break
        else:
            raise RuntimeError("plugin not found")

        self.assertEqual(loader.skill_id, self.skill_id)
        self.assertEqual(loader.instance.bus, bus)
        self.assertEqual(loader.instance.skill_id, self.skill_id)


