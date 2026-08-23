"""SM-2 spaced-repetition algorithm (PRD Appendix A).

Pure functions — fully unit-testable without a database.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Sm2State:
    repetition: int = 0
    interval_days: int = 1
    ease_factor: float = 2.5
    mastery: int = 0


def update_sm2(state: Sm2State, quality: int) -> Sm2State:
    """Apply one review with quality q (0-5) and return the new state.

    Matches PRD §5.5 / Appendix A exactly:
      - q >= 3: advance repetition; interval = 1 / 6 / round(interval*EF)
      - q <  3: reset repetition=0, interval=1
      - ease_factor = max(1.3, EF + 0.1 - (5-q)*(0.08 + (5-q)*0.02))
      - mastery += 10 if correct else -15 (clamped 0..100)
    """
    q = max(0, min(5, int(quality)))

    if q >= 3:
        if state.repetition == 0:
            interval = 1
        elif state.repetition == 1:
            interval = 6
        else:
            interval = round(state.interval_days * state.ease_factor)
        repetition = state.repetition + 1
    else:
        repetition = 0
        interval = 1

    ease_factor = max(
        1.3,
        state.ease_factor + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02),
    )

    delta = 10 if q >= 3 else -15
    mastery = max(0, min(100, state.mastery + delta))

    return Sm2State(
        repetition=repetition,
        interval_days=interval,
        ease_factor=round(ease_factor, 4),
        mastery=mastery,
    )


def initial_sm2() -> Sm2State:
    return Sm2State(repetition=0, interval_days=1, ease_factor=2.5, mastery=0)
