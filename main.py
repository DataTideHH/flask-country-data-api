from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from country_api.anthropic_client import get_country_data
from country_api.validation import normalize_country_codes, validate_country_response


load_dotenv()

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        {
            "project": "flask-ai-country-api",
            "endpoints": ["/countries?country=DE,US"],
            "note": "Learning project for Flask, query parameters, JSON and generative API calls.",
        }
    )


@app.get("/countries")
def countries():
    raw_country_param = request.args.get("country", "")

    try:
        country_codes = normalize_country_codes(raw_country_param)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    use_mock = os.getenv("USE_MOCK_RESPONSE", "1") == "1"

    try:
        result = get_country_data(country_codes=country_codes, use_mock=use_mock)
        validate_country_response(result)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
