# Geoip reports
### Description
This app on python for get client location from his ip by request.

Download link Maxmind-Database
[GeoLite2-Country.mmdb](https://git.io/GeoLite2-Country.mmdb)

You should put database in db directory
## Start
Prepare python virtual enviroments.
```bash
python3 -m venv venv
source venv/bin/activate
install requirements
pip install -r requirements.txt
```
Start your server.
```bash
SECRET_TOKEN="123" uvicorn server:app --host 127.0.0.1 --port 8081 --app-dir src/
```
If you want to change database directory
```bash
SECRET_TOKEN="123" DB_DIR="test" uvicorn server:app --host 0.0.0.0 --port 8081
```
Request example
```bash
curl -X POST -H "AUTH_TOKEN: 123" "http://127.0.0.1:8081/api/v1/report"
```
