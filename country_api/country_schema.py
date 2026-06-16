COUNTRY_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["source", "countries"],
    "properties": {
        "source": {"type": "string"},
        "countries": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "countryCode",
                    "countryName",
                    "languages",
                    "population",
                    "description",
                ],
                "properties": {
                    "countryCode": {
                        "type": "string",
                        "minLength": 2,
                        "maxLength": 2,
                    },
                    "countryName": {"type": "string"},
                    "languages": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "population": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "description": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}
