import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time
import os
import json
import re

# ---------- CONFIG ----------
SHEET_NAME = "Coolify-Wudgres"

API_URL = "http://evo-v40s8cc8o8gw0kgswos4w0wc.72.62.197.26.sslip.io"
API_KEY = "QM6HxQI2oBX3gkwLu6qn8RSBFtWXvlMv"
INSTANCE = "wudgres"

OWNER_PHONE = "919844610001"

POLL_INTERVAL = 10
WAIT_LOG_INTERVAL = 120

MAX_RETRIES = 3
RETRY_DELAY = 5
# ----------------------------

def setup_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise Exception("GOOGLE_CREDENTIALS_JSON env variable not found")

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def format_phone(phone):
    if not phone:
        return None
    digits = re.sub(r"\D", "", str(phone))
    if not digits:
        return None
    if digits.startswith("91"):
        return digits
    if len(digits) == 10:
        return "91" + digits
    return digits

def send_whatsapp(phone, message, label="Contact"):
    clean_phone = format_phone(phone)
    if not clean_phone:
        print(f"⚠️ [{label}] Invalid or missing phone number")
        return False

    url = f"{API_URL}/message/sendText/{INSTANCE}"
    payload = {"number": clean_phone, "text": message}
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            res_data = response.json()
            if response.status_code == 201:
                print(f"✅ [{label}] Sent to {clean_phone}")
                return True
            if response.status_code == 400 and "exists" in str(res_data):
                print(f"❌ [{label}] {clean_phone} not on WhatsApp. Skipping.")
                return "INVALID"
        except Exception as e:
            print(f"⚠️ [{label}] Error: {e}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    return False

def run_automation():
    sheet = setup_google_sheets()
    headers = sheet.row_values(1)

    try:
        processed_col = headers.index("Processed") + 1
    except ValueError:
        print("❌ Error: 'Processed' column missing!")
        return

    last_wait_log_time = time.time()
    print("🚀 Wudgres System Live. Waiting for new leads...")

    while True:
        processed_any = False
        try:
            rows = sheet.get_all_records()

            for idx, row in enumerate(rows, start=2):
                if str(row.get("Processed")).strip().lower() == "true":
                    continue

                processed_any = True

                # Basic Info
                c_name = row.get("CustomerName", "Customer")
                c_phone = row.get("CustomerPhone")
                c_pin = row.get("CustomerPincode", "N/A")
                d_name = row.get("DealerName", "Assigned Dealer")
                d_phone = row.get("DealerPhone")
                d_addr = row.get("DealerAddress", "").strip()

                # [cite_start]NEW COLUMNS [cite: 1]
                req_type = row.get("you_are_looking_for_doors_for?", "N/A")
                door_interest = row.get("which_door_are_you_interested_in?", "N/A")
                door_qty = row.get("how_many_doors_do_you_require?", "N/A")
                timeline = row.get("when_do_you_plan_to_finalize_the_purchase?", "N/A")
                contact_pref = row.get("preferred_contact_method", "N/A")

                # Customer Message (Unchanged)
                customer_msg = (
                    f"Hi {c_name},\n"
                    f"Thanks for your interest in Wudgres.\n\n"
                    f"Your nearest Wudgres Display Center is:\n"
                    f"*{d_name}*\n"
                    f"📞 {d_phone}\n\n"
                    f"📌 Location Map:\n"
                    f"{d_addr}\n\n"
                    f"They’ll help you explore designs, finishes, and pricing in detail.\n\n"
                    f"Warm regards,\n"
                    f"Team Wudgres"
                )

                customer_status = send_whatsapp(c_phone, customer_msg, "Customer")
                time.sleep(2)

                # Dealer Message (Updated with new columns)
                dealer_msg = (
                    f"New Wudgres enquiry assigned to you.\n\n"
                    f"Customer details:\n"
                    f"Name: {c_name}\n"
                    f"Phone: {c_phone}\n"
                    f"Pincode: {c_pin}\n\n"
                    f"Requirement Details:\n"
                    f"- Purpose: {req_type}\n"
                    f"- Interested in: {door_interest}\n"
                    f"- Quantity: {door_qty}\n"
                    f"- Timeline: {timeline}\n"
                    f"- Preferred Contact: {contact_pref}\n\n"
                    f"Please connect with them at the earliest.\n\n"
                    f"- Wudgres"
                )

                dealer_status = send_whatsapp(d_phone, dealer_msg, "Dealer")
                time.sleep(2)

                # Owner Message (Updated with new columns)
                owner_msg = (
                    f"New Wudgres lead processed.\n\n"
                    f"Customer: {c_name}\n"
                    f"📞 {c_phone}\n"
                    f"📍 Pincode: {c_pin}\n\n"
                    f"Lead Details:\n"
                    f"- Purpose: {req_type}\n"
                    f"- Interest: {door_interest}\n"
                    f"- Qty: {door_qty}\n"
                    f"- Timeline: {timeline}\n\n"
                    f"Assigned Display Center:\n"
                    f"{d_name}\n"
                    f"📞 {d_phone}\n\n"
                    f"- Automated Lead System"
                )

                owner_status = send_whatsapp(OWNER_PHONE, owner_msg, "Owner")

                if (customer_status in [True, "INVALID"]) and dealer_status and owner_status:
                    sheet.update_cell(idx, processed_col, "TRUE")
                    print(f"✔️ Row {idx} processed.")
                else:
                    print(f"⏸️ Row {idx} failed internal alerts.")

        except Exception as e:
            print(f"⚠️ System error: {e}")
            time.sleep(30)

        if not processed_any:
            if time.time() - last_wait_log_time >= WAIT_LOG_INTERVAL:
                print(f"🕒 [{time.strftime('%H:%M:%S')}] waiting for a row")
                last_wait_log_time = time.time()
        else:
            last_wait_log_time = time.time()

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_automation()
