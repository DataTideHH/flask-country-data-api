from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml
from openapi_spec_validator import validate

from country_api import create_app


OPENAPI_PATH = Path(__file__).resolve().parents[1] / "openapi" / "openapi.yaml"


class OpenApiContractTest(unittest.TestCase):
    def test_openapi_document_is_valid_and_covers_runtime_routes(self):
        document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
        validate(document)

        self.assertEqual(document["openapi"], "3.1.0")
        self.assertEqual(document["info"]["title"], "Flask Country Data API")

        with tempfile.TemporaryDirectory() as temporary_directory:
            app = create_app(
                {
                    "TESTING": True,
                    "DATABASE_PATH": str(Path(temporary_directory) / "country.sqlite"),
                }
            )
            runtime_paths = {
                rule.rule.replace("<code>", "{code}")
                for rule in app.url_map.iter_rules()
                if rule.endpoint != "static"
            }

        self.assertEqual(set(document["paths"]), runtime_paths)

        operation_ids = [
            operation["operationId"]
            for path_item in document["paths"].values()
            for method, operation in path_item.items()
            if method in {"get", "post", "put", "patch", "delete"}
        ]
        self.assertEqual(len(operation_ids), len(set(operation_ids)))

    def test_openapi_document_is_served_by_the_application(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            app = create_app(
                {
                    "TESTING": True,
                    "DATABASE_PATH": str(Path(temporary_directory) / "country.sqlite"),
                }
            )
            response = app.test_client().get("/openapi/openapi.yaml")

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/yaml", response.content_type)
        self.assertIn(b"openapi: 3.1.0", response.data)


if __name__ == "__main__":
    unittest.main()
