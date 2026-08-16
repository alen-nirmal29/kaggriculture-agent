"""Turn-aware V2 investment and liquidation helpers."""

from agent_v2.economics import LAST_DAY, production_schedule


def is_final_day(day: int) -> bool:
    return day >= LAST_DAY


def crop_can_return(crop: str, current_step: int) -> bool:
    return bool(production_schedule(crop, current_step))


def should_liquidate_carried(day: int, hour: int) -> bool:
    return is_final_day(day) or (day == LAST_DAY - 1 and hour >= 20)
