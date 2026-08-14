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


if not API_KEY:
    raise ValueError(
        "ROUTESTACK_API_KEY is not configured."
    )


if not API_SECRET:
    raise ValueError(
        "ROUTESTACK_API_SECRET is not configured."
    )


# =================================================
# Generate authentication values
# =================================================

timestamp = int(
    time.time()
)

nonce = secrets.token_urlsafe(
    24
)


# =================================================
# Create HMAC
# =================================================

message = (
    f"{API_KEY}:{timestamp}:{nonce}"
)

signature = hmac.new(
    API_SECRET.encode("utf-8"),
    message.encode("utf-8"),
    hashlib.sha256
).digest()


hmac_signature = (
    base64.urlsafe_b64encode(signature)
    .decode("utf-8")
    .rstrip("=")
)


# =================================================
# Request partner token
# =================================================

payload = {
    "apiKey": API_KEY,
    "timestamp": timestamp,
    "nonce": nonce,
    "hmac": hmac_signature
}


url = (
    f"{BASE_URL}/mcp/auth/partner-token"
)


print("=" * 60)
print("ROUTESTACK AUTHENTICATION TEST")
print("=" * 60)

print()
print("Endpoint:")
print(url)

print()
print("Requesting partner token...")


response = requests.post(
    url,
    json=payload,
    timeout=30
)


print()
print("Status:")
print(response.status_code)


print()
print("Response:")

try:

    data = response.json()

    # Never print the actual token
    if "token" in data:
        data["token"] = "***TOKEN_RECEIVED***"

    print(data)

except ValueError:

    print(response.text)


# =================================================
# Result
# =================================================

if response.ok:

    print()
    print("=" * 60)
    print("AUTHENTICATION SUCCESSFUL")
    print("=" * 60)

else:

    print()
    print("=" * 60)
    print("AUTHENTICATION FAILED")
    print("=" * 60)

    response.raise_for_status()