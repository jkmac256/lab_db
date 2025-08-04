import os
from google.cloud import storage
from google.oauth2 import service_account
from fastapi import UploadFile
from datetime import datetime

CREDENTIALS_FILE = "backend/gcs_creds.json"  # path to your JSON credentials file
BUCKET_NAME = "medicallab-results-buckect"  # your GCS bucket name

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
client = storage.Client(credentials=credentials)
bucket = client.bucket(BUCKET_NAME)

def upload_file_to_gcs(file: UploadFile, destination_folder: str) -> str:
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"{destination_folder}/{timestamp}_{file.filename}"

        blob = bucket.blob(filename)
        blob.upload_from_file(file.file, content_type=file.content_type)

        # Don't make it public
        return f"gs://{BUCKET_NAME}/{filename}"
    except Exception as e:
        raise Exception(f"GCS upload failed: {e}")
