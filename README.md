# Flask AI Country API

**Flask · Query parameters · JSON responses · Anthropic/Claude API · structured output · data quality notes**

This repository documents a small Flask learning project.

The project exposes a simple HTTP endpoint that reads country codes from a query parameter, calls a generative AI API and returns structured JSON.

Example request:

```text
http://localhost:8080/countries?country=DE,US
```

The project is part of my broader **DataTideHH portfolio** and supports my learning path toward **Data/BI Analyst** roles with a focus on Python, APIs, JSON workflows, data quality awareness and responsible use of AI-assisted tools.

---

## Why This Project Matters for Data/BI

Many Data/BI workflows depend on external systems such as databases, REST APIs, data warehouses, SaaS platforms, cloud services or generative APIs.

This project demonstrates a small version of that pattern:

1. receive an HTTP request
2. read query parameters
3. transform request input into a Python data structure
4. call an external API
5. request structured JSON
6. validate the response shape
7. return JSON to the browser

The focus is not on authoritative country statistics. The focus is on API flow, JSON structure and the difference between structured data and verified data quality.

---

## Current Scope

The current endpoint is:

```text
GET /countries?country=DE,US
```

It should return a JSON response with generated country objects.

Expected object structure:

```json
{
  "countryCode": "DE",
  "countryName": "Germany",
  "languages": ["German"],
  "population": 83000000,
  "description": "Short generated description."
}
```

---

## Important Data Quality Note

Claude/Anthropic is used here as a generative API, not as an authoritative country database.

A JSON schema can help enforce the structure of a response, but it does not automatically guarantee that generated facts such as population numbers are accurate, complete or current.

For production-quality country data, a verified source would be more appropriate, for example an official statistics source, an internal database, a curated dataset or a dedicated public country-data API.

---

## Setup

```bash
/usr/local/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Never commit `.env`.

---

## How to Run

Run the Flask app locally:

```bash
python main.py
```

Then open:

```text
http://localhost:8080/countries?country=DE,US
```

By default, `.env.example` uses `USE_MOCK_RESPONSE=1` for local mock testing without an external API call.

## Project Structure

```text
flask-ai-country-api/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py
├── country_api/
│   ├── __init__.py
│   ├── anthropic_client.py
│   ├── country_schema.py
│   └── validation.py
├── docs/
│   └── data-quality-notes.md
└── examples/
    └── sample-response.json
```

---

## Notes and Limitations

This is a learning project.

It is not a production country-data API and should not be used as an authoritative source for country information.

The main value of this project is the Flask/API/JSON workflow, not the generated country facts.
