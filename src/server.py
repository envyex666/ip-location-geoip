import logging
import os
from contextlib import asynccontextmanager
from enum import Enum

import geoip2.database
import geoip2.errors
import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse


class ErrorEnum(Enum):
    BAD_REQUEST = 400, "bad request"
    INVALID_IP = 400, "invalid ip"
    IP_NOT_FOUND = 404, "ip not found in database"
    COUNTRY_NOT_FOUND = 404, "country not found"
    INTERNAL_ERROR = 500, "internal error"


def error(err: ErrorEnum) -> JSONResponse:
    status_code, message = err.value
    return JSONResponse(
        status_code=status_code,
        content={"status_code": status_code, "message": message},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").disabled = True

    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(place)s %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(handler)
    logger.propagate = False

    app.state.logger = logger
    app.state.secret_token = os.getenv("SECRET_TOKEN", "").strip()
    app.state.geoip_reader = geoip2.database.Reader("db/GeoLite2-Country.mmdb")
    try:
        yield
    finally:
        app.state.geoip_reader.close()


app = FastAPI(lifespan=lifespan)
router = APIRouter(prefix="/v1")


@app.middleware("http")
async def auth(request: Request, call_next):
    if request.headers.get("AUTH_TOKEN", "").strip() != request.app.state.secret_token:
        return JSONResponse(status_code=401, content={})
    try:
        return await call_next(request)
    except Exception as e:
        request.app.state.logger.exception(str(e), extra={"place": "middleware"})
        return error(ErrorEnum.INTERNAL_ERROR)


@router.post("/report")
async def report(request: Request):
    if not request.client or not request.client.host:
        return error(ErrorEnum.BAD_REQUEST)

    try:
        country_code = request.app.state.geoip_reader.country(
            request.client.host
        ).country.iso_code
        if not country_code:
            return error(ErrorEnum.COUNTRY_NOT_FOUND)
    except geoip2.errors.AddressNotFoundError as e:
        request.app.state.logger.warning(str(e), extra={"place": "geoip"})
        return error(ErrorEnum.IP_NOT_FOUND)
    except ValueError as e:
        request.app.state.logger.warning(str(e), extra={"place": "ip"})
        return error(ErrorEnum.INVALID_IP)
    except Exception as e:
        request.app.state.logger.error(str(e), extra={"place": "report"})
        return error(ErrorEnum.INTERNAL_ERROR)

    print("LogReport:", {"ip": request.client.host, "country_code": country_code})
    return {"status": "ok"}


app.include_router(router, prefix="/api")


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)


if __name__ == "__main__":
    main()
