from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "app_error"):
        self.status_code = status_code
        self.code = code
        self.message = message

class NotFoundError(AppError):
    def __init__(self, message: str = "Not found"):
        super().__init__(message, status_code=404, code="not_found")

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401, code="unauthorized")

class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403, code="forbidden")

class ValidationError(AppError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422, code="validation_error")

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"ok": False, "error": exc.code, "message": exc.message}
        )
