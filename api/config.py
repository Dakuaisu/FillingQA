"""Configuration and environment loading.

One place that reads `.env`, so the database layer and the EDGAR client cannot
disagree about where settings come from.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"
MIGRATIONS_DIR = REPO_ROOT / "infra" / "migrations"

# Matches docker-compose.yml, so a throwaway container needs no env file.
DEFAULT_DSN = "postgresql://filingqa:filingqa@localhost:5432/filingqa"

_loaded = False


def load_env(path: Path = ENV_FILE, force: bool = False) -> None:
    """Read KEY=VALUE lines from .env into os.environ.

    Deliberately not python-dotenv: a dozen lines for one file we control, and
    one fewer dependency to justify. A real environment variable always wins, so
    CI and shell overrides are never clobbered by a stale .env.
    """
    global _loaded
    if _loaded and not force:
        return
    _loaded = True

    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def dsn() -> str:
    load_env()
    return os.environ.get("DATABASE_URL", DEFAULT_DSN)


def data_dir() -> Path:
    load_env()
    return Path(os.environ.get("DATA_DIR", str(REPO_ROOT / "data")))


CORPUS_FILE = REPO_ROOT / "api" / "config.yaml"


def chunking(path: Path = CORPUS_FILE) -> dict:
    """The `chunking:` block of api/config.yaml (PRD 6.3, Appendix A)."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))["chunking"]


def baseline(path: Path = CORPUS_FILE) -> dict:
    """The `baseline:` block of api/config.yaml (PRD 14, Phase 2)."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))["baseline"]


def generation(path: Path = CORPUS_FILE) -> dict:
    """The `generation:` block of api/config.yaml (PRD Appendix A)."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))["generation"]


def span_resolution(path: Path = CORPUS_FILE) -> dict:
    """The `span_resolution:` block of api/config.yaml (PRD 14, Phase 2)."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))["span_resolution"]


def embedding(path: Path = CORPUS_FILE) -> dict:
    """The `embedding:` block of api/config.yaml (PRD 6.4)."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))["embedding"]


def parser_bounds(path: Path = CORPUS_FILE) -> dict:
    """The `parser:` block of api/config.yaml: validation-suite bounds."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))["parser"]


def companies(path: Path = CORPUS_FILE) -> dict[str, dict]:
    """Ticker -> {cik, sector, companyfacts_ciks}, as pinned in api/config.yaml."""
    out = {}
    for c in yaml.safe_load(path.read_text(encoding="utf-8"))["corpus"]["companies"]:
        cik = str(c["cik"])
        if len(cik) != 10 or not cik.isdigit():
            raise ConfigError(f"{c['ticker']}: cik {cik!r} is not a 10-digit string")
        out[c["ticker"].upper()] = {
            "cik": cik,
            "sector": c["sector"],
            "companyfacts_ciks": [str(x) for x in c.get("companyfacts_ciks", [cik])],
        }
    return out


def corpus_filings(path: Path = CORPUS_FILE) -> list[dict[str, str]]:
    """The frozen eval corpus: [{ticker, accession, form, period_end, filed}]."""
    corpus = yaml.safe_load(path.read_text(encoding="utf-8"))["corpus"]
    return [{k: str(v) for k, v in entry.items()} for entry in corpus["filings"]]


def dev_slice(path: Path = CORPUS_FILE) -> list[dict[str, str]]:
    """The dev slice as [{ticker, accession, form}], in file order."""
    corpus = yaml.safe_load(path.read_text(encoding="utf-8"))["corpus"]
    entries = corpus["dev_slice"]
    for entry in entries:
        missing = {"ticker", "accession", "form"} - entry.keys()
        if missing:
            raise ConfigError(f"dev_slice entry {entry!r} is missing {sorted(missing)}")
    return [{k: str(entry[k]) for k in ("ticker", "accession", "form")} for entry in entries]


# ---------------------------------------------------------------- user agent

_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")

# Rejected outright: a placeholder contact is no more use to SEC than none, and
# it is the single most likely thing to be left in by accident.
_PLACEHOLDER_DOMAINS = ("example.com", "example.org", "example.net", "email.com")


class ConfigError(RuntimeError):
    """Raised when configuration is missing or unusable."""


def sec_user_agent() -> str:
    """The User-Agent for every SEC request. Fails loudly rather than degrading.

    PRD 6.1 and PRD 16: SEC requires a descriptive User-Agent containing real
    contact information, and sending requests without one risks an IP block that
    costs days. There is no sensible fallback, so a missing or placeholder value
    is a hard stop before any request is attempted -- not a warning logged next
    to a request that already went out.
    """
    load_env()
    ua = os.environ.get("SEC_USER_AGENT", "").strip()

    if not ua:
        raise ConfigError(
            "SEC_USER_AGENT is not set. SEC requires a descriptive User-Agent "
            "containing real contact information (PRD 6.1); requests without one "
            "risk an IP block. Set it in .env, e.g.\n"
            '  SEC_USER_AGENT="FilingQA Research Project you@yourdomain.com"'
        )

    match = _EMAIL.search(ua)
    if not match:
        raise ConfigError(
            f"SEC_USER_AGENT does not contain an email address: {ua!r}. "
            "SEC requires reachable contact information in the header."
        )

    domain = match.group(0).rsplit("@", 1)[-1].lower()
    if domain in _PLACEHOLDER_DOMAINS:
        raise ConfigError(
            f"SEC_USER_AGENT still contains the placeholder address {match.group(0)!r}. "
            "Replace it with a real contact address before contacting SEC."
        )

    return ua
