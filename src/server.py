import logging
import os
from contextlib import asynccontextmanager

import geoip2.database
import geoip2.errors
import uvicorn
from fastapi import APIRouter, FastAPI, Request, Response, status
from pydantic import BaseModel

logging.basicConfig(
    level=logging.WARNING,
    format="log %(asctime)s %(message)s",
    datefmt="%Y.%d.%m %H:%M",
    force=True,
)


class LogReport(BaseModel):
    ip: str
    country_code: str


class StatusResponse(BaseModel):
    status_code: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.secret_token = os.getenv("SECRET_TOKEN", "").strip()
    db_dir = os.getenv("DB_DIR", "db").strip()
    db_path = os.path.join(db_dir, "GeoLite2-Country.mmdb")
    if not os.path.isfile(db_path):
        raise FileNotFoundError(db_path)
    app.state.geoip_reader = geoip2.database.Reader(db_path)
    try:
        yield
    finally:
        app.state.geoip_reader.close()


app = FastAPI(lifespan=lifespan)
router = APIRouter(prefix="/v1")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.headers.get("AUTH_TOKEN", "").strip() != request.app.state.secret_token:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    return await call_next(request)


@router.post("/report", response_model=StatusResponse)
async def report(request: Request):
    try:
        assert request.client is not None
        ip = request.client.host

        if not ip:
            logging.warning("client ip is empty")
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        response = request.app.state.geoip_reader.country(ip)
        country_code = response.country.iso_code

        if country_code is None:
            logging.warning("country code not found for this ip %s", ip)
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        print("LogReport:", LogReport(ip=ip, country_code=country_code))
        return StatusResponse(status_code=status.HTTP_200_OK)

    except geoip2.errors.AddressNotFoundError as e:
        logging.warning("ip not found in db: %s", e)
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logging.error("report error: %s", e)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


app.include_router(router, prefix="/api")


def main():
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
