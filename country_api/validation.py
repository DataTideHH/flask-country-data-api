from __future__ import annotations

import re
from datetime import datetime
from typing import Any


ISO2_PATTERN = re.compile(r"^[A-Z]{2}$")
MAX_COUNTRY_CODES = 10
MIN_YEAR = 1960
MAX_YEAR = datetime.now().year + 1


class InputValidationError(ValueError):
    pass


class SourceValidationError(ValueError):
    pass


def normalize_country_code(value: str) -> str:
    code = value.strip().upper()
    if not ISO2_PATTERN.fullmatch(code):
        raise InputValidationError(
            f"Invalid country code: {value!r}. Use a two-letter code such as DE or US."
        )
    return code


def normalize_country_codes(raw_value: str | None, *, max_codes: int = MAX_COUNTRY_CODES) -> list[str]:
    if raw_value is None or not raw_value.strip():
        raise InputValidationError("Missing required country code list.")

    normalized: list[str] = []
    seen: set[str] = set()

    for part in raw_value.split(","):
        if not part.strip():
            continue
        code = normalize_country_code(part)
        if code not in seen:
            normalized.append(code)
            seen.add(code)

    if not normalized:
        raise InputValidationError("No valid country codes were provided.")
    if len(normalized) > max_codes:
        raise InputValidationError(
            f"A maximum of {max_codes} country codes is allowed per request."
        )
    return normalized


def parse_limit(raw_value: str | None, *, default: int = 50, maximum: int = 100) -> int:
    if raw_value is None or raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise InputValidationError("limit must be an integer.") from exc
    if value < 1 or value > maximum:
        raise InputValidationError(f"limit must be between 1 and {maximum}.")
    return value


def parse_year_range(
    raw_from_year: str | int | None,
    raw_to_year: str | int | None,
    *,
    default_from: int,
    default_to: int,
) -> tuple[int, int]:
    try:
        from_year = default_from if raw_from_year in (None, "") else int(raw_from_year)
        to_year = default_to if raw_to_year in (None, "") else int(raw_to_year)
    except (TypeError, ValueError) as exc:
        raise InputValidationError("from and to must be valid years.") from exc

    if from_year < MIN_YEAR or to_year > MAX_YEAR:
        raise InputValidationError(
            f"Years must be between {MIN_YEAR} and {MAX_YEAR}."
        )
    if from_year > to_year:
        raise InputValidationError("from must be less than or equal to to.")
    return from_year, to_year


def _required_text(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SourceValidationError(f"Source field {key!r} must contain text.")
    return value.strip()


def _nested_text(raw: dict[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise SourceValidationError(f"Source field {key!r} must be an object.")
    nested = value.get("value")
    if nested in (None, ""):
        return None
    if not isinstance(nested, str):
        raise SourceValidationError(f"Source field {key!r}.value must contain text.")
    return nested.strip()


def _optional_float(raw: dict[str, Any], key: str, minimum: float, maximum: float) -> float | None:
    value = raw.get(key)
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SourceValidationError(f"Source field {key!r} must be numeric.") from exc
    if number < minimum or number > maximum:
        raise SourceValidationError(
            f"Source field {key!r} must be between {minimum} and {maximum}."
        )
    return number


def normalize_country_record(
    raw: dict[str, Any],
    *,
    expected_code: str,
    source_name: str,
    fetched_at: str,
) -> dict[str, Any]:
    source_code = normalize_country_code(_required_text(raw, "iso2Code"))
    if source_code != expected_code:
        raise SourceValidationError(
            f"Source returned country code {source_code} while {expected_code} was requested."
        )

    region = _nested_text(raw, "region")
    if region in (None, "Aggregates"):
        raise SourceValidationError(
            f"Country code {expected_code} resolved to an aggregate instead of a country."
        )

    capital_city = raw.get("capitalCity")
    if capital_city not in (None, "") and not isinstance(capital_city, str):
        raise SourceValidationError("Source field 'capitalCity' must contain text or be empty.")

    return {
        "iso2_code": source_code,
        "country_name": _required_text(raw, "name"),
        "region_name": region,
        "income_level": _nested_text(raw, "incomeLevel"),
        "capital_city": capital_city.strip() if isinstance(capital_city, str) and capital_city.strip() else None,
        "longitude": _optional_float(raw, "longitude", -180.0, 180.0),
        "latitude": _optional_float(raw, "latitude", -90.0, 90.0),
        "source_name": source_name,
        "fetched_at": fetched_at,
    }


def normalize_population_record(
    raw: dict[str, Any],
    *,
    expected_code: str,
    source_name: str,
    fetched_at: str,
) -> dict[str, Any]:
    country = raw.get("country")
    if not isinstance(country, dict):
        raise SourceValidationError("Population record must include a country object.")

    source_code = normalize_country_code(_required_text(country, "id"))
    if source_code != expected_code:
        raise SourceValidationError(
            f"Population record returned {source_code} while {expected_code} was requested."
        )

    indicator = raw.get("indicator")
    if not isinstance(indicator, dict) or indicator.get("id") != "SP.POP.TOTL":
        raise SourceValidationError("Unexpected or missing population indicator code.")

    try:
        observation_year = int(raw.get("date"))
    except (TypeError, ValueError) as exc:
        raise SourceValidationError("Population record contains an invalid year.") from exc

    if observation_year < MIN_YEAR or observation_year > MAX_YEAR:
        raise SourceValidationError("Population record contains an implausible year.")

    value = raw.get("value")
    if value is not None:
        if isinstance(value, bool):
            raise SourceValidationError("Population value must be an integer or null.")
        try:
            value = int(value)
        except (TypeError, ValueError) as exc:
            raise SourceValidationError("Population value must be an integer or null.") from exc
        if value < 0:
            raise SourceValidationError("Population value cannot be negative.")

    return {
        "iso2_code": source_code,
        "observation_year": observation_year,
        "population": value,
        "indicator_code": "SP.POP.TOTL",
        "source_name": source_name,
        "fetched_at": fetched_at,
    }
