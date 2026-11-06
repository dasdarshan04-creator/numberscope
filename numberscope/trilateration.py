"""Synthetic trilateration demo.

This module is a teaching aid for the *geometry* of trilateration. Everything
here lives on an arbitrary 2-D plane measured in made-up "demo kilometres".

It has NO connection to mobile networks, real cell towers, radio signals, GPS,
maps, or phone numbers, and it cannot locate or track any real person. The
tower coordinates and the ranges are all invented, user-adjustable sample
values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Fictional towers: (label, x, y) on the demo plane.
DEMO_TOWERS: tuple[tuple[str, float, float], ...] = (
    ("Tower A", 0.0, 0.0),
    ("Tower B", 8.0, 0.0),
    ("Tower C", 2.0, 7.0),
)


@dataclass(frozen=True)
class TrilaterationResult:
    """Outcome of a synthetic trilateration estimate."""

    x: float
    y: float
    residuals: tuple[float, float, float]  # entered range − range from estimate
    rms_error: float  # root-mean-square of the residuals (demo km)

    @property
    def is_consistent(self) -> bool:
        """True when the three ranges agree closely (small RMS error)."""
        return self.rms_error < 1e-6


def estimate_demo_position(
    ranges: tuple[float, float, float],
) -> tuple[float, float]:
    """Estimate a point on the demo plane from three sample ranges.

    Kept as a thin ``(x, y)`` helper for backward compatibility. For residuals
    and error, use :func:`solve`.
    """
    result = solve(ranges)
    return result.x, result.y


def solve(ranges: tuple[float, float, float]) -> TrilaterationResult:
    """Solve the synthetic trilateration problem and report fit quality.

    Args:
        ranges: Three positive, finite sample ranges, one per demo tower.

    Raises:
        ValueError: If a range is non-positive/non-finite, or the tower
            geometry is degenerate.
    """
    if any(not math.isfinite(distance) or distance <= 0 for distance in ranges):
        raise ValueError("Sample ranges must be positive, finite numbers.")

    (x1, y1), (x2, y2), (x3, y3) = ((t[1], t[2]) for t in DEMO_TOWERS)
    r1, r2, r3 = ranges

    a = 2 * (x2 - x1)
    b = 2 * (y2 - y1)
    c = r1**2 - r2**2 + x2**2 + y2**2 - x1**2 - y1**2
    d = 2 * (x3 - x1)
    e = 2 * (y3 - y1)
    f = r1**2 - r3**2 + x3**2 + y3**2 - x1**2 - y1**2
    determinant = a * e - b * d
    if math.isclose(determinant, 0.0):
        raise ValueError("The demo tower geometry cannot determine a position.")

    x = (c * e - b * f) / determinant
    y = (a * f - c * d) / determinant

    residuals = tuple(
        entered - math.hypot(x - tower[1], y - tower[2])
        for entered, tower in zip(ranges, DEMO_TOWERS, strict=True)
    )
    rms = math.sqrt(sum(r * r for r in residuals) / len(residuals))

    return TrilaterationResult(x=x, y=y, residuals=residuals, rms_error=rms)
