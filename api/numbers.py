"""Number and unit-scale normalization.

Pure functions, heavily tested. PRD 7.5 calls the numeric path "the
highest-reliability component in the entire verifier"; it is also what turns a
printed "7,286" under an "in millions" caption into the 7286000000 that
companyfacts reports (PRD 6.5.2 Trap 2). Getting the direction backwards
produces a 10^6 error that presents as catastrophic accuracy failure.

Lives at the package root rather than under verify/ because parsing needs it in
Phase 1 -- inline-XBRL scale application and table unit captions both -- and the
verifier does not exist until Phase 4.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# Multiplier for a scale word as printed in a table caption.
UNIT_SCALES: dict[str, int] = {
    "thousands": 10**3,
    "millions": 10**6,
    "billions": 10**9,
}

# Characters that decorate a printed figure without changing its value.
# The exotic spaces are deliberate: filings use non-breaking, thin and narrow
# no-break spaces as digit separators, and treating them as ordinary spaces is
# how "1 234" silently becomes unparseable.
_STRIP = str.maketrans("", "", "$   , ")  # noqa: RUF001

# Unicode minus, en dash and em dash all show up as negatives in filings.
# Deliberately not ASCII hyphens -- that is the whole point of the mapping.
_MINUSES = "−–—"  # noqa: RUF001

_NUMERIC = re.compile(r"^[+-]?\d*\.?\d+$")


class NumberFormatError(ValueError):
    """A string that was expected to be a printed figure could not be read."""


def parse_number(text: str) -> Decimal:
    """Parse a figure as printed in a filing.

    Handles `$7,286` / `7,286` / `7286` / `7.286` / `(7,286)` for negatives /
    unicode minus signs / non-breaking and thin spaces used as digit separators.

    Returns the value exactly as printed, with no scale applied -- scale is a
    separate concern and applying it here would hide which of the two happened.
    """
    if text is None:
        raise NumberFormatError("cannot parse None as a number")

    s = text.strip()
    if not s:
        raise NumberFormatError("cannot parse an empty string as a number")

    # Accounting convention: parentheses mean negative.
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    for dash in _MINUSES:
        s = s.replace(dash, "-")

    s = s.translate(_STRIP)

    # A bare dash is how filings print a zero or an omitted value in tables.
    if s in {"-", ""}:
        return Decimal(0)

    if not _NUMERIC.match(s):
        raise NumberFormatError(f"not a recognizable figure: {text!r}")

    try:
        value = Decimal(s)
    except InvalidOperation as exc:
        raise NumberFormatError(f"not a recognizable figure: {text!r}") from exc

    return -value if negative else value


def apply_scale(value: Decimal, scale: int) -> Decimal:
    """Apply an inline-XBRL `scale` attribute: the value is `value * 10**scale`."""
    return value * (Decimal(10) ** scale)


def to_base_units(value: Decimal, unit_scale: str | None) -> Decimal:
    """Convert a figure printed under a caption like "(in millions)" to base units.

    `xbrl_facts.value` stores base units and the document prints scaled ones, so
    both sides must be normalized before they can be compared at all.
    """
    if unit_scale is None:
        return value
    key = unit_scale.strip().lower()
    if key not in UNIT_SCALES:
        raise NumberFormatError(f"unknown unit scale: {unit_scale!r}")
    return value * UNIT_SCALES[key]


def detect_unit_scale(caption: str) -> str | None:
    """Find a scale word in a table caption. Returns None when absent."""
    lowered = caption.lower()
    for word in UNIT_SCALES:
        # "in thousands", "in millions, except per share data", "$ in millions"
        if re.search(rf"\bin\s+{word}\b", lowered) or re.search(rf"\b{word}\b", lowered):
            return word
    return None
