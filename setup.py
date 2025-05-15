#!/usr/bin/env python3
import os
from os import walk
from os.path import abspath, dirname, join, isdir

from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    """ Find the version of the package"""
    version_file = os.path.join(BASEDIR, 'version.py')
    major, minor, build, alpha = (None, None, None, None)
    with open(version_file) as f:
        for line in f:
            if 'VERSION_MAJOR' in line:
                major = line.split('=')[1].strip()
            elif 'VERSION_MINOR' in line:
                minor = line.split('=')[1].strip()
            elif 'VERSION_BUILD' in line:
                build = line.split('=')[1].strip()
            elif 'VERSION_ALPHA' in line:
                alpha = line.split('=')[1].strip()

            if ((major and minor and build and alpha) or
                    '# END_VERSION_BLOCK' in line):
                break
    version = f"{major}.{minor}.{build}"
    if alpha and int(alpha) > 0:
        version += f"a{alpha}"
    return version


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


def find_resource_files():
    resource_base_dirs = ("locale", "gui", "res")
    base_dir = abspath(dirname(__file__))
    package_data = ["*.json"]
    for res in resource_base_dirs:
        if isdir(join(base_dir, res)):
            for (directory, _, files) in walk(join(base_dir, res)):
                if files:
                    package_data.append(join(directory.replace(base_dir, "").lstrip('/'), '*'))
    return package_data


# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'ovos-skill-personal.openvoiceos=ovos_skill_personal:PersonalSkill'
# in this case the skill_id is defined to purposefully replace the mycroft version of the skill,
# or rather to be replaced by it in case it is present. all skill directories take precedence over plugin skills


setup(
    # this is the package name that goes on pip
    name='ovos-skill-personal',
    version=get_version(),
    description='OVOS personal skill plugin',
    url='https://github.com/OpenVoiceOS/ovos-skill-personal',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"ovos_skill_personal": ""},
    package_data={'ovos_skill_personal': find_resource_files()},
    packages=['ovos_skill_personal'],
    include_package_data=True,
    install_requires=required("requirements.txt"),
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
