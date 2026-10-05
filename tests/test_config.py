from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "vps.py"
spec = spec_from_file_location("vps", SCRIPT)
vps = module_from_spec(spec)
spec.loader.exec_module(vps)


def config(tmp_path, **changes):
    text = (SCRIPT.parents[1] / ".env.example").read_text()
    for name, value in changes.items():
        text = __import__("re").sub(rf"^{name}=.*$", f"{name}={value}", text, flags=__import__("re").M)
    path = tmp_path / ".env"
    path.write_text(text)
    return path


def test_example_has_valid_complete_plan(tmp_path):
    parsed = vps.load_env(config(tmp_path))
    assert parsed["HYSTERIA_PORT"] == "443"
    assert parsed["SSH_TARGET_PORT"] == "2322"
    assert "ACME_EMAIL" not in parsed


def test_keeping_current_ssh_port_is_supported(tmp_path):
    parsed = vps.load_env(config(tmp_path, CHANGE_SSH_PORT="no", SSH_TARGET_PORT="22"))
    assert parsed["SSH_TARGET_PORT"] == parsed["BOOTSTRAP_SSH_PORT"]


def test_public_panel_is_supported(tmp_path, capsys):
    parsed = vps.load_env(config(tmp_path, PANEL_ALLOWED_CIDRS="0.0.0.0/0"))
    vps.plan(parsed)
    assert "public IPv4" in capsys.readouterr().out


def test_hysteria_can_be_disabled_without_opening_udp(tmp_path, capsys):
    parsed = vps.load_env(config(tmp_path, ENABLE_HYSTERIA="no"))
    vps.plan(parsed)
    assert "no UDP allow" in capsys.readouterr().out


@pytest.mark.parametrize("changes", [
    {"PANEL_PORT": "443"},
    {"SUBSCRIPTION_PORT": "80"},
    {"CHANGE_SSH_PORT": "no"},
    {"SSH_TARGET_PORT": "22"},
])
def test_unsafe_or_conflicting_settings_fail(tmp_path, changes):
    with pytest.raises(ValueError):
        vps.load_env(config(tmp_path, **changes))


def test_dotenv_is_not_shell_code(tmp_path):
    path = config(tmp_path)
    path.write_text(path.read_text() + "\nUNEXPECTED=$(touch /tmp/should-not-run)\n")
    with pytest.raises(ValueError):
        vps.load_env(path)


def test_russian_example_matches_english_settings():
    root = SCRIPT.parents[1]
    english = vps.load_env(root / ".env.example")
    russian = vps.load_env(root / ".env.ru.example")
    assert russian == english


def test_close_ipv6_requires_apply_before_network(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["vps.py", "close-ipv6", "--env", str(config(tmp_path))])
    assert vps.main() == 1
    assert "--apply" in capsys.readouterr().err
