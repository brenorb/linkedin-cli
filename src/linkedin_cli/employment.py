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


def normalize_voyager_profile_payload(payload: dict[str, Any]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for position in _voyager_position_items(payload):
        start_date = _coerce_month_year(
            position.get("startMonthYear")
            or position.get("startDate")
            or position.get("startedOn")
            or _mapping_value(position.get("timePeriod"), "startDate")
        )
        end_date = _coerce_month_year(
            position.get("endMonthYear")
            or position.get("endDate")
            or _mapping_value(position.get("timePeriod"), "endDate")
        )
        records.append(
            {
                "employer_name": (
                    _localized_text(position.get("companyName"))
                    or _localized_text(_mapping_value(position.get("company"), "name"))
                    or _localized_text(_mapping_value(position.get("miniCompany"), "name"))
                ),
                "job_title": _localized_text(position.get("title")) or _localized_text(position.get("occupation")),
                "start_date": start_date,
                "end_date": end_date,
                "is_current": end_date is None,
            }
        )
    return records


def normalize_browser_experience_entries(entries: Sequence[object]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for entry in entries:
        description: str | None = None
        if isinstance(entry, Mapping):
            raw_lines = entry.get("lines")
            if not isinstance(raw_lines, list):
                continue
            lines = [line.strip() for line in raw_lines if isinstance(line, str) and line.strip()]
            raw_description = entry.get("description")
            if isinstance(raw_description, str) and raw_description.strip():
                description = raw_description.strip()
        elif isinstance(entry, list):
            lines = [line.strip() for line in entry if isinstance(line, str) and line.strip()]
        else:
            continue
        if len(lines) < 3:
            continue
        date_index = next((index for index, line in enumerate(lines) if _looks_like_date_range(line)), None)
        if date_index is None or date_index < 2:
            continue

        title = lines[date_index - 2]
        employer_line = lines[date_index - 1]
        start_date, end_date = _parse_browser_date_range(lines[date_index])
        if start_date is None:
            continue

        records.append(
            {
                "employer_name": employer_line.split(" · ", 1)[0].strip() or None,
                "job_title": title,
                "start_date": start_date,
                "end_date": end_date,
                "is_current": end_date is None,
                "description": description,
            }
        )
    return records


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


def _voyager_position_items(payload: Mapping[str, object]) -> list[dict[str, Any]]:
    direct_keys = ("positionView", "positions", "positionGroupView", "profilePositionView")
    for key in direct_keys:
        items = _position_items(payload.get(key))
        if items:
            return items

    items: list[dict[str, Any]] = []
    _collect_voyager_position_items(payload, items)
    return items


def _collect_voyager_position_items(value: object, items: list[dict[str, Any]]) -> None:
    if isinstance(value, list):
        for item in value:
            _collect_voyager_position_items(item, items)
        return
    if not isinstance(value, dict):
        return

    if _looks_like_position(value):
        items.append(cast(dict[str, Any], value))

    for nested in value.values():
        _collect_voyager_position_items(nested, items)


def _looks_like_position(value: Mapping[str, object]) -> bool:
    company_name = value.get("companyName")
    company = value.get("company")
    title = value.get("title")
    occupation = value.get("occupation")
    start = value.get("startDate") or value.get("startMonthYear") or _mapping_value(value.get("timePeriod"), "startDate")

    has_company = company_name is not None or _mapping_value(company, "name") is not None
    has_title = title is not None or occupation is not None
    return has_company and has_title and start is not None


def _localized_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None

    for key in ("text", "name", "rawText"):
        direct = value.get(key)
        if isinstance(direct, str):
            return direct

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


def _mapping_value(value: object, key: str) -> object | None:
    if not isinstance(value, Mapping):
        return None
    return value.get(key)


def _looks_like_date_range(value: str) -> bool:
    return _parse_browser_date_range(value)[0] is not None


def _parse_browser_date_range(value: str) -> tuple[str | None, str | None]:
    date_range = value.split("·", 1)[0].strip()
    if " - " not in date_range:
        return None, None
    start_text, end_text = (part.strip() for part in date_range.split(" - ", 1))
    start = _parse_browser_month_year(start_text)
    if start is None:
        return None, None
    if end_text.lower() == "present":
        return start, None
    return start, _parse_browser_month_year(end_text)


def _parse_browser_month_year(value: str) -> str | None:
    parts = value.split()
    if len(parts) != 2:
        return None
    month = _month_number(parts[0])
    try:
        year = int(parts[1])
    except ValueError:
        return None
    if month is None:
        return None
    return f"{year:04d}-{month:02d}"


def _month_number(value: str) -> int | None:
    month_map = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    return month_map.get(value.strip().lower())


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
