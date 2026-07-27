from __future__ import annotations

import sqlite3
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from country_api.database import (
    data_quality_snapshot,
    get_country,
    get_population_history,
    health_snapshot,
    list_countries,
    list_ingestion_runs,
    summary_snapshot,
)
from country_api.errors import ApiError
from country_api.validation import (
    InputValidationError,
    normalize_country_code,
    normalize_country_codes,
    parse_limit,
    parse_year_range,
)


api = Blueprint("api", __name__)


def _database_path() -> str:
    return str(current_app.config["DATABASE_PATH"])


def _bad_request(exc: InputValidationError) -> ApiError:
    return ApiError(
        code="invalid_query_parameter",
        message=str(exc),
        status_code=400,
    )


@api.get("/")
def index():
    return jsonify(
        {
            "service": "flask-country-data-api",
            "description": "Deterministic country metadata and population API backed by SQLite.",
            "documentation": "/openapi/openapi.yaml",
            "endpoints": [
                "/health",
                "/api/v1/countries",
                "/api/v1/countries/<code>",
                "/api/v1/countries/<code>/population",
                "/api/v1/summary",
                "/api/v1/data-quality",
                "/api/v1/ingestion-runs",
            ],
        }
    )


@api.get("/health")
def health():
    try:
        snapshot = health_snapshot(_database_path())
    except sqlite3.Error as exc:
        raise ApiError(
            code="database_unavailable",
            message="The SQLite database is unavailable.",
            status_code=503,
        ) from exc
    return jsonify(snapshot)


@api.get("/api/v1/countries")
def countries():
    raw_codes = request.args.get("codes")
    try:
        codes = normalize_country_codes(raw_codes) if raw_codes else None
        limit = parse_limit(request.args.get("limit"))
    except InputValidationError as exc:
        raise _bad_request(exc) from exc

    data = list_countries(
        _database_path(),
        codes=codes,
        region=request.args.get("region"),
        income_level=request.args.get("income_level"),
        limit=limit,
    )
    return jsonify({"data": data, "meta": {"count": len(data), "limit": limit}})


@api.get("/api/v1/countries/<code>")
def country_detail(code: str):
    try:
        normalized_code = normalize_country_code(code)
    except InputValidationError as exc:
        raise _bad_request(exc) from exc

    data = get_country(_database_path(), normalized_code)
    if data is None:
        raise ApiError(
            code="country_not_found",
            message=f"No country was found for code {normalized_code}.",
            status_code=404,
            details={"countryCode": normalized_code},
        )
    return jsonify({"data": data})


@api.get("/api/v1/countries/<code>/population")
def population_history(code: str):
    try:
        normalized_code = normalize_country_code(code)
        current_year = datetime.now().year
        from_year, to_year = parse_year_range(
            request.args.get("from"),
            request.args.get("to"),
            default_from=1960,
            default_to=current_year,
        )
    except InputValidationError as exc:
        raise _bad_request(exc) from exc

    if get_country(_database_path(), normalized_code) is None:
        raise ApiError(
            code="country_not_found",
            message=f"No country was found for code {normalized_code}.",
            status_code=404,
            details={"countryCode": normalized_code},
        )

    data = get_population_history(
        _database_path(),
        code=normalized_code,
        from_year=from_year,
        to_year=to_year,
    )
    return jsonify(
        {
            "data": data,
            "meta": {
                "countryCode": normalized_code,
                "fromYear": from_year,
                "toYear": to_year,
                "count": len(data),
            },
        }
    )


@api.get("/api/v1/summary")
def summary():
    return jsonify({"data": summary_snapshot(_database_path())})


@api.get("/api/v1/data-quality")
def data_quality():
    return jsonify({"data": data_quality_snapshot(_database_path())})


@api.get("/api/v1/ingestion-runs")
def ingestion_runs():
    try:
        limit = parse_limit(request.args.get("limit"), default=20, maximum=100)
    except InputValidationError as exc:
        raise _bad_request(exc) from exc

    data = list_ingestion_runs(_database_path(), limit=limit)
    return jsonify({"data": data, "meta": {"count": len(data), "limit": limit}})
