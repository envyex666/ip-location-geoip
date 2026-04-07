import logging
import os
from contextlib import asynccontextmanager

import geoip2.database
import geoip2.errors
from fastapi import APIRouter, FastAPI, Request, Response, status
from pydantic import BaseModel


class LogReport(BaseModel):
    ip: str
    country_code: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.WARNING,
        format="log %(asctime)s %(message)s",
        datefmt="%Y.%d.%m.%H:%M",
        force=True,
    )

    secret_token = os.getenv("SECRET_TOKEN", "").strip()
    if not secret_token:
        raise RuntimeError("SECRET_TOKEN is required and must be not empty")

    app.state.secret_token = secret_token

    db_path = os.getenv("DB_PATH", "db/GeoLite2-Country.mmdb").strip()
    app.state.geoip_reader = geoip2.database.Reader(db_path)

    try:
        yield
    finally:
        app.state.geoip_reader.close()


app = FastAPI(lifespan=lifespan)
router = APIRouter(prefix="/v1")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    secret_token = request.app.state.secret_token

    if request.headers.get("AUTH_TOKEN", "").strip() != secret_token:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    return await call_next(request)


@router.post("/report")
async def report(request: Request):
    try:
        assert request.client is not None
        ip = request.client.host

        if not ip:
            logging.warning("client ip is empty")
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        response = request.app.state.geoip_reader.country(ip)
        country_code = response.country.iso_code

        print(f"LogReport ip={ip}, country_code={country_code}")
        return Response(status_code=status.HTTP_200_OK)

    except geoip2.errors.AddressNotFoundError:
        logging.warning(f"{ip} not found in db: %s")
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logging.error("report error: %s", e)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


app.include_router(router, prefix="/api")
