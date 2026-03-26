import geoip2.database
import uvicorn
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/report")
def get_ip(request: Request):
    client_host = request.client.host

    with geoip2.database.Reader("../Maxmind_CountryDB/GeoLite2-Country.mmdb") as reader:
        response = reader.country(client_host)
        print(
            "report_recieved ",
            "IP:",
            client_host,
            "Country_Code:",
            response.country.iso_code,
            "Country_name:",
            response.country.name,
        )

    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
