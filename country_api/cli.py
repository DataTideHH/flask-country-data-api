from __future__ import annotations

import json
from pathlib import Path

import click
from flask import Flask, current_app

from country_api.service import refresh_country_data
from country_api.validation import InputValidationError, normalize_country_codes, parse_year_range
from country_api.world_bank import FixtureWorldBankClient, WorldBankClient


def register_cli_commands(app: Flask) -> None:
    @app.cli.command("refresh-data")
    @click.option("--codes", default="DE,US,JP", show_default=True)
    @click.option("--from-year", default=2020, show_default=True, type=int)
    @click.option("--to-year", default=2024, show_default=True, type=int)
    @click.option(
        "--fixture-dir",
        type=click.Path(path_type=Path, file_okay=False, exists=True),
        default=None,
        help="Load deterministic versioned fixtures instead of the live World Bank API.",
    )
    def refresh_data_command(
        codes: str,
        from_year: int,
        to_year: int,
        fixture_dir: Path | None,
    ) -> None:
        """Refresh country metadata and population observations."""
        try:
            country_codes = normalize_country_codes(codes)
            from_year, to_year = parse_year_range(
                from_year,
                to_year,
                default_from=from_year,
                default_to=to_year,
            )
        except InputValidationError as exc:
            raise click.ClickException(str(exc)) from exc

        client = (
            FixtureWorldBankClient(fixture_dir)
            if fixture_dir is not None
            else WorldBankClient()
        )

        try:
            result = refresh_country_data(
                current_app.config["DATABASE_PATH"],
                client=client,
                country_codes=country_codes,
                from_year=from_year,
                to_year=to_year,
            )
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

        click.echo(json.dumps(result, indent=2, sort_keys=True))
