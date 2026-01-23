import gspread
from google.oauth2.service_account import Credentials
import json
import os
import base64
import requests
import time

# ---------- CONFIG ----------
# Pulling configurations from Environment Variables for security
SHEET_NAME = os.getenv("SHEET_NAME", "Coolify-Wudgres")
API_URL = os.getenv("API_URL", "http://evo-v40s8cc8o8gw0kgswos4w0wc.72.62.197.26.sslip.io")
API_KEY = os.getenv("API_KEY", "QM6HxQI2oBX3gkwLu6qn8RSBFtWXvlMv")
INSTANCE = os.getenv("INSTANCE", "wudgres")
OWNER_PHONE = os.getenv("OWNER_PHONE", "918660694556")

POLL_INTERVAL = 10
WAIT_LOG_INTERVAL = 120
MAX_RETRIES = 3
RETRY_DELAY = 5
# ----------------------------

def setup_google_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # 1. Get the env variable and strip any accidental whitespace/quotes
    raw_b64 = os.getenv("GOOGLE_CREDENTIALS_BASE64", "").strip().strip('"').strip("'")
    
    if not raw_b64:
        raise RuntimeError("❌ GOOGLE_CREDENTIALS_BASE64 is empty or not set in Coolify.")

    try:
        # 2. Decode and parse
        creds_json = base64.b64decode(raw_b64).decode("utf-8")
        creds_dict = json.loads(creds_json)
        
        # 3. Initialize credentials
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # 4. Attempt to open the sheet immediately to test the connection
        opened_sheet = client.open(SHEET_NAME).sheet1
        return opened_sheet
        
    except base64.binascii.Error:
        raise RuntimeError("❌ Base64 decoding failed. The string in Coolify might be truncated.")
    except json.JSONDecodeError:
        raise RuntimeError("❌ JSON parsing failed. The decoded string is not valid JSON.")
    except Exception as e:
        # This will catch the 'invalid_grant' and give more context
        raise RuntimeError(f"❌ Google Auth Error: {e}")

def format_phone(phone):
    """Cleans and ensures 91 prefix for Indian numbers."""
    if not phone:
        return None
    clean = str(phone).replace("+", "").replace(" ", "").replace("-", "").strip()
    if not clean.startswith("91"):
        clean = "91" + clean
    return clean

def send_whatsapp(phone, message, label="Contact"):
    clean_phone = format_phone(phone)
    if not clean_phone:
        print(f"⚠️ [{label}] Missing phone number")
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
    print(f"🚀 Wudgres System Starting...")
    sheet = setup_google_sheets()
    
    last_wait_log_time = time.time()
    print(f"✅ Connection Established. Monitoring '{SHEET_NAME}'...")

    while True:
        processed_any = False
        try:
            # Refresh headers in case the sheet changed
            headers = sheet.row_values(1)
            try:
                processed_col = headers.index("Processed") + 1
            except ValueError:
                print("❌ Error: 'Processed' column missing!")
                time.sleep(60)
                continue

            rows = sheet.get_all_records()

            for idx, row in enumerate(rows, start=2):
                if str(row.get("Processed")).strip().lower() == "true":
                    continue

                processed_any = True

                # Data Mapping
                c_name = row.get("CustomerName", "Customer")
                c_phone = row.get("CustomerPhone")
                c_pin = row.get("CustomerPincode", "N/A")
                d_name = row.get("DealerName", "Assigned Dealer")
                d_phone = row.get("DealerPhone")
                d_addr = row.get("DealerAddress", "").strip()

                # --- 1. Customer Message ---
                customer_msg = (
                    f"Hi {c_name},\n"
                    f"Thanks for your interest in Wudgres.\n\n"
                    f"Your nearest Wudgres Display Center is:\n"
                    f"       *{d_name}*\n"
                    f"📞 {d_phone}\n\n"
                    f"📌 Location Map:\n"
                    f"{d_addr}\n\n"
                    f"They’ll help you explore designs and pricing in detail.\n"
                    f"Warm regards,\nTeam Wudgres"
                )
                customer_status = send_whatsapp(c_phone, customer_msg, "Customer")
                time.sleep(2)

                # --- 2. Dealer Notification ---
                dealer_msg = (
                    f"New Wudgres enquiry assigned to you.\n\n"
                    f"Customer: {c_name}\n"
                    f"Phone: {c_phone}\n"
                    f"Pincode: {c_pin}\n\n"
                    f"Please connect with them at the earliest."
                )
                dealer_status = send_whatsapp(d_phone, dealer_msg, "Dealer")
                time.sleep(2)

                # --- 3. Owner Visibility ---
                owner_msg = f"New Lead: {c_name} ({c_phone}) assigned to {d_name}."
                owner_status = send_whatsapp(OWNER_PHONE, owner_msg, "Owner")

                if (customer_status in [True, "INVALID"]) and dealer_status and owner_status:
                    sheet.update_cell(idx, processed_col, "TRUE")
                    print(f"✔️ Row {idx} processed successfully.")
                else:
                    print(f"⏸️ Row {idx} failed one or more alerts.")

        except Exception as e:
            print(f"⚠️ System error: {e}")
            time.sleep(30)

        if not processed_any:
            if time.time() - last_wait_log_time >= WAIT_LOG_INTERVAL:
                print(f"🕒 [{time.strftime('%H:%M:%S')}] Waiting for new rows...")
                last_wait_log_time = time.time()
        else:
            last_wait_log_time = time.time()

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_automation()