from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, cast


def normalize_positions_payload(payload: dict[str, Any]) -> list[dict[str, object]]:
    positions = payload.get("positions")
    records: list[dict[str, object]] = []
    for position in _position_items(positions):
        start_date = _coerce_month_year(
            position.get("startMonthYear") or position.get("startDate") or position.get("startedOn")
        )
        end_date = _coerce_month_year(position.get("endMonthYear") or position.get("endDate"))
        records.append(
            {
                "employer_name": _localized_text(position.get("companyName")),
                "job_title": _localized_text(position.get("title")),
                "start_date": start_date,
                "end_date": end_date,
                "is_current": end_date is None,
            }
        )
    return records


def normalize_current_position(payload: dict[str, Any]) -> list[dict[str, object]]:
    position = payload.get("primaryCurrentPosition")
    if not isinstance(position, dict):
        return []

    return [
        {
            "employer_name": _localized_text(position.get("companyName")),
            "job_title": _localized_text(position.get("title")),
            "start_date": _coerce_month_year(position.get("startedOn")),
            "end_date": None,
            "is_current": True,
        }
    ]


def filter_employment_history(
    records: Sequence[Mapping[str, object]],
    *,
    years: int,
    today: date | None = None,
) -> list[dict[str, object]]:
    if years <= 0:
        return []

    reference_day = today or date.today()
    cutoff = date(reference_day.year - years, reference_day.month, 1)
    filtered: list[dict[str, object]] = []

    for record in records:
        start = _parse_year_month(record.get("start_date"))
        end = _parse_year_month(record.get("end_date")) or reference_day.replace(day=1)
        if start is None:
            continue
        if end >= cutoff:
            filtered.append(dict(record))

    return filtered


def _position_items(positions: object) -> list[dict[str, Any]]:
    if isinstance(positions, list):
        return [cast(dict[str, Any], item) for item in positions if isinstance(item, dict)]
    if not isinstance(positions, dict):
        return []

    for key in ("elements", "values"):
        items = positions.get(key)
        if isinstance(items, list):
            return [cast(dict[str, Any], item) for item in items if isinstance(item, dict)]

    return []


def _localized_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None

    localized = value.get("localized")
    if isinstance(localized, dict):
        for item in localized.values():
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                raw_text = item.get("rawText")
                if isinstance(raw_text, str):
                    return raw_text

    return None


def _coerce_month_year(value: object) -> str | None:
    if not isinstance(value, dict):
        return None

    year = value.get("year")
    month = value.get("month")
    if not isinstance(year, int):
        return None
    if isinstance(month, int):
        return f"{year:04d}-{month:02d}"
    return f"{year:04d}-01"


def _parse_year_month(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        year_str, month_str = value.split("-", 1)
        return date(int(year_str), int(month_str), 1)
    except ValueError:
        return None
