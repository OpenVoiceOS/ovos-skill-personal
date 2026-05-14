"""Local pytest config for the end2end suite.

Two responsibilities:

1. If ovoscope isn't installed (e.g. the build-tests workflow uses only
   the ``test`` extras and skips the ovoscope plugin), skip collecting
   anything in this directory — otherwise pytest errors on the
   ``from ovoscope import ...`` line in ``test_personal.py``.

2. When ovoscope IS available, inject sensible defaults for the
   accuracy reporter flags (tolerant mode + JSON + Markdown + a
   generous floor).
"""
from __future__ import annotations

try:
    import ovoscope  # noqa: F401
except ImportError:  # pragma: no cover - exercised only in CI
    # Tell pytest to skip every test module in this directory. Build-tests
    # workflow doesn't install ovoscope; the ovoscope workflow does.
    collect_ignore_glob = ["*.py"]


def pytest_configure(config):  # noqa: D401
    """Add ovoscope accuracy flags if the plugin registered them."""
    # ``--ovoscope-accuracy-tolerant`` is added by ovoscope.pytest_plugin
    # via pytest_addoption. If it isn't present we're being run without
    # ovoscope (e.g. the build-tests workflow); skip silently.
    try:
        config.getoption("--ovoscope-accuracy-tolerant")
    except (ValueError, KeyError):
        return

    # Enable tolerant mode + JSON + Markdown + a generous accuracy floor.
    # Tighten the floor as the pipelines stabilise; once a green report
    # exists, switch to --ovoscope-accuracy-baseline to block regressions.
    config.option.ovoscope_accuracy_tolerant = True
    if not config.option.ovoscope_accuracy_report:
        config.option.ovoscope_accuracy_report = "intent-accuracy.json"
    # The gh-automations ovoscope workflow already passes
    # --ovoscope-accuracy-md=/tmp/ovoscope-intent-accuracy.md when running
    # in CI; this default makes the local run also produce a markdown
    # artifact next to the JSON.
    if (hasattr(config.option, "ovoscope_accuracy_md")
            and not config.option.ovoscope_accuracy_md):
        config.option.ovoscope_accuracy_md = "intent-accuracy.md"
    if config.option.ovoscope_accuracy_min is None:
        config.option.ovoscope_accuracy_min = 0.5
