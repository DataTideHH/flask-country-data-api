from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx


class WorldBankClientError(RuntimeError):
    pass


class WorldBankClient:
    source_name = "World Bank API"

    def __init__(
        self,
        *,
        base_url: str = "https://api.worldbank.org/v2",
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get_items(self, path: str, params: dict[str, object]) -> list[dict[str, Any]]:
        try:
            response = httpx.get(
                f"{self.base_url}/{path.lstrip('/')}",
                params={**params, "format": "json", "per_page": 20000},
                timeout=self.timeout_seconds,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise WorldBankClientError("World Bank request timed out.") from exc
        except httpx.HTTPError as exc:
            raise WorldBankClientError("World Bank request failed.") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise WorldBankClientError("World Bank response was not valid JSON.") from exc

        if not isinstance(payload, list) or len(payload) < 2:
            raise WorldBankClientError("World Bank response has an unexpected structure.")

        items = payload[1]
        if items is None:
            return []
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            raise WorldBankClientError("World Bank response items have an unexpected structure.")
        return items

    def fetch_country(self, code: str) -> dict[str, Any]:
        items = self._get_items(f"country/{code}", {})
        if not items:
            raise WorldBankClientError(f"World Bank returned no country for code {code}.")
        return items[0]

    def fetch_population(self, code: str, from_year: int, to_year: int) -> list[dict[str, Any]]:
        return self._get_items(
            f"country/{code}/indicator/SP.POP.TOTL",
            {"date": f"{from_year}:{to_year}"},
        )


class FixtureWorldBankClient:
    source_name = "World Bank fixture snapshot"

    def __init__(self, fixture_directory: str | Path) -> None:
        directory = Path(fixture_directory)
        self._countries = self._load_object(directory / "world-bank-countries.json", "countries")
        self._observations = self._load_object(
            directory / "world-bank-population.json", "observations"
        )

    @staticmethod
    def _load_object(path: Path, key: str) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise WorldBankClientError(f"Fixture file could not be read: {path}") from exc
        except json.JSONDecodeError as exc:
            raise WorldBankClientError(f"Fixture file is not valid JSON: {path}") from exc

        value = payload.get(key) if isinstance(payload, dict) else None
        if not isinstance(value, dict):
            raise WorldBankClientError(f"Fixture file {path} must contain object key {key!r}.")
        return value

    def fetch_country(self, code: str) -> dict[str, Any]:
        value = self._countries.get(code)
        if not isinstance(value, dict):
            raise WorldBankClientError(f"Fixture contains no country for code {code}.")
        return value

    def fetch_population(self, code: str, from_year: int, to_year: int) -> list[dict[str, Any]]:
        value = self._observations.get(code)
        if not isinstance(value, list):
            raise WorldBankClientError(f"Fixture contains no observations for code {code}.")
        return [
            item
            for item in value
            if isinstance(item, dict)
            and from_year <= int(item.get("date", -1)) <= to_year
        ]
