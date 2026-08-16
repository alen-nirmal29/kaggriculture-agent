"""Basic V1 end-of-season decisions."""

from agent.crops import CROPS

SEASON_DAYS = 30


def days_remaining(day: int) -> int:
    return max(0, SEASON_DAYS - day)


def should_invest(day: int, crop: str) -> bool:
    return days_remaining(day) > CROPS[crop].first_yield_day


def is_final_day(day: int) -> bool:
    return day >= SEASON_DAYS - 1
