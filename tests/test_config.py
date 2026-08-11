import os

from autoresearch.config import load_local_env, sanitize_error


def test_load_local_env_does_not_override_shell_env(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("UNPAYWALL_EMAIL=file@example.com\nEXTRA_FLAG=yes\n", encoding="utf-8")
    monkeypatch.setenv("UNPAYWALL_EMAIL", "shell@example.com")
    monkeypatch.delenv("EXTRA_FLAG", raising=False)

    loaded = load_local_env(env_path)

    assert loaded == ["EXTRA_FLAG"]
    assert os.environ["UNPAYWALL_EMAIL"] == "shell@example.com"
    assert os.environ["EXTRA_FLAG"] == "yes"


def test_sanitize_error_redacts_unpaywall_email(monkeypatch):
    monkeypatch.setenv("UNPAYWALL_EMAIL", "person@example.com")

    message = sanitize_error("GET https://api.unpaywall.org/v2/10.x?email=person@example.com")

    assert "person@example.com" not in message
    assert "pe***@example.com" in message
