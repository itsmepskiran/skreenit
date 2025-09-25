from fastapi import FastAPI
from fastapi.responses import JSONResponse

class AppError(Exception):
    status_code = 400
    code = "app_error"
    def __init__(self, message: str, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.message = message

class NotFoundError(AppError):
    status_code = 404
    code = "not_found"

class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"

class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"

class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={
            "ok": False,
            "error": {"code": exc.code, "message": exc.message}
        })
