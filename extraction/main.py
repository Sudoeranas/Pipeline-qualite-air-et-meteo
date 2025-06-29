import functions_framework
import requests
import json
from google.cloud import storage

# CONFIGURATION
OWM_API_KEY = "20cd756e0258ac8ebbbe75a41c2d0c4e"
AQICN_API_KEY = "139b58752a2d617c73003a4ec85ba999dee4e6c9"
BUCKET_NAME = "bucket_mspr3"
FOLDER = "environment-data/"
VILLES = ["Paris", "Lyon", "Marseille", "Lille", "Toulouse", "Nice", "Bordeaux", "Strasbourg", "Nantes", "Rennes"]

@functions_framework.http
def collect_air_weather_data(request):
    client = storage.Client()
    errors = []

    for city in VILLES:
        try:
            # OpenWeatherMap (Météo)
            owm_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric"
            owm_data = requests.get(owm_url).json()
            filename_owm = f"{FOLDER}{city}-owm.json"
            blob_owm = client.bucket(BUCKET_NAME).blob(filename_owm)
            blob_owm.upload_from_string(
                data=json.dumps(owm_data, indent=2),
                content_type="application/json"
            )

            # AQICN (Qualité de l'air)
            aqicn_url = f"https://api.waqi.info/feed/{city}/?token={AQICN_API_KEY}"
            aqicn_data = requests.get(aqicn_url).json()
            filename_aqicn = f"{FOLDER}{city}-aqicn.json"
            blob_aqicn = client.bucket(BUCKET_NAME).blob(filename_aqicn)
            blob_aqicn.upload_from_string(
                data=json.dumps(aqicn_data, indent=2),
                content_type="application/json"
            )

        except Exception as e:
            errors.append({city: str(e)})

    if errors:
        return (json.dumps({"status": "partial_success", "errors": errors}), 207, {'Content-Type': 'application/json'})
    return (json.dumps({
        "status": "success",
        "files": [f"{FOLDER}{v}-owm.json" for v in VILLES] + [f"{FOLDER}{v}-aqicn.json" for v in VILLES]
    }), 200, {'Content-Type': 'application/json'})
