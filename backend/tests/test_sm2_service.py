"""Unit tests for the SM-2 spaced-repetition algorithm (PRD Appendix A)."""
from app.services.sm2_service import Sm2State, initial_sm2, update_sm2


def test_initial_state():
    s = initial_sm2()
    assert (s.repetition, s.interval_days, s.ease_factor, s.mastery) == (
        0,
        1,
        2.5,
        0,
    )


def test_correct_first_review():
    s = update_sm2(initial_sm2(), quality=5)
    assert s.repetition == 1
    assert s.interval_days == 1  # first correct -> 1 day
    assert s.ease_factor > 2.5
    assert s.mastery == 10


def test_wrong_review_resets():
    s = update_sm2(initial_sm2(), quality=1)
    assert s.repetition == 0
    assert s.interval_days == 1
    assert s.ease_factor < 2.5
    assert s.mastery == 0


def test_second_review_interval():
    s = Sm2State(repetition=1, interval_days=1, ease_factor=2.5, mastery=10)
    n = update_sm2(s, quality=4)
    assert n.repetition == 2
    assert n.interval_days == 6  # second correct -> 6 days


def test_classic_interval_rule():
    # 3rd+ review: interval = round(interval * ease_factor)
    s = Sm2State(repetition=2, interval_days=6, ease_factor=2.6, mastery=50)
    n = update_sm2(s, quality=5)
    assert n.interval_days == round(6 * 2.6)


def test_ease_factor_floor():
    s = Sm2State(repetition=0, interval_days=1, ease_factor=1.3, mastery=0)
    n = update_sm2(s, quality=0)
    assert n.ease_factor >= 1.3


def test_mastery_clamp():
    high = Sm2State(repetition=0, interval_days=1, ease_factor=2.5, mastery=95)
    assert update_sm2(high, quality=5).mastery <= 100
    low = Sm2State(repetition=0, interval_days=1, ease_factor=2.5, mastery=5)
    assert update_sm2(low, quality=0).mastery >= 0


def test_quality_bounds():
    # out-of-range quality is clamped to 0..5
    assert update_sm2(initial_sm2(), quality=99).ease_factor > 2.5  # clamped to 5 -> correct
    assert update_sm2(initial_sm2(), quality=-5).repetition == 0
