# Data Quality Notes

This project uses Claude/Anthropic as a generative API to produce structured country data.

That is useful for learning Flask routing, query parameters, JSON responses, external API calls, schema validation and API-key handling.

It is not the same as using a verified country-data source.

## Structure vs. correctness

The JSON schema can check whether a response has the expected structure.

It cannot prove that generated facts are correct.

A generated population number can be outdated or inaccurate even if it is a valid integer.

## Learning value

The intended learning workflow is:

```text
Browser -> Flask endpoint -> query parameter -> Python list -> external generative API -> structured JSON -> JSON response
```
