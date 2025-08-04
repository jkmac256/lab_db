import os
from google.cloud import storage
from google.oauth2 import service_account
from fastapi import UploadFile
from datetime import datetime, timedelta

CREDENTIALS_FILE = "backend\gcs_creds.json"  # path to your JSON credentials file
BUCKET_NAME = "medicallab-results-buckect"  # your GCS bucket name

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
client = storage.Client(credentials=credentials)
bucket = client.bucket(BUCKET_NAME)

def upload_file_to_gcs(file: UploadFile, request_id: int, make_public=False) -> str:
    filename = f"test-results/{datetime.utcnow().strftime('%Y%m%d%H%M')}_{file.filename}"
    blob = bucket.blob(filename)

    blob.upload_from_file(file.file, content_type=file.content_type)

    if make_public:
        blob.make_public()
        return blob.public_url
    else:
        return filename  


def generate_signed_url(blob_path: str, expiration_minutes: int = 30) -> str:
    """
    Generate a signed URL for securely downloading a GCS object.
    
    :param blob_path: Full path of the file in the bucket (e.g., "test-results/202508041234_file.pdf")
    :param expiration_minutes: How long the signed URL should be valid for.
    :return: Signed URL as a string
    """
    try:
        blob = bucket.blob(blob_path)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        return url
    except Exception as e:
        raise Exception(f"Signed URL generation failed: {e}")
