#frontend/main_frontend.py

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import datetime
import os
import time
from components import display_equipment_list
import pandas as pd
from utils import (
    login_user, register_user, get_equipment, search_equipment, add_equipment,
    get_technicians, submit_test_request, get_my_requests, get_my_results,
    get_pending_requests, upload_result, get_doctors, update_equipment, delete_equipment
)


API_URL = "https://lab-db-i793.onrender.com"
TIMEOUT = 300

# Set your timeout limit in seconds (5 minutes = 300s)
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()
if time.time() - st.session_state.last_activity > TIMEOUT:
    st.warning("⏳ Session timed out due to inactivity. Please log in again.")
    if "token" in st.session_state:
        del st.session_state.token
    st.stop()
st.session_state.last_activity = time.time()


def auth_header():
    token = st.session_state.get("token", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

st.set_page_config(page_title="📊 Medical Lab System", layout="centered", page_icon="🚪")

#st_autorefresh(interval=3000, limit=None, key="refresh")

def load_custom_css():
    st.markdown("""
    <style>
    .stApp { background-color: #001f3f; color: #ffffff; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #001a33; color: #ffffff; }
    .css-1d391kg { background-color: #002b5c !important; color: #ffffff !important; border-radius: 8px; }
    .stButton button {
        background-color: #0074D9 !important;
        color: black !important;
        border: none;
        border-radius: 5px;
        padding: 0.5em 1.5em;
    }
    .stButton button:hover {
        background-color: #005fa3 !important;
    }
    .stDownloadButton button {
        background-color: #2ECC40 !important;
        color: white !important;
    }
    .stDownloadButton button:hover {
        background-color: #27ae60 !important;
    }
    </style>
            """, unsafe_allow_html=True)

load_custom_css()

if "token" not in st.session_state: st.session_state.token = None
if "role" not in st.session_state: st.session_state.role = None
if "full_name" not in st.session_state: st.session_state.full_name = None
if "page" not in st.session_state: st.session_state.page = "Home"

def login_user(name, password, lab_name):
    payload = {
        "full_name": name,
        "password": password,
        "lab_name": lab_name  # ✅ always send it, can be None
    }
    res = requests.post(f"{API_URL}/auth/login", json=payload)

    if res.status_code == 200:
        return res.json()
    else:
        return {}


def register_user(full_name, email, password, role, lab_id):
    payload = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "role": role,
        "laboratory_id": lab_id  # ✅ Add this field
    }
    return requests.post(f"{API_URL}/auth/register", json=payload)


# ------------------ DOCTOR DASHBOARD ------------------
def doctor_dashboard():
    page = st.sidebar.radio("Navigation", ["💾 Submit Test", "📋 My Requests", "📈 My Results", "🔍 Equipment"])
    
    if page == "💾 Submit Test":
        st.subheader("Submit Test Request")

        patient_name = st.text_input("Patient Full Name")
        patient_dob = st.date_input("Date of Birth (optional)", format="YYYY-MM-DD")
        patient_gender = st.selectbox("Patient Gender", ["Male", "Female"])

        test_type = st.text_input("Test Type")

        equipment_resp = requests.get(f"{API_URL}/equipment/", headers=auth_header())
        tech_resp = requests.get(f"{API_URL}/doctor/", headers=auth_header())

        equipment_list = equipment_resp.json() if equipment_resp.status_code == 200 else []
        tech_list = tech_resp.json() if tech_resp.status_code == 200 else []

        equipment_options = {f"{e['name']} - {e['description']}": e["id"] for e in equipment_list if e['is_available']}
        technician_options = {t["full_name"]: t["id"] for t in tech_list}

        selected_equipment = st.selectbox("Select Equipment", list(equipment_options.keys()))
        selected_technician = st.selectbox("Assign Technician", list(technician_options.keys()))

        if st.button("Submit Request"):
            if not patient_name or not test_type:
                st.error("Patient name and test type are required.")
            else:
                payload = {
                    "patient_name": patient_name,
                    "patient_dob": str(patient_dob) if patient_dob else None,
                    "patient_gender": patient_gender,
                    "test_type": test_type,
                    "equipment_name": selected_equipment.split(" - ")[0],
                    "technician_id": technician_options[selected_technician]
                }
                res = requests.post(f"{API_URL}/doctor/submit-request/", headers=auth_header(), json=payload)
                st.success("✅ Submitted!") if res.status_code == 200 else st.error(f"❌ Error: {res.text}")
                st.rerun()


    elif page == "📋 My Requests":
        st.subheader("📋 Your Test Requests")
        requests_data = get_my_requests(st.session_state.token)

        if not requests_data:
            st.info("📭 No test requests.")
        else:
            for req in requests_data:
                with st.expander(label=f"🧑 Patient: {req['patient_name']}", expanded=False):
                    st.markdown(f"""
                    **🧑 Patient**: {req['patient_name']}  
                    **🧪 Test Type**: {req['test_type']}  
                    **📅 Requested**: {req['request_date']}  
                    **⚙️ Equipment**: {req.get('equipment_name', 'Unknown')}  
                    **🧪 Technician ID**: {req['technician_id']}  
                    **📊 Status**: `{req.get('status', 'Pending')}`  
                    """)

                    if req.get("result_file_url"):
                        st.download_button(
                            "⬇️ Download Result",
                            data=requests.get(req["result_file_url"]).content,
                            file_name="test_result.pdf"
                        )

                        with st.expander("📤 Share Result"):
                            recipient_email = st.text_input(
                                "Recipient Email",
                                key=f"email_{req['id']}"
                            )
                            message = st.text_area(
                                "Optional Message",
                                key=f"msg_{req['id']}"
                            )
                            if st.button("Send", key=f"send_{req['id']}"):
                                if not recipient_email:
                                    st.error("Please enter a recipient email.")
                                else:
                                    payload = {
                                        "test_request_id": req["id"],
                                        "recipient_email": recipient_email,
                                        "message": message
                                    }
                                    res = requests.post(
                                        f"{API_URL}/doctor/share-result",
                                        headers=auth_header(),
                                        json=payload
                                    )
                                    if res.status_code == 200:
                                        st.success(f"✅ Shared with {recipient_email}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to share: {res.text}")
                                        st.rerun()

                                     #RESULTS PAGE#
    elif page == "📈 My Results":
        st.subheader("📈 Your Test Results")
        results = get_my_results(st.session_state.token)
        if not results:
            st.info("📭 No test results yet.")
        else:
            for res in results:
                with st.expander(f"🧪 {res['test_type']} for {res['patient_name']} ({res['result_date']})"):
                    st.markdown(f"**Patient:** {res['patient_name']}")
                    st.markdown(f"**Test Type:** {res['test_type']}")
                    st.markdown(f"**Details:** {res.get('result_details', 'No details provided')}")
                    st.markdown(f"**Uploaded At:** {res.get('result_date', 'Unknown')}")
                    st.markdown(f"**Status:** {'Seen' if res.get('seen') else 'Pending'}")

                    if res.get("result_file_path"):
                        try:
                            with open(res["result_file_path"], "rb") as f:
                                file_data = f.read()
                            st.download_button(
                                "⬇️ Download Result File",
                                data=file_data,
                                file_name=os.path.basename(res["result_file_path"]),
                                mime="application/octet-stream"
                            )
                        except FileNotFoundError:
                            st.error("❌ Result file not found on the server.")
                            st.rerun()

                    st.markdown("### 📤 Share Result")
                    recipient_email = st.text_input("Recipient Email", key=f"email_{res['id']}")
                    message = st.text_area("Optional Message", key=f"msg_{res['id']}")
                    if st.button("Send", key=f"send_{res['id']}"):
                        if not recipient_email:
                            st.error("Please enter a recipient email.")
                            st.rerun()
                        else:
                            payload = {
                                "result_id": res["id"],
                                "recipient_email": recipient_email,
                                "message": message
                            }
                            share_resp = requests.post(
                                f"{API_URL}/doctor/share-result",
                                headers=auth_header(),
                                json=payload
                            )
                            if share_resp.status_code == 200:
                                st.success(f"✅ Shared with {recipient_email}")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to share: {share_resp.text}")
                                st.rerun()

                                       #EQUIPMENT PAGE#
    elif page == "🔍 Equipment":
        st.subheader("🔍 View Equipment")
        display_equipment_list(st.session_state.token, can_edit=False)



# ------------------ TECHNICIAN DASHBOARD ------------------
def technician_dashboard():
    page = st.sidebar.radio("Navigation", ["📥 Pending Requests", "📤 Upload Result", "🔍 Equipment"])
    if page == "📥 Pending Requests":
        st.subheader("📥 Pending Test Requests")

        requests_data = requests.get(
            f"{API_URL}/technicians/technician/pending-requests/",
            headers=auth_header()
        ).json()

        if not requests_data:
            st.info("📭 No test requests.")
        else:
            for req in requests_data:
                with st.expander(label=f"🧑 Patient: {req['patient_name']}", expanded=False):
                    st.markdown(f"""
                    **📄 Request ID**: {req['id']}  
                    **🧑 Patient**: {req['patient_name']}  
                    **🧪 Test Type**: {req['test_type']}  
                    **📅 Date**: {req['request_date']}  
                    **⚙️ Equipment**: {req.get('equipment_name', 'Unknown')}  
                    """)

                                # 📤 Upload Result page
    elif page == "📤 Upload Result":
        st.subheader("📤 Upload Test Result")
        requests_data = get_pending_requests(st.session_state.token)
        if not requests_data:
            st.info("📭 No pending requests.")
            st.stop()
    
        # Map requests to a display label
        label_map = {f"{r['id']} - {r['patient_name']} - {r['test_type']}": r for r in requests_data}
        selected_label = st.selectbox("Select Request", list(label_map.keys()))
        selected_request = label_map[selected_label]
    
        doctor_id = selected_request.get("doctor", {}).get("id") or selected_request.get("doctor_id")
        if not doctor_id:
            st.error("❌ Doctor info missing.")
            st.stop()
    
        # --- Mode Selection ---
        mode = st.radio("Choose Input Method:", ["Manual Upload", "Fetch from LIS"])
    
        result_text = ""
        result_file = None
    
        if mode == "Manual Upload":
            result_text = st.text_area("📝 Result Details")
            result_file = st.file_uploader("📁 Upload File", type=["pdf", "txt", "docx"])
    
        elif mode == "Fetch from LIS":
            if st.button("🔄 Fetch from LIS"):
                res = fetch_from_lis(
                    token=st.session_state.token,
                    request_id=selected_request["id"]
                )
                if res.status_code == 200:
                    lis_data = res.json()
                    st.success("✅ Data fetched from LIS")
                    result_text = st.text_area("📝 Result Details (Pre-filled, editable)", value=lis_data.get("result_text", ""))
                else:
                    st.error(f"❌ Failed to fetch from LIS: {res.text}")
    
        # --- Submit Section ---
        if st.button("🚀 Submit Result"):
            if not result_text:
                st.warning("⚠️ Result text is required.")
            else:
                res = upload_result(
                    token=st.session_state.token,
                    request_id=selected_request["id"],
                    result_text=result_text,
                    doctor_id=doctor_id,
                    result_file=result_file
                )
                st.success("✅ Uploaded!") if res.status_code == 200 else st.error(f"❌ Upload failed: {res.text}")



                                           #Equipment page#
    elif page == "🔍 Equipment":
        st.subheader("🔍 Manage Equipment")
        display_equipment_list(st.session_state.token, can_edit=True)

        user_id = st.session_state.get("user", {}).get("id")  # Make sure user info is stored

        if not user_id:
            st.error("❌ User ID not found. Please log in again.")
            st.rerun()
        else:
            # ➕ Add new equipment
            st.markdown("### ➕ Add Equipment")
            new_name = st.text_input("Name", key="add_eq_name")
            new_type = st.text_input("Type", key="add_eq_type")
            new_desc = st.text_input("Description", key="add_eq_desc")
            new_status = st.selectbox("Availability", [True, False], key="add_eq_status")
            new_serviced_date = st.date_input("Last Serviced", value=datetime.date.today(), key="add_eq_serviced")

            if st.button("➕ Add Equipment", key="add_eq_btn"):
                payload = {
                    "name": new_name,
                    "type": new_type,
                    "description": new_desc,
                    "is_available": new_status,
                    "last_serviced": str(new_serviced_date),
                    "added_by_id": user_id  # ✅ This is required
                }

                res = add_equipment(st.session_state.token, payload)
                if res.status_code == 200:
                    st.success("✅ Added")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {res.text}")
                    st.rerun()


# ------------------ ADMIN DASHBOARD ------------------
#admin_lab_id = st.session_state.get("lab_id")

def admin_dashboard():
    admin_lab_id = st.session_state.get("lab_id")
    headers = auth_header()
    st.title("👨‍⚕️ Admin Dashboard")

    page = st.sidebar.radio("📋 Admin Menu", [
        "👥 Manage Users",
        "🧪 Test Requests",
        "📄 Test Results",
        "🔬 Equipment",
        "🗂️ All Patients"
    ])
                                       #Manage Users Page#
    if page == "👥 Manage Users":
        st.subheader("👥 Manage Users")

        # === Role Filter and Fetch Users ===
        role_filter = st.selectbox("Filter by Role", ["ALL", "DOCTOR", "LAB_TECHNICIAN", "PATIENT"])
        user_url = f"{API_URL}/users/all/?lab_id={admin_lab_id}"
        if role_filter != "ALL":
            user_url += f"&role={role_filter}"

        users = requests.get(user_url, headers=headers).json()
        if not users:
            st.info("No users found.")
            return

        # === Display Users Table ===
        users_df = pd.DataFrame(users)
        if not users_df.empty:
            st.dataframe(users_df[["id", "full_name", "email", "role"]])

        # === Select and View User Details ===
        user_options = {f"{u['full_name']} ({u['role']})": u['id'] for u in users}
        selected_user_name = st.selectbox("Select a user to view details", options=list(user_options.keys()))
        selected_user_id = user_options[selected_user_name]

        user_details_resp = requests.get(f"{API_URL}/users/{selected_user_id}", headers=headers)
        if user_details_resp.status_code != 200:
            st.error("❌ Failed to load user details.")
            st.rerun()
            return

        user_details = user_details_resp.json()
        st.markdown(f"### 👤 Details for {user_details['full_name']} ({user_details['role']})")
        st.write({
            "ID": user_details["id"],
            "Email": user_details["email"],
            "Role": user_details["role"],
        })

        # === EDIT USER INFO ===
        with st.expander("✏️ Edit User Info"):
            updated_name = st.text_input("Edit Full Name", user_details["full_name"])
            updated_email = st.text_input("Edit Email", user_details["email"])
            updated_role = st.selectbox("Edit Role", ["DOCTOR", "LAB_TECHNICIAN", "PATIENT", "ADMIN"], index=["DOCTOR", "LAB_TECHNICIAN", "PATIENT", "ADMIN"].index(user_details["role"]))

            if st.button("💾 Save Changes"):
                payload = {
                    "full_name": updated_name,
                    "email": updated_email,
                    "role": updated_role,
                }
                update_resp = requests.put(f"{API_URL}/users/{selected_user_id}", headers=headers, json=payload)
                if update_resp.status_code == 200:
                    st.success("✅ User updated successfully.")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to update user: {update_resp.text}")
                    st.rerun()

        # === Show Extra Info Based on Role ===
        role = user_details.get("role", "").upper()

        if role == "DOCTOR":
            st.markdown("#### 🧪 Test Requests by Doctor")
            reqs_resp = requests.get(f"{API_URL}/users/doctor/test-requests/{selected_user_id}", headers=headers)
            if reqs_resp.status_code == 200:
                reqs = reqs_resp.json()
                st.dataframe(pd.DataFrame(reqs) if reqs else [])
            else:
                st.error("❌ Failed to fetch test requests.")

            st.markdown("#### 🩺 Patients Handled by Doctor")
            patients = user_details.get("patients", [])
            st.dataframe(pd.DataFrame(patients) if patients else [])

        elif role == "LAB_TECHNICIAN":
            st.markdown("#### 📄 Test Results by Technician")
            results_resp = requests.get(f"{API_URL}/users/technician/test-results/{selected_user_id}", headers=headers)
            if results_resp.status_code == 200:
                results = results_resp.json()
                st.dataframe(pd.DataFrame(results) if results else [])
            else:
                st.error("❌ Failed to fetch test results.")

        # === DELETE USER ===
        st.divider()
        if st.button(f"🗑️ Delete user {user_details['full_name']}"):
            confirm = st.radio("Are you sure?", ["No", "Yes, delete user"])
            if confirm == "Yes, delete user":
                del_resp = requests.delete(f"{API_URL}/users/{selected_user_id}", headers=headers)
                if del_resp.status_code == 200:
                    st.success("✅ User deleted successfully.")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to delete user: {del_resp.text}")

        # === ADD NEW USER ===
        st.divider()
        st.markdown("### ➕ Add New User")
        with st.form("add_user_form"):
            new_full_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["DOCTOR", "LAB_TECHNICIAN", "PATIENT", "ADMIN"])

            submitted = st.form_submit_button("Add User")
            if submitted:
                if not new_full_name or not new_email or not new_password or not new_role:
                    st.warning("⚠️ Please fill in all fields.")
                else:
                    payload = {
                        "full_name": new_full_name,
                        "email": new_email,
                        "password": new_password,
                        "role": new_role,
                        "laboratory_id": admin_lab_id  # ✅ Pass the admin's lab ID here!
                    }
                    add_resp = requests.post(f"{API_URL}/users/create/", headers=headers, json=payload)
                    if add_resp.status_code in (200, 201):
                        st.success(f"✅ User {new_full_name} added successfully.")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add user: {add_resp.text}")


        
                                        # === TEST REQUESTS Page ===
    elif page == "🧪 Test Requests":
        st.subheader("🧪 All Test Requests")
        reqs = requests.get(f"{API_URL}/admin/test-requests?lab_id={admin_lab_id}", headers=headers).json()


        if not reqs:
            st.info("📭 No test requests found.")
        else:
            test_types = list(set(r["test_type"] for r in reqs))
            selected_type = st.selectbox("Filter by Test Type", ["All"] + test_types)
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Completed", "Seen"])

            filtered = [
                r for r in reqs
                if (selected_type == "All" or r["test_type"] == selected_type) and
                (status_filter == "All" or r.get("status") == status_filter)
            ]

            if filtered:
                df = pd.DataFrame(filtered)
                
                df.rename(columns={
                    "id": "Request ID",
                    "doctor_id": "Doctor ID",
                    "patient_name": "Patient",
                    "test_type": "Test Type",
                    "request_date": "Requested At",
                    "status": "Status"
                }, inplace=True)

                if "Requested At" in df.columns:
                    df["Requested At"] = pd.to_datetime(df["Requested At"]).dt.strftime("%Y-%m-%d %H:%M")

                st.dataframe(df)  # or st.table(df)

                # Export filtered data as CSV
                csv_data = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Export to CSV", csv_data, "test_requests.csv", "text/csv")
            else:
                st.info("No test requests match the selected filters.")


                                    # === TEST RESULTS page ===
    elif page == "📄 Test Results":
        st.subheader("📄 Test Results")

        res = requests.get(f"{API_URL}/admin/test-results/?lab_id={admin_lab_id}", headers=headers)

        try:
            results = res.json()
        except ValueError:
            st.error("❌ Failed to decode JSON from response.")
            st.stop()

        if isinstance(results, dict) and "detail" in results:
            st.error(f"❌ Error from backend: {results['detail']}")
        elif isinstance(results, list) and results:
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(results)

            df.rename(columns={
                "id": "Result ID",
                "test_request_id": "Test Request ID",
                "uploaded_by": "Uploaded By",
                "result_data": "Result Data",
                "uploaded_at": "Uploaded At"
            }, inplace=True)
            
            st.dataframe(df)  # Or st.table(df)
        else:
            st.info("No test results found.")


                                        # === EQUIPMENT PAGE===
    elif page == "🔬 Equipment":
        st.subheader("🔬 Equipment")
        display_equipment_list(st.session_state.token, lab_id=admin_lab_id, can_edit=True)


                                 # === View All Patients in the System === 
    elif page == "🗂️ All Patients":
        st.markdown("### 🗂️ All Patients in the System")
        patients_resp = requests.get(f"{API_URL}/patients/all/?lab_id={admin_lab_id}", headers=headers)
        if patients_resp.status_code == 200:
            patients = patients_resp.json()
            st.dataframe(pd.DataFrame(patients) if patients else [])
        else:
            st.error("❌ Failed to fetch patients.")
            
#..................superadmin...................
def manage_labs():
    st.subheader("🗂️ Manage Laboratories")

    st.write("### ➕ Add a new laboratory")

    name = st.text_input("Lab Name")
    address = st.text_input("Address")
    contact_email = st.text_input("Contact Email")

    if st.button("Add Laboratory"):
        if name:
            payload = {
                "name": name,
                "address": address,
                "contact_email": contact_email
            }
            res = requests.post(f"{API_URL}/superadmin/labs", json=payload)
            if res.status_code == 200:
                st.success("✅ Lab added successfully.")
                st.rerun()  # ✅ Refresh to show new lab!
            else:
                st.error(f"❌ Failed to add: {res.text}")
        else:
            st.warning("Please enter at least a lab name.")

    st.write("### 🗂️ Existing Laboratories:")

    # ✅ Always check response status & .json()
    res = requests.get(f"{API_URL}/superadmin/labs")
    if res.status_code == 200:
        labs = res.json()

        if not labs:
            st.info("No laboratories found.")
        else:
            for lab in labs:
                st.write(f"- **{lab['name']}** | 📧 {lab.get('contact_email', 'N/A')} | 📍 {lab.get('address', 'N/A')}")
                if st.button(f"❌ Delete {lab['name']}", key=f"delete_{lab['id']}"):
                    delete_res = requests.delete(f"{API_URL}/superadmin/labs/{lab['id']}")
                    if delete_res.status_code == 200:
                        st.success("✅ Lab deleted.")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete: {delete_res.text}")
    else:
        st.error(f"❌ Failed to load labs: {res.text}")



# ------------------ MAIN APP ------------------
st.sidebar.title("🧪 MedLab System")
if st.session_state.token:
    st.sidebar.markdown(f"👋 Welcome **{st.session_state.full_name}** ({st.session_state.role.capitalize()})")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.token = None
        st.session_state.role = None
        st.session_state.full_name = None
        st.rerun()

    st.title("📊 Medical Lab Dashboard")
    if st.session_state.role.lower() == "doctor":
        doctor_dashboard()
    elif st.session_state.role.lower() == "lab_technician":
        technician_dashboard()
    elif st.session_state.role.lower() == "admin":
        admin_dashboard()
    elif st.session_state.role == "SUPER_ADMIN":
        manage_labs()    
else:
    st.title("🔐 Welcome to MedLab System")
    login_tab, register_tab = st.tabs(["🔑 Login", "📝 Register"])

    def login_section():
        st.subheader("Login")
        name = st.text_input("Name", key="login_name")
        password = st.text_input("Password", type="password", key="login_password")
        lab_name = st.text_input("Lab Name", key="login_lab_name")

        if st.button("Login", key="login_btn"):
            if name and password:
                res = login_user(name, password, lab_name)

                if "access_token" in res and "user" in res:
                    st.session_state.token = res["access_token"]
                    st.session_state.user = res["user"]
                    st.session_state.role = res["user"]["role"]
                    st.session_state.full_name = res["user"]["full_name"]
                    st.success("✅ Login successful.")
                    st.rerun()
                else:
                    st.error("❌ Login failed. Please check credentials.")
            else:
                st.warning("Please fill in both fields.")



    def register_section():
        st.subheader("Register")

        full_name = st.text_input("Full Name", key="register_name")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        role = st.selectbox("Role", ["DOCTOR", "LAB_TECHNICIAN", "ADMIN"], key="register_role")

        # ✅ Get available labs
        labs_response = requests.get(f"{API_URL}/superadmin/labs")
        labs = labs_response.json() if labs_response.status_code == 200 else []

        lab_id = None
        if labs:
            lab_names = [f"{lab['name']} (ID: {lab['id']})" for lab in labs]
            selected_lab = st.selectbox("Select Laboratory", lab_names, key="register_lab")
            lab_id = next((lab['id'] for lab in labs if f"{lab['name']} (ID: {lab['id']})" == selected_lab), None)
        else:
            st.warning("⚠️ No laboratories available. Contact the Super Admin to add one.")

        if st.button("Register", key="register_btn"):
            if full_name and email and password and role and lab_id:
                res = register_user(full_name, email, password, role, lab_id)

                if res.status_code in (200, 201):
                    user_data = res.json()
                    st.success(f"✅ Registered successfully as {user_data['full_name']} ({user_data['role']})")
                elif res.status_code == 403 and "Only one admin" in res.text:
                    st.error("⚠️ Admin Already Registered. Not allowed to register as Admin.")
                else:
                    st.error(f"❌ Registration failed: {res.text}")
            else:
                st.warning("Please complete all fields and select a lab to register.")


    with login_tab:
        login_section()
    with register_tab:
        register_section()
