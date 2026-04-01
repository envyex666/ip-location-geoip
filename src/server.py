import logging
import os
from contextlib import asynccontextmanager
from enum import IntEnum

import geoip2.database
import geoip2.errors
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

secret_token = os.environ.get("SECRET_TOKEN", "").strip()


class ResponseCode(IntEnum):
    OK = status.HTTP_200_OK
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR


class ApiResponse(BaseModel):
    code: ResponseCode


class LogReport(BaseModel):
    ip: str
    country_code: str


def make_error_response(http_status: ResponseCode) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content=ApiResponse(code=http_status).model_dump(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.geoip_reader = geoip2.database.Reader("db/GeoLite2-Country.mmdb")
    logger.info("GeoIP reader opened")
    try:
        yield
    finally:
        app.state.geoip_reader.close()
        logger.info("GeoIP reader closed")


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.headers.get("AUTH_TOKEN", "").strip() != secret_token:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    return await call_next(request)


@app.post("/api/v1/report", response_model=ApiResponse)
async def get_ip(request: Request):
    client = request.client
    if client is None or not client.host:
        return make_error_response(ResponseCode.BAD_REQUEST)

    client_host = client.host

    try:
        response = request.app.state.geoip_reader.country(client_host)
        country_code = response.country.iso_code

        if country_code is None:
            logger.warning("Country code is none")
            return make_error_response(ResponseCode.NOT_FOUND)

    except geoip2.errors.AddressNotFoundError:
        logger.warning("IP not found in GeoIP database")
        return make_error_response(ResponseCode.NOT_FOUND)

    except Exception:
        logger.exception("Failed to resolve country")
        return make_error_response(ResponseCode.INTERNAL_SERVER_ERROR)

    print(LogReport(ip=client_host, country_code=country_code))
    return ApiResponse(code=ResponseCode.OK)
