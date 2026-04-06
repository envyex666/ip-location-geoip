# Geoip reports
### Description
This app for get client location from his ip by request.

### Database
[GeoLite2-Country.mmdb](https://git.io/GeoLite2-Country.mmdb)

## Start
Prepare python virtual enviroments.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
wget https://git.io/GeoLite2-Country.mmdb
mv GeoLite2-Country.mmdb db/
chmod +r db/GeoLite2-Country.mmdb
```
Start your server.
```bash
uvicorn server:app --host 127.0.0.1 --port 8081 --app-dir src/
```
Required parameter SECRET_TOKEN="123"

(Optional) DB_PATH="test/GeoLite2-Country.mmdb"

Request example
```bash
curl -X POST -H "AUTH_TOKEN: 123" "http://127.0.0.1:8081/api/v1/report"
```
