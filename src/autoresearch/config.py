from __future__ import annotations

import os
from pathlib import Path


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    if not key:
        return None
    return key, value


def load_local_env(path: Path | str = ".env") -> list[str]:
    """Load simple KEY=VALUE pairs from a local .env file without overriding shell env."""

    env_path = Path(path)
    if not env_path.exists():
        return []
    loaded: list[str] = []
    for line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(line)
        if not parsed:
            continue
        key, value = parsed
        if key in os.environ:
            continue
        os.environ[key] = value
        loaded.append(key)
    return loaded


def redact_email(value: str) -> str:
    if "@" not in value:
        return value
    name, domain = value.split("@", 1)
    prefix = name[:2] if len(name) > 2 else name[:1]
    return f"{prefix}***@{domain}"


def sanitize_error(text: str) -> str:
    email = os.getenv("UNPAYWALL_EMAIL", "").strip()
    if email:
        text = text.replace(email, redact_email(email))
    return text
