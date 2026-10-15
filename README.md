# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/smile-wink.svg' card_color='#22a7f0' width='50' height='50' style='vertical-align:bottom'/> Assistant's Background
![Supported Python Versions](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/mikejgray/.github/main/python-versions.json)

This [OpenVoiceOS](https://github.com/OpenVoiceOS) skill answers basic questions about the assistant's identity, such as when and where it was created and who made it. It speaks a canned dialog filled with values from the skill settings, and needs no internet or network access to work.

## Install

Install the skill with pip, or through the OVOS skill store on a running OVOS device.

```console
pip install ovos-skill-personal
```

## Usage

Set the assistant's identity in `settings.json`:

```json
{
  "year_of_birth": 2015,
  "location_of_birth": "Lawrence Kansas",
  "creator": "OpenVoiceOS",
  "assistant_name": "Mycroft"
}
```

If `assistant_name` is not set, the skill derives a name from the configured wake word.

Ask the assistant:
* "When were you created?"
* "What are you?"
* "Where were you born?"
* "Who made you?"

## Related projects

* [OpenVoiceOS/ovos-core](https://github.com/OpenVoiceOS/ovos-core): the assistant core that loads this skill.
* [OpenVoiceOS/ovos-workshop](https://github.com/OpenVoiceOS/ovos-workshop): the skill base classes and decorators this skill builds on.

## Credits
OpenVoiceOS ([@OpenVoiceOS](https://github.com/OpenVoiceOS))
Mycroft AI ([@MycroftAI](https://github.com/MycroftAI))

## Category
**Entertainment**

## Tags
#personality
#persona

## License
See [LICENSE](LICENSE).
