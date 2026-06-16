from __future__ import annotations

import json
import os

from anthropic import Anthropic


def get_country_data(country_codes: list[str], use_mock: bool = False) -> dict:
    if use_mock:
        return _mock_country_data(country_codes)

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key or api_key == "your_api_key_here":
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured. "
            "Set it in .env or run with USE_MOCK_RESPONSE=1 for local testing."
        )

    model = os.getenv("ANTHROPIC_MODEL", "replace_with_current_model_id_from_anthropic_docs")

    if model == "replace_with_current_model_id_from_anthropic_docs":
        raise RuntimeError(
            "ANTHROPIC_MODEL is not configured. "
            "Set a current Anthropic model ID in .env or use USE_MOCK_RESPONSE=1."
        )

    client = Anthropic(api_key=api_key)
    prompt = _build_prompt(country_codes)

    message = client.messages.create(
        model=model,
        max_tokens=1200,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    text_blocks = [
        block.text
        for block in message.content
        if getattr(block, "type", None) == "text"
    ]

    if not text_blocks:
        raise ValueError("Anthropic response did not contain a text block.")

    raw_text = "\n".join(text_blocks).strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Anthropic response was not valid JSON. "
            "This learning project expects the model to return JSON only."
        ) from exc


def _build_prompt(country_codes: list[str]) -> str:
    codes = ", ".join(country_codes)

    return f"""
You are generating structured JSON for a Flask learning project.

Return JSON only. Do not include Markdown, explanations, comments or code fences.

Create one country object for each of these two-letter country codes:

{codes}

Return exactly this JSON object structure:

{{
  "source": "anthropic",
  "countries": [
    {{
      "countryCode": "DE",
      "countryName": "Germany",
      "languages": ["German"],
      "population": 83000000,
      "description": "One short neutral description."
    }}
  ]
}}

Rules:
- Use the requested country codes.
- countryCode must be uppercase and two letters.
- languages must be an array of strings.
- population must be an integer.
- description must be one short neutral sentence.
- Return JSON only.
""".strip()


def _mock_country_data(country_codes: list[str]) -> dict:
    countries = []

    for code in country_codes:
        countries.append(
            {
                "countryCode": code,
                "countryName": f"Mock country for {code}",
                "languages": ["Example language"],
                "population": 0,
                "description": "Mock response for local testing without an external API call.",
            }
        )

    return {
        "source": "mock",
        "countries": countries,
    }
