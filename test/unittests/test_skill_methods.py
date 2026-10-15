from unittest.mock import Mock
from ovos_skill_personal import PersonalSkill

WW_COMBOS = [
        # Precise
        ["hey_mycroft", "mycroft"],
        ["hey_neon", "neon"],
        ["android", "android"],
        ["computer", "computer"],
        ["hey_chatterbox", "chatterbox"],
        ["hey_firefox", "firefox"],
        ["hey_k9", "k9"],
        ["hey_kit", "kit"],
        ["hey_moxie", "moxie"],
        ["hey_scout", "scout"],
        ["marvin", "marvin"],
        ["o_sauro", "sauro"],
        ["sheila", "sheila"],
        # OpenWakeWord
        ["alexa", "alexa"],
        ["hey_rhasspy", "rhasspy"],
        ["hey_jarvis", "jarvis"],
        # Snowboy
        ["hey_extreme", "extreme"],
        ["jarvis", "jarvis"],
        ["snowboy", "snowboy"],
        ["smart_mirror", "smart mirror"],
        ["subex", "subex"],
        ["neoya", "neoya"],
        ["view_glass", "view glass"],
        # Vosk
        ["hey_ziggy", "ziggy"],
        ["hey ziggy", "ziggy"],
        ["jarbas", "jarbas"],
        ["computador", "computador"],
        ["hey mycroft", "mycroft"],
        ["hey neon", "neon"],
        ["hey jarvis", "jarvis"],
        ["hey computer", "computer"],
        # Community dataset
        ["hey_savant", "savant"],
        ["hey_floyd", "floyd"],
        ["hey_ordenador", "ordenador"],
        ["amelia", "amelia"],
        ["athena", "athena"],
        ["christopher", "christopher"],
        ["hey_mike", "mike"],
        ["ei_computador", "computador"],
        ["ei_jarbas", "jarbas"],
        ["ei_lara", "lara"],
        ["ó_computador", "computador"],
        ["ó_flôr", "flôr"],
        ["ó_inês", "inês"],
        ["ó_jarbas", "jarbas"],
        ["ó_sauro", "sauro"],
        ["ó_televisão", "televisão"],
        # Nyumaya
        ["firefox", "firefox"],
        # PocketSphinx
        ["andromeda", "andromeda"],
        ["dinossauro", "dinossauro"],
        # auto-synth-dataset
        ["arisa", "arisa"],
        ["bartleby", "bartleby"],
        ["hey_andromeda", "andromeda"],
        ["hey_eggbert", "eggbert"],
        ["hey_ezra", "ezra"],
        ["hey_robin", "robin"],
        ["hey_rodney", "rodney"],
        ["lazarus", "lazarus"],
        ["ovos", "ovos"],
        ["say_jeeves", "jeeves"],
        ["wilberforce", "wilberforce"],
    ]

def test_parse_name_from_ww():
    skill = PersonalSkill()
    for combo in WW_COMBOS:
        ww, name = combo
        assert skill._parse_name_from_ww(ww) == name

def test_handle_who_are_you_intent_setting_overrides_ww():
    skill = PersonalSkill(settings={"assistant_name": "test"})
    skill.speak_dialog = Mock()
    skill.handle_who_are_you_intent(None)
    skill.speak_dialog.assert_called_once_with("who_am_i", {"name": "test"})

def test_handle_who_are_you_intent():
    skill = PersonalSkill()
    skill.speak_dialog = Mock()
    skill.config_core = {"listener": {"wake_word": "hey_jarbas"}}
    skill.handle_who_are_you_intent(None)
    skill.speak_dialog.assert_called_once_with("who_am_i", {"name": "jarbas"})

def test_handle_who_are_you_no_ww_default():
    skill = PersonalSkill()
    skill.speak_dialog = Mock()
    skill.config_core = {"listener": {}}
    skill.handle_who_are_you_intent(None)
    skill.speak_dialog.assert_called_once_with("who_am_i", {"name": "mycroft"})
