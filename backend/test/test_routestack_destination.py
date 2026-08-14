import os
import time
import hmac
import hashlib
import base64
import secrets

import requests
from dotenv import load_dotenv


load_dotenv()


API_KEY = os.getenv(
    "ROUTESTACK_API_KEY"
)

API_SECRET = os.getenv(
    "ROUTESTACK_API_SECRET"
)

BASE_URL = os.getenv(
    "ROUTESTACK_BASE_URL",
    "https://evolvemcp.routestack.ai"
)


# =================================================
# Get Partner Token
# =================================================

def get_partner_token():

    timestamp = int(
        time.time()
    )

    nonce = secrets.token_urlsafe(
        24
    )

    message = (
        f"{API_KEY}:{timestamp}:{nonce}"
    )

    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()

    hmac_signature = (
        base64.urlsafe_b64encode(
            signature
        )
        .decode("utf-8")
        .rstrip("=")
    )

    response = requests.post(
        f"{BASE_URL}/mcp/auth/partner-token",
        json={
            "apiKey": API_KEY,
            "timestamp": timestamp,
            "nonce": nonce,
            "hmac": hmac_signature
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()["token"]


# =================================================
# Main Test
# =================================================

print("=" * 60)
print("ROUTESTACK DESTINATION SEARCH TEST")
print("=" * 60)


# -------------------------------------------------
# Authentication
# -------------------------------------------------

token = get_partner_token()

print()
print("Partner token obtained successfully.")


# -------------------------------------------------
# Headers
# -------------------------------------------------

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}


# -------------------------------------------------
# Destination Search
# -------------------------------------------------

payload = {
    "query": "Tokyo",
    "type": "DESTINATION"
}


print()
print("Searching destination: Tokyo")


response = requests.post(
    f"{BASE_URL}/mcp/hotel/search-destinations",
    headers=headers,
    json=payload,
    timeout=30
)


print()
print("Status:")
print(response.status_code)


print()
print("Raw Response:")
print(response.text)


# -------------------------------------------------
# Error handling
# -------------------------------------------------

response.raise_for_status()


# -------------------------------------------------
# JSON
# -------------------------------------------------

data = response.json()


print()
print("Parsed Response:")
print(data)


# -------------------------------------------------
# Extract results
# -------------------------------------------------

results = (
    data
    .get("result", [])
)


print()
print("=" * 60)
print("DESTINATION RESULTS")
print("=" * 60)


for result in results:

    print()

    print(
        "Name:",
        result.get("fullName")
    )

    print(
        "Type:",
        result.get("type")
    )

    print(
        "Country:",
        result.get("country")
    )

    print(
        "ID:",
        result.get("id")
    )

    coordinates = (
        result.get(
            "coordinates",
            {}
        )
    )

    print(
        "Latitude:",
        coordinates.get("lat")
    )

    print(
        "Longitude:",
        coordinates.get("long")
    )


print()
print("=" * 60)
print("DESTINATION SEARCH TEST COMPLETED")
print("=" * 60)