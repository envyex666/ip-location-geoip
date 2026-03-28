import os
from dataclasses import dataclass
from typing import Literal, Optional

import geoip2.database
import geoip2.errors
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI()


class ApiResponse(BaseModel):
    status: Literal["OK", "ERROR"]
    error: Optional[str] = Field(default=None)


@dataclass
class LogReport:
    ip: str
    country_code: str


secret_token: Optional[str] = os.environ.get("SECRET_TOKEN")


def error_response(message: str, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(status="ERROR", error=message).model_dump(),
    )


@app.middleware("http")
async def check_token(request: Request, call_next):
    token = request.headers.get("AUTH_TOKEN")

    if secret_token is None or secret_token.isspace():
        return error_response("You must write token or token is empty", status_code=500)

    if token != secret_token:
        return error_response("Unauthorized", status_code=401)

    return await call_next(request)


@app.post("/report", response_model=ApiResponse)
async def get_ip(request: Request) -> ApiResponse:
    try:
        if request.client is None:
            return ApiResponse(status="ERROR", error="Cant determine client IP")

        client_host = request.client.host
        if not client_host:
            return ApiResponse(status="ERROR", error="Client host is empty")

        with geoip2.database.Reader("db/GeoLite2-Country.mmdb") as reader:
            response = reader.country(client_host)

        country_code = response.country.iso_code
        if country_code is None:
            return ApiResponse(status="ERROR", error="Cant determine country code")

        print(LogReport(ip=client_host, country_code=country_code))
        return ApiResponse(status="OK", error=None)

    except geoip2.errors.AddressNotFoundError:
        return ApiResponse(
            status="ERROR",
            error="No Adress in GeoIP database",
        )
    except Exception as e:
        return ApiResponse(
            status="ERROR",
            error=f"Unknown error: {str(e)}",
        )
