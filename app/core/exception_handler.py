# app/core/exception_handler.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def handle_unexpected_error(request, exc):
        return JSONResponse(content={"status": "error", "message": str(exc)}, status_code=500)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request, exc):
        return JSONResponse(content={"status": "error", "message": "Invalid request parameters", "errors": exc.errors()}, status_code=400)
