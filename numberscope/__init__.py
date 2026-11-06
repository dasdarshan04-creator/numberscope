"""NumberScope — a local, privacy-respecting mobile-number OSINT lab.

The package exposes two independent building blocks:

* :mod:`numberscope.analysis` — parse a phone number and report the *public*
  numbering-plan metadata that libphonenumber ships offline. It never contacts
  a carrier, a device, a GPS service, or a lookup API.
* :mod:`numberscope.trilateration` — a self-contained, synthetic trilateration
  demo on an arbitrary 2-D plane. It has no connection to real towers, radio
  signals, maps, or phone numbers; it exists only to teach the geometry.
"""

from __future__ import annotations

from .analysis import NumberReport, analyse_number, metadata_version
from .trilateration import DEMO_TOWERS, estimate_demo_position

__all__ = [
    "NumberReport",
    "analyse_number",
    "metadata_version",
    "DEMO_TOWERS",
    "estimate_demo_position",
    "__version__",
]

__version__ = "1.0.0"
