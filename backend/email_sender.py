# utils/email_sender.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Loads .env

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_SENDER = os.getenv("MAILGUN_SENDER")

def send_mailgun_email(to_email: str, subject: str, message: str, file_path: str):
    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    with open(file_path, "rb") as f:
        files = {"attachment": (os.path.basename(file_path), f)}

        data = {
            "from": MAILGUN_SENDER,
            "to": [to_email],
            "subject": subject,
            "text": message
        }

        response = requests.post(
            url,
            auth=("api", MAILGUN_API_KEY),
            files=files,
            data=data
        )

    if response.status_code != 200:
        raise Exception(f"Mailgun error: {response.status_code} {response.text}")

    return response.json()
