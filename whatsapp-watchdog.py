import gspread
import requests
import time
from oauth2client.service_account import ServiceAccountCredentials

# ---------- CONFIG ----------

SHEET_NAME = "Coolify-Wudgres"

API_URL = "http://evo-v40s8cc8o8gw0kgswos4w0wc.72.62.197.26.sslip.io"
API_KEY = "QM6HxQI2oBX3gkwLu6qn8RSBFtWXvlMv"
INSTANCE = "wudgres"

OWNER_PHONE = "918660694556"

POLL_INTERVAL = 10
WAIT_LOG_INTERVAL = 120

MAX_RETRIES = 3
RETRY_DELAY = 5

# ---------- GOOGLE CREDENTIALS ----------

SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "n8n-gmail-471507",
    "private_key_id": "7c7bd6eeef39d53cd64f9a8fe78bc3db2259f37a",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCgzhsxR8teVBIX\nBE3oNRwXuSYiUJzCrJE1aR75qLt4QWQU93p15rqDIJ+L2XWjh+WTzd0lUHb6S+K+\nKcdZjwcAXIxs616yavCrvKL0fdIZq01wEOGjiqlGJ+kuGoKguTcRp3f6Cu1YcpVD\nwqoS3/yw9+Kbm256eOEKSXiyxxIEI7d9dtfJI//7HpBTNSOuyiAuGcp9HxNsKXde\nuxdJxE82ZTBCuCGOFPyuakoHzhKVv0SVXamul1oINhRZuhwJae6MHgtfUd8u4srp\nNEPC3Beua76OiPY0INECy4CjfZktTZg23e/Ry1cgaei4+Z1qEUMqSVn9/umj5X7o\npLBOywJFAgMBAAECggEAEyZweRY0ezOWYuzVjVeT1KRtTO1eOdXcxihScsd8KfZZ\noaCWUier4xVVws0fNB4pQkikMz8pqCW051Io5jrBCfM7mvYN1UAkkMM6gdThGkL7\nCiNMh9Ip1gvHOoEYOOVN0FmqEVpPSTb+HS932x8XJAklUMQ6LDYskLHOwLWx6NGa\nrcHnBiFOkd1+1Cc54WscxJJOkXZJX714Z7s2Wd4Ppb5Ncxs0hoEjFHkl9km10iR6\nj6TKqQqtLF6RfDeomwq0kXmdSXr7EGpxavnM2IrGqOTLcp7R4Fr53aDXz5zq7ozO\n2Ebq9hGfhU4L7i10AE59rIntzoAacDszk+DbTBYXcQKBgQDXPqXboqQrs7hFX8vY\nYYVI1hoFN7pCx0iLa/4keyRqKr0qF2e0lngDp5+sZD7IogGypzl4S5Z/gsSQUigI\nKlylWyJ3I/rDt2T31i+OSjCGLPfzdszhNVcLMiBZUO3YK2roAQWhkMI4Jh8qVnVy\nqpeNb39zgkpD/XPFmfvkYjJzEQKBgQC/QKihjeJMToxHE1MN5PzvsS5qpH7bFxQq\n8XaUlcBXl2eY9nnCGjRHZD/F8dUiUUce4NqSAZU4Q4GkWFqHCzdAJhyPQE8YJBJA\nnUYR3hGtk85DLaL9XWwtZVJsBDfY1ogfDHupM8HAlpvibvfIc97VptvlgGQQ/LaY\nSF88US6z9QKBgDzl3qsrcuNib6pBFj1cKgeXe7kqMSqfk2jO3xKXPJBFE0wLXy36\nvG3cSRLPMew12eEf6uScDjJ5Xv+uHuFgiuHFzRSEO3iQNKLiGIZbeysbIfPiEslM\n/BmQzxI2EXTto8uMLnmtqSWVs4+Y8pXEqig7+YVGwZhG5zBrBpdxKPDhAoGAYyZq\nRhcAkv7FyrNCA5oLZ1g78B2Hhp3YXsr/5tgb900O8EYXqYFcSQa36S8Oh9QLQv7f\nUYJwkdKtiz4i8I/n/OHFPJ7iYmmQ7N6cTPcLwyk1ba5jKWcdhgtZR5aIPWo6953J\nHlcuw2FRP3q4CrvHcowmxDxjpErffuNGPEb6J2ECgYBWs+hMCCci4O4ixGbczxpy\nJ61zj8nMRqCk34uNXxQ0Y3E25JBhEbcvX4XRTvcJJEjGun9g+XOz+D3PH+YywEDK\nXvldviaR0cVOPE0+tCUfCc68JOsJs13mmxCOayTntlITwSrIGTtJy73FF5EZCsFw\nuK50KvjtPTJxRI/hdE+tKw==\n-----END PRIVATE KEY-----\n",
    "client_email": "excel-16@n8n-gmail-471507.iam.gserviceaccount.com",
    "client_id": "100161316256984292958",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/excel-16%40n8n-gmail-471507.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}

# ----------------------------


def setup_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        SERVICE_ACCOUNT_INFO, scope
    )

    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


def format_phone(phone):
    if not phone:
        return None

    clean = str(phone).replace("+", "").replace(" ", "").replace("-", "").strip()

    if not clean.startswith("91"):
        clean = "91" + clean

    return clean


def send_whatsapp(phone, message, label="Contact"):
    clean_phone = format_phone(phone)

    if not clean_phone:
        print(f"Missing phone for {label}")
        return False

    url = f"{API_URL}/message/sendText/{INSTANCE}"
    payload = {"number": clean_phone, "text": message}
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)

            if response.status_code == 201:
                print(f"Sent to {clean_phone}")
                return True

            if response.status_code == 400:
                return "INVALID"

        except Exception as e:
            print(f"Error sending message {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    return False


def run_automation():
    sheet = setup_google_sheets()
    headers = sheet.row_values(1)

    processed_col = headers.index("Processed") + 1

    print("Wudgres automation running")

    last_wait_log_time = time.time()

    while True:
        processed_any = False

        try:
            rows = sheet.get_all_records()

            for idx, row in enumerate(rows, start=2):
                if str(row.get("Processed")).lower() == "true":
                    continue

                processed_any = True

                c_name = row.get("CustomerName", "Customer")
                c_phone = row.get("CustomerPhone")
                c_pin = row.get("CustomerPincode", "N/A")

                d_name = row.get("DealerName", "Dealer")
                d_phone = row.get("DealerPhone")
                d_addr = row.get("DealerAddress", "")

                customer_msg = (
                    f"Hi {c_name}\n\n"
                    f"Your nearest Wudgres display center is\n"
                    f"{d_name}\n"
                    f"Phone {d_phone}\n\n"
                    f"Location\n{d_addr}\n\n"
                    f"Team Wudgres"
                )

                customer_status = send_whatsapp(c_phone, customer_msg, "Customer")
                time.sleep(2)

                dealer_msg = (
                    f"New Wudgres enquiry\n\n"
                    f"Name {c_name}\n"
                    f"Phone {c_phone}\n"
                    f"Pincode {c_pin}"
                )

                dealer_status = send_whatsapp(d_phone, dealer_msg, "Dealer")
                time.sleep(2)

                owner_msg = (
                    f"Lead processed\n\n" f"{c_name}\n" f"{c_phone}\n" f"{d_name}"
                )

                owner_status = send_whatsapp(OWNER_PHONE, owner_msg, "Owner")

                if customer_status and dealer_status and owner_status:
                    sheet.update_cell(idx, processed_col, "TRUE")
                    print(f"Row {idx} processed")

        except Exception as e:
            print(f"System error {e}")
            time.sleep(30)

        if not processed_any:
            if time.time() - last_wait_log_time >= WAIT_LOG_INTERVAL:
                print("Waiting for new rows")
                last_wait_log_time = time.time()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_automation()
