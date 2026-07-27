from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from flask import Flask, jsonify


@dataclass(slots=True)
class ApiError(Exception):
    code: str
    message: str
    status_code: int
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)


def error_payload(error: ApiError) -> dict[str, object]:
    error_body: dict[str, object] = {
        "code": error.code,
        "message": error.message,
    }
    if error.details:
        error_body["details"] = error.details
    return {"error": error_body}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify(error_payload(error)), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        error = ApiError(
            code="route_not_found",
            message="The requested endpoint does not exist.",
            status_code=404,
        )
        return jsonify(error_payload(error)), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        error = ApiError(
            code="method_not_allowed",
            message="The HTTP method is not allowed for this endpoint.",
            status_code=405,
        )
        return jsonify(error_payload(error)), 405

    @app.errorhandler(500)
    def handle_internal_error(_error):
        error = ApiError(
            code="internal_server_error",
            message="The service could not complete the request.",
            status_code=500,
        )
        return jsonify(error_payload(error)), 500
