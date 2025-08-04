import requests

API_BASE_URL = "https://lab-db-i793.onrender.com"

# ---------------------
# ✅ LOGIN
# ---------------------
def login_user(username: str, password: str):
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"full_name": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()
    return None

# ---------------------
# ✅ EQUIPMENT
# ---------------------
def get_equipment(token, lab_id=None):
    headers = {"Authorization": f"Bearer {token}"}
    params = {}
    if lab_id:
        params["lab_id"] = lab_id

    res = requests.get(f"{API_BASE_URL}/equipment/", headers=headers, params=params)
    if res.status_code == 200:
        return res.json()
    return []

def search_equipment(token, query, lab_id=None):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"search": query}
    if lab_id:
        params["lab_id"] = lab_id

    res = requests.get(f"{API_BASE_URL}/equipment/", headers=headers, params=params)
    if res.status_code == 200:
        return res.json()
    return []


def add_equipment(token: str, data: dict):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(f"{API_BASE_URL}/equipment/", headers=headers, json=data)  # MUST be json=


def update_equipment(token: str, equipment_id: int, update_data: dict):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{API_BASE_URL}/equipment/{equipment_id}"
    response = requests.put(url, headers=headers, json=update_data)
    return response

def delete_equipment(token, equipment_id):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(f"{API_BASE_URL}/equipment/equipment/{equipment_id}", headers=headers)



# ---------------------
# ✅ DOCTOR ENDPOINTS
# ---------------------
def get_technicians(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE_URL}/technicians/technician/technicians/", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []


def submit_test_request(token, patient_name, test_type, equipment_id, technician_id):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "patient_name": patient_name,
        "test_type": test_type,
        "equipment_id": equipment_id,
        "technician_id": technician_id
    }
    response = requests.post(
        f"{API_BASE_URL}/doctor/submit-request/",
        json=payload,
        headers=headers
    )
    return response

def get_my_requests(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/doctor/my-requests/", headers=headers)
    return response.json() if response.status_code == 200 else []

def get_my_results(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/doctor/test-results/", headers=headers)
    return response.json() if response.status_code == 200 else []


# ---------------------
# ✅ TECHNICIAN ENDPOINTS
# ---------------------
def get_pending_requests(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/technicians/technician/pending-requests/", headers=headers)
    return response.json() if response.status_code == 200 else []

def get_doctors(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/technician/doctors/", headers=headers)
    return response.json() if response.status_code == 200 else []

def upload_result(token, request_id, result_text, doctor_id, result_file):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    files = {
        "result_file": (result_file.name, result_file, result_file.type)
    }
    data = {
        "request_id": str(request_id),
        "details": result_text,
        "doctor_id": str(doctor_id)
    }
    response = requests.post(
        f"{API_BASE_URL}/technicians/technician/upload_result/",
        headers=headers,
        files=files,
        data=data
    )
    return response

# ---------------------
# ✅ REGISTRATION
# ---------------------
def register_user(full_name, email, password, role):
    payload = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "role": role,
    }
    return requests.post(f"{API_BASE_URL}/auth/register", json=payload)


# ---------------------
# ✅ TEST REQUESTS
# ---------------------

def get_all_test_requests(token: str):
    url = f"{API_BASE_URL}/admin/test-requests"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        print(f"Failed to fetch test requests: {res.status_code}, {res.text}")
        return []
