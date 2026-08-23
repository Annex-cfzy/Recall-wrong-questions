"""Unified API response envelope.

Every non-streaming API returns: {"code": 0, "message": "success", "data": ...}
Business error codes follow the segments defined in the dev plan.
"""
from __future__ import annotations

from typing import Any


def success_response(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def error_response(code: int, message: str, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
