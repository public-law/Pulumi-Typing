from pathlib import Path

from pulumi_typing.transform import extract_values, transform

FIXTURE = Path(__file__).parent / "fixtures" / "ruleset.pyi"


def test_real_sdk_docstring_values():
    assert extract_values('Available values: "managed", "custom", "root", "zone".') == (
        "managed", "custom", "root", "zone"
    )


def test_ambiguous_documentation_is_not_interpreted():
    assert extract_values("Available values depend on your account.") == ()


def test_real_world_ruleset_fixture(tmp_path):
    stubs = tmp_path / "pulumi_cloudflare"
    stubs.mkdir()
    sources = tmp_path / "source"
    sources.mkdir()
    target = stubs / "ruleset.pyi"
    target.write_text(FIXTURE.read_text())

    assert transform(stubs, sources) == 1
    transformed = target.read_text()
    assert "kind: pulumi.Input[Literal['managed', 'custom', 'root', 'zone']]" in transformed
    assert "name: pulumi.Input[_builtins.str]" in transformed
    assert "from typing import Literal, " in transformed
    assert '"allowed_values": [' in (tmp_path / "constraints.json").read_text()
    assert transform(stubs, sources) == 0
