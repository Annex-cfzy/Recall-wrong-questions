"""Global exception handling.

Business exceptions (AppException) are returned with HTTP 200 + a business
error code, so the frontend only checks `code` (per dev plan 1.5).
"""
from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.response import error_response


class AppException(Exception):
    """Raise with a business error code + Chinese message."""

    def __init__(self, code: int, message: str, data: Any | None = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=200, content=error_response(exc.code, exc.message, exc.data))


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # FastAPI returns 422 for invalid params; normalise to business code 1001.
    return JSONResponse(
        status_code=200,
        content=error_response(1001, "请求参数校验失败，请检查输入"),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=error_response(9000, "服务器内部错误"))
