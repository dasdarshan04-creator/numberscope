"""Core phone-number analysis.

Everything here runs locally against the offline metadata bundled with the
``phonenumbers`` package (the Python port of Google's libphonenumber). No
network request is made, and nothing is written to disk.

The output is deliberately limited to *numbering-plan metadata*: how a number
is structured, whether it is a plausible/assigned-range number, and the coarse,
public descriptors (original range assignee, broad geographic range, candidate
time zones). It cannot identify a subscriber or a device location — see
:data:`FIELD_NOTES` for the caveats attached to each field.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from datetime import timezone as _tz
from typing import Any

import phonenumbers
from phonenumbers import carrier, geocoder
from phonenumbers import timezone as pn_timezone
from phonenumbers.phonenumberutil import ValidationResult

NOT_AVAILABLE = "Not available in local metadata"

TYPE_LABELS: dict[Any, str] = {
    phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed line",
    phonenumbers.PhoneNumberType.MOBILE: "Mobile",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed line or mobile",
    phonenumbers.PhoneNumberType.TOLL_FREE: "Toll-free",
    phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium rate",
    phonenumbers.PhoneNumberType.SHARED_COST: "Shared cost",
    phonenumbers.PhoneNumberType.VOIP: "VoIP",
    phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal number",
    phonenumbers.PhoneNumberType.PAGER: "Pager",
    phonenumbers.PhoneNumberType.UAN: "Universal access number",
    phonenumbers.PhoneNumberType.VOICEMAIL: "Voicemail",
    phonenumbers.PhoneNumberType.UNKNOWN: "Unknown",
}

POSSIBLE_REASON_LABELS: dict[Any, str] = {
    ValidationResult.IS_POSSIBLE: "Length is possible",
    ValidationResult.IS_POSSIBLE_LOCAL_ONLY: "Possible only when dialled locally",
    ValidationResult.TOO_SHORT: "Too short",
    ValidationResult.TOO_LONG: "Too long",
    ValidationResult.INVALID_LENGTH: "Invalid length for this numbering plan",
    ValidationResult.INVALID_COUNTRY_CODE: "Invalid country calling code",
}

# Short, plain-language caveats shown next to each field in the UI and reports.
FIELD_NOTES: dict[str, str] = {
    "carrier_metadata": (
        "Identifies the operator a number RANGE was originally assigned to. "
        "Number portability means the current operator may differ."
    ),
    "range_description": (
        "A broad geographic range tied to the numbering block — not the "
        "phone's present location."
    ),
    "time_zones": (
        "Candidate time zones for the numbering range, not the device's "
        "actual location or current time."
    ),
    "valid_range": (
        "The number falls inside an assigned range. It does NOT prove the "
        "number is currently allocated, active, reachable, or owned by anyone."
    ),
}


@dataclass(frozen=True)
class NumberReport:
    """A structured, serialisable result for a single phone number."""

    input: str
    international: str
    national: str
    e164: str
    rfc3966: str
    country_calling_code: str
    region_code: str
    possible: bool
    possible_reason: str
    valid_range: bool
    number_type: str
    carrier_metadata: str
    range_description: str
    time_zones: list[str]
    analysed_at_utc: str
    metadata_version: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_flat_row(self) -> dict[str, Any]:
        """Flatten for CSV: join list fields into a single string."""
        row = self.as_dict()
        row["time_zones"] = "; ".join(self.time_zones)
        return row


def metadata_version() -> str:
    """Return the installed phonenumbers/libphonenumber metadata version."""
    return getattr(phonenumbers, "__version__", "unknown")


def analyse_number(raw_number: str, default_region: str = "IN") -> NumberReport:
    """Parse ``raw_number`` and return its local numbering-plan metadata.

    Args:
        raw_number: The number to analyse. If it starts with ``+`` it carries
            its own country code; otherwise ``default_region`` is assumed.
        default_region: ISO region code used only for non-``+`` input.

    Raises:
        ValueError: If the input is empty or cannot be parsed.
    """
    raw_number = (raw_number or "").strip()
    if not raw_number:
        raise ValueError("Enter a phone number first.")

    region = None if raw_number.startswith("+") else default_region

    try:
        parsed = phonenumbers.parse(raw_number, region)
    except phonenumbers.NumberParseException as exc:
        raise ValueError(f"Could not parse this number: {exc}") from exc

    possible_reason = phonenumbers.is_possible_number_with_reason(parsed)
    number_type = phonenumbers.number_type(parsed)
    time_zones = list(pn_timezone.time_zones_for_number(parsed))

    return NumberReport(
        input=raw_number,
        international=phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        ),
        national=phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.NATIONAL
        ),
        e164=phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        rfc3966=phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.RFC3966
        ),
        country_calling_code=f"+{parsed.country_code}",
        region_code=phonenumbers.region_code_for_number(parsed) or "Unknown",
        possible=phonenumbers.is_possible_number(parsed),
        possible_reason=POSSIBLE_REASON_LABELS.get(possible_reason, "Not specified"),
        valid_range=phonenumbers.is_valid_number(parsed),
        number_type=TYPE_LABELS.get(number_type, "Unknown"),
        carrier_metadata=carrier.name_for_number(parsed, "en") or NOT_AVAILABLE,
        range_description=geocoder.description_for_number(parsed, "en") or NOT_AVAILABLE,
        time_zones=time_zones or [NOT_AVAILABLE],
        analysed_at_utc=datetime.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        metadata_version=metadata_version(),
    )
