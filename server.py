from fastapi import FastAPI, Request
import geoip2.database
import uvicorn

app = FastAPI()

@app.post("/client-data")
def get_ip(request: Request):
    client_host = request.client.host

    with geoip2.database.Reader('db/GeoLite2-Country.mmdb') as reader:
        response = reader.country(client_host)
        print('IP:', client_host, '\nCountry_Code:', response.country.iso_code, '\nCountry_name:', response.country.name)
    return {"status": "OK"}
