from fastapi.responses import JSONResponse

def success(data=None, message="Success", status=200):
    return JSONResponse(
        content={"code": status, "message": message, "data": data},
        status_code=status
    )

def error(message="Error", status=500):
    return JSONResponse(
        content={"code": status, "message": message, "data": None},
        status_code=status
    )
