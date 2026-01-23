import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time

# ---------- CONFIG ----------
SHEET_NAME = "Coolify-Wudgres"
JSON_FILE = "credentials.json"

API_URL = "http://evo-v40s8cc8o8gw0kgswos4w0wc.72.62.197.26.sslip.io"
API_KEY = "QM6HxQI2oBX3gkwLu6qn8RSBFtWXvlMv"
INSTANCE = "wudgres"

OWNER_PHONE = "918660694556"

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
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


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
    sheet = setup_google_sheets()
    headers = sheet.row_values(1)

    try:
        processed_col = headers.index("Processed") + 1
    except ValueError:
        print("❌ Error: 'Processed' column missing!")
        return

    last_wait_log_time = time.time()
    print(f"🚀 Wudgres System Live. Links will be active if they start with https://")

    while True:
        processed_any = False
        try:
            rows = sheet.get_all_records()

            for idx, row in enumerate(rows, start=2):
                if str(row.get("Processed")).strip().lower() == "true":
                    continue

                processed_any = True

                # Mapping
                c_name = row.get("CustomerName", "Customer")
                c_phone = row.get("CustomerPhone")
                c_pin = row.get("CustomerPincode", "N/A")
                d_name = row.get("DealerName", "Assigned Dealer")
                d_phone = row.get("DealerPhone")
                d_addr = row.get("DealerAddress", "").strip()  # This should be a URL

                # --- 1. Customer Message (With Clickable Link) ---

                customer_msg = (
                    f"Hi {c_name},\n"
                    f"Thanks for your interest in Wudgres.\n\n"
                    f"Your nearest Wudgres Display Center is:\n"
                    f"       *{d_name}*\n"
                    f"📞 {d_phone}\n\n"
                    f"📌 Location Map:\n" # Move link to a new line for better recognition
                    f"{d_addr}\n\n"
                    f"They’ll help you explore designs, finishes, and pricing in detail.\n"
                    f"Feel free to reach out or walk in at your convenience.\n\n"
                    f"Warm regards,\n"
                    f"Team Wudgres"
                )

                customer_status = send_whatsapp(c_phone, customer_msg, "Customer")
                time.sleep(2)

                # --- 2. Dealer Notification ---
                dealer_msg = (
                    f"New Wudgres enquiry assigned to you.\n\n"
                    f"Customer details:\n"
                    f"Name: {c_name}\n"
                    f"Phone: {c_phone}\n"
                    f"Pincode: {c_pin}\n\n"
                    f"The customer has been informed about your display center.\n"
                    f"Please connect with them at the earliest.\n\n"
                    f"– Wudgres"
                )
                dealer_status = send_whatsapp(d_phone, dealer_msg, "Dealer")
                time.sleep(2)

                # --- 3. Owner Visibility ---
                owner_msg = (
                    f"New Wudgres lead processed.\n\n"
                    f"Customer: {c_name}\n"
                    f"📞 {c_phone}\n"
                    f"📍 Pincode: {c_pin}\n\n"
                    f"Assigned Display Center:\n"
                    f"{d_name}\n"
                    f"📞 {d_phone}\n\n"
                    f"Status: Customer and dealer notified successfully.\n\n"
                    f"– Automated Lead System"
                )
                owner_status = send_whatsapp(OWNER_PHONE, owner_msg, "Owner")

                if (
                    (customer_status in [True, "INVALID"])
                    and dealer_status
                    and owner_status
                ):
                    sheet.update_cell(idx, processed_col, "TRUE")
                    print(f"✔️ Row {idx} Processed successfully.")
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
