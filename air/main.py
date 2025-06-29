import json
from google.cloud import storage, bigquery

BUCKET_NAME = "bucket_mspr3"
STAGING_TABLE = "valid-perigee-415608.environment_data.staging_air"
STATUS_TABLE = "valid-perigee-415608.environment_data.processing_status"

def process_air_json(event, context):
    storage_client = storage.Client()
    bq_client = bigquery.Client()
    file_name = event['name']
    if not file_name.endswith('-aqicn.json'):
        return

    ville = file_name.split('/')[-1].replace('-aqicn.json', '')

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    data = json.loads(blob.download_as_string())

    try:
        d = data['data']
        ts = d['time']['iso']
        aqi = d.get('aqi')
        pm25 = d.get('iaqi', {}).get('pm25', {}).get('v')
        pm10 = d.get('iaqi', {}).get('pm10', {}).get('v')
        no2 = d.get('iaqi', {}).get('no2', {}).get('v')
        o3 = d.get('iaqi', {}).get('o3', {}).get('v')
        
        row = [{
            "ville": ville,
            "collecte_timestamp": ts,
            "aqi": aqi,
            "pm25": pm25,
            "pm10": pm10,
            "no2": no2,
            "o3": o3,
            "source_file": file_name
        }]

        errors = bq_client.insert_rows_json(STAGING_TABLE, row)
        etat = "traité" if not errors else "erreur"
        message = "" if not errors else str(errors)
    except Exception as e:
        etat = "erreur"
        message = str(e)
        ts = None

    # Update status table
    status_row = [{
        "filename": file_name,
        "ville": ville,
        "api_source": "aqicn",
        "collecte_timestamp": ts,
        "etat": etat,
        "message": message
    }]
    bq_client.insert_rows_json(STATUS_TABLE, status_row)
