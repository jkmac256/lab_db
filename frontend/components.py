# frontend/components.py

import streamlit as st
from utils import get_equipment, search_equipment, update_equipment, add_equipment
import datetime
import requests

API_URL = "https://lab-db-i793.onrender.com"

def auth_header():
    token = st.session_state.get("token", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def display_equipment_list(token, lab_id=None, can_edit=False):
    query = st.text_input("Search Equipment")

    # If you have a search API that accepts lab_id too:
    if query:
        results = search_equipment(token, query, lab_id=lab_id)
    else:
        results = get_equipment(token, lab_id=lab_id)

    if results:
        for item in results:
            name = item.get("name", "Unnamed")
            equipment_id = item.get("id")
            desc = item.get("description", "-")
            eq_type = item.get("type", "-")
            available = item.get("is_available", False)
            added_by = item.get("added_by", {}).get("full_name", "Unknown")
            last_serviced = item.get("last_serviced")

            if last_serviced:
                serviced_date = datetime.date.fromisoformat(last_serviced[:10])
            else:
                serviced_date = datetime.date.today()

            with st.expander(f"🔧 {name}"):
                st.markdown(f"**🧾 Description:** {desc}")
                st.markdown(f"**🧪 Type:** `{eq_type}`")
                st.markdown(f"**👤 Added by:** `{added_by}`")
                st.markdown(f"**🛠️ Last Serviced:** `{last_serviced or 'N/A'}`")
                st.markdown(f"**✅ Available:** `{available}`")

                if st.session_state.role in ["LAB_TECHNICIAN", "ADMIN"] and can_edit:
                    with st.form(key=f"edit_form_{equipment_id}"):
                        new_name = st.text_input("Name", value=name, key=f"edit_name_{equipment_id}")
                        new_type = st.text_input("Type", value=eq_type, key=f"edit_type_{equipment_id}")
                        new_desc = st.text_area("Description", value=desc, key=f"edit_desc_{equipment_id}")
                        new_avail = st.selectbox("Availability", [True, False], index=0 if available else 1, key=f"edit_avail_{equipment_id}")
                        new_serviced = st.date_input("Last Serviced", value=serviced_date, key=f"edit_serviced_{equipment_id}")

                        update_submitted = st.form_submit_button("💾 Save Changes")
                        if update_submitted:
                            update_payload = {
                                "name": new_name,
                                "type": new_type,
                                "description": new_desc,
                                "is_available": new_avail,
                                "last_serviced": new_serviced.isoformat(),
                            }
                            res = update_equipment(token, equipment_id, update_payload)
                            if res.status_code == 200:
                                st.success("✅ Equipment updated.")
                                st.experimental_rerun()
                            else:
                                st.error(f"❌ Update failed: {res.text}")

                    with st.form(key=f"delete_form_{equipment_id}"):
                        confirm = st.radio(
                            f"Are you sure you want to delete '{name}'?",
                            ["No", "Yes"],
                            key=f"confirm_{equipment_id}"
                        )
                        submitted = st.form_submit_button(f"🗑️ Confirm Delete '{name}'")
                        if submitted and confirm == "Yes":
                            delete_url = f"{API_URL}/equipment/{equipment_id}"
                            res = requests.delete(delete_url, headers=auth_header())
                            if res.status_code == 200:
                                st.success("✅ Deleted successfully.")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete: {res.text}")
    else:
        st.info("📭 No equipment found.")
