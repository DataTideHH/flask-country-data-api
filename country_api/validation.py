from __future__ import annotations

from jsonschema import ValidationError, validate

from country_api.country_schema import COUNTRY_RESPONSE_SCHEMA


def normalize_country_codes(raw_country_param: str) -> list[str]:
    if not raw_country_param.strip():
        raise ValueError("Missing required query parameter: country")

    country_codes = [
        part.strip().upper()
        for part in raw_country_param.split(",")
        if part.strip()
    ]

    if not country_codes:
        raise ValueError("No valid country codes provided.")

    invalid_codes = [
        code for code in country_codes
        if len(code) != 2 or not code.isalpha()
    ]

    if invalid_codes:
        raise ValueError(
            "Invalid country code(s): "
            + ", ".join(invalid_codes)
            + ". Use two-letter codes such as DE or US."
        )

    return country_codes


def validate_country_response(data: dict) -> None:
    try:
        validate(instance=data, schema=COUNTRY_RESPONSE_SCHEMA)
    except ValidationError as exc:
        raise ValueError(
            f"Generated response does not match expected JSON schema: {exc.message}"
        ) from exc
