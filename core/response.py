from fastapi.responses import JSONResponse

def success(data=None, message="Success", status=200):
    return JSONResponse(
        content={"status": "success", "message": message, "data": data},
        status_code=status
    )

def error(message="Error", status=500):
    return JSONResponse(
        content={"status": "error", "message": message},
        status_code=status
    )
