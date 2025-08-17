# backend/services/middleware_client.py
import os
import requests
from typing import Dict, Any

MIDDLEWARE_BASE_URL = os.getenv("MIDDLEWARE_BASE_URL")  # e.g., https://middleware.vendor.com/api
MIDDLEWARE_API_KEY = os.getenv("MIDDLEWARE_API_KEY")    # if your vendor gives an API key

class MiddlewareError(Exception):
    pass

def fetch_result_from_middleware(request_id: int, equipment_id: int) -> Dict[str, Any]:
    """
    Call your online LIS middleware to fetch analyzer results for a request/equipment.
    Return a normalized dict that your Streamlit UI can show/edit.
    NOTE: This does NOT save to DB — just returns data for preview.
    """
    # If you haven't configured a real middleware yet, return simulated data for development:
    if not MIDDLEWARE_BASE_URL:
        return {
            "source": "middleware-simulated",
            "test_type": "Electrolytes",
            "values": {"Na": 139.0, "K": 4.3, "Cl": 103.0},
            "unit": "mmol/L",
            "flags": {},
            "analyzer": {"equipment_id": equipment_id, "name": "Demo Analyzer"},
        }

    try:
        headers = {}
        if MIDDLEWARE_API_KEY:
            headers["Authorization"] = f"Bearer {MIDDLEWARE_API_KEY}"

        # Example path – adjust to your vendor’s API
        url = f"{MIDDLEWARE_BASE_URL}/results?request_id={request_id}&equipment_id={equipment_id}"
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        # (Optional) normalize vendor payload to your preferred structure here
        return data
    except Exception as e:
        raise MiddlewareError(str(e))
