import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# --- CONFIGURATION ---
POSTCODES = [p.strip() for p in os.environ["POSTCODES"].split(",")]  # comma-separated, set as a secret
PART_NUMBERS = ["MK2E4QN/A", "MK2D4QN/A"]

# Email settings
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
SENDER_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]  # Gmail App Password, set as a secret
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SENDER_EMAIL)

FULFILLMENT_URL = "https://www.apple.com/uk/shop/pickup-message-recommendations"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}

def send_email_alert(part_number, available):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"🚨 iPhone Duo {part_number} IN STOCK at {len(available)} store(s)!"

        lines = "\n".join(f"- {name}: {details}" for name, details in available)
        body = f"Good news! The iPhone Duo ({part_number}) is available for pickup.\n\n{lines}\n\nGo to Apple UK Store immediately to secure it!"
        msg.attach(MIMEText(body, "plain"))

        # Connecting to Gmail SMTP server (change if using Outlook/Yahoo)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Alert email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_stock(postcode, part_number):
    params = {
        "mts.0": "regular",
        "parts.0": part_number,
        "product": part_number,
        "location": postcode,
    }
    
    try:
        response = requests.get(FULFILLMENT_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        stores = data.get("body", {}).get("PickupMessage", {}).get("stores", [])
        
        available = []
        for store in stores:
            store_name = store.get("storeName")
            parts_availability = store.get("partsAvailability", {}).get(part_number, {})
            pickup_display = parts_availability.get("pickupDisplay")
            pickup_search_quote = parts_availability.get("pickupSearchQuote", "")
            
            if pickup_display == "available":
                print(f"[+] {part_number} STOCK AVAILABLE at {store_name}!")
                available.append((store_name, pickup_search_quote))

        if available:
            send_email_alert(part_number, available)

    except Exception as e:
        print(f"[!] Error checking stock for {part_number} near {postcode}: {e}")

if __name__ == "__main__":
    for postcode in POSTCODES:
        for part_number in PART_NUMBERS:
            check_stock(postcode, part_number)