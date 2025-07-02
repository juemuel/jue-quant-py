from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.exceptions import DataProviderError, DataEmptyError, DataFieldMissingError, DataAccessDeniedError, InvalidParameterError

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(DataEmptyError)
    async def handle_data_empty_error(request: Request, exc: DataEmptyError):
        return JSONResponse(
            content={"status": "warning", "message": exc.message, "detail": exc.detail},
            status_code=exc.status_code
        )

    @app.exception_handler(DataFieldMissingError)
    async def handle_field_missing_error(request: Request, exc: DataFieldMissingError):
        return JSONResponse(
            content={"status": "error", "message": exc.message, "detail": exc.detail},
            status_code=exc.status_code
        )

    @app.exception_handler(DataAccessDeniedError)
    async def handle_access_denied_error(request: Request, exc: DataAccessDeniedError):
        return JSONResponse(
            content={"status": "forbidden", "message": exc.message, "detail": exc.detail},
            status_code=exc.status_code
        )

    @app.exception_handler(InvalidParameterError)
    async def handle_invalid_parameter(request: Request, exc: InvalidParameterError):
        return JSONResponse(
            content={"status": "invalid", "message": exc.message, "detail": exc.detail},
            status_code=exc.status_code
        )

    @app.exception_handler(DataProviderError)
    async def handle_data_provider_error(request: Request, exc: DataProviderError):
        return JSONResponse(
            content={"status": "error", "message": exc.message, "detail": exc.detail},
            status_code=exc.status_code
        )

    # 默认兜底异常处理
    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        return JSONResponse(
            content={"status": "unknown", "message": "发生未知错误", "detail": str(exc)},
            status_code=500
        )
