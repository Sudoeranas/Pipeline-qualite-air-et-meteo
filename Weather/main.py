import json
from google.cloud import storage, bigquery
from datetime import datetime, timezone

BUCKET_NAME = "bucket_mspr3"
STAGING_TABLE = "valid-perigee-415608.environment_data.staging_weather"
STATUS_TABLE = "valid-perigee-415608.environment_data.processing_status"

def process_weather_json(event, context):
    storage_client = storage.Client()
    bq_client = bigquery.Client()
    file_name = event['name']
    if not file_name.endswith('-owm.json'):
        return

    ville = file_name.split('/')[-1].replace('-owm.json', '')

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    data = json.loads(blob.download_as_string())

    try:
        dt_utc = datetime.utcfromtimestamp(data['dt']).replace(tzinfo=timezone.utc).isoformat()
        temp = data['main']['temp']
        humidite = data['main']['humidity']
        vent_vitesse = data['wind']['speed']
        meteo_code = data['weather'][0]['id']
        
        row = [{
            "ville": ville,
            "collecte_timestamp": dt_utc,
            "temperature": temp,
            "humidite": humidite,
            "vent_vitesse": vent_vitesse,
            "meteo_code": meteo_code,
            "source_file": file_name
        }]
        errors = bq_client.insert_rows_json(STAGING_TABLE, row)
        etat = "traité" if not errors else "erreur"
        message = "" if not errors else str(errors)
    except Exception as e:
        etat = "erreur"
        message = str(e)
        dt_utc = None

    # Update status table
    status_row = [{
        "filename": file_name,
        "ville": ville,
        "api_source": "owm",
        "collecte_timestamp": dt_utc,
        "etat": etat,
        "message": message
    }]
    bq_client.insert_rows_json(STATUS_TABLE, status_row)
