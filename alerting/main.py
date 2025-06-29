import os
from google.cloud import bigquery
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_alert_email(request):
    client = bigquery.Client()
    query = """
      SELECT ville, collecte_timestamp, aqi
      FROM environment_data.alerts_air
      WHERE collecte_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    """
    results = client.query(query).result()
    rows = list(results)
    if not rows:
        return "No alerts to send."

    content = "Alertes AQI > 100 détectées :\n\n"
    for row in rows:
        content += f"Ville : {row.ville}, Date : {row.collecte_timestamp}, AQI : {row.aqi}\n"

    message = Mail(
        from_email='ton_email@exemple.com',
        to_emails='destinataire@exemple.com',
        subject='ALERTE AQI > 100',
        plain_text_content=content)
    try:
        sg = SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
        response = sg.send(message)
        return f"Alerte envoyée ! Status : {response.status_code}"
    except Exception as e:
        return str(e)
