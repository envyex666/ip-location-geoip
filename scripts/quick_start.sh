cd .. && python3 -m venv venv
source venv/bin/activate
pip install -r requirements/requirements.txt
cd src && uvicorn server:app --host 0.0.0.0 --port 8081
