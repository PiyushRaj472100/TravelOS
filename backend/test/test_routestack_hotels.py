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
# Authentication
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
# Main
# =================================================

print("=" * 60)
print("ROUTESTACK HOTEL SEARCH TEST")
print("=" * 60)


# =================================================
# Get Partner Token
# =================================================

token = get_partner_token()

print()
print("Partner token obtained successfully.")


# =================================================
# Headers
# =================================================

headers = {
    "Authorization": (
        f"Bearer {token}"
    ),
    "Content-Type": "application/json"
}


# =================================================
# Tokyo Destination
# =================================================

destination_id = "333465"

latitude = 35.630539

longitude = 139.439767


# =================================================
# Hotel Search Payload
# =================================================

payload = {

    "long": longitude,

    "lat": latitude,

    "rooms": [
        {
            "adults": 2,
            "children": 0,
            "childAges": []
        }
    ],

    "roomCount": 1,

    "checkOut": "2026-08-20",

    "checkIn": "2026-08-15",

    "destinationId": destination_id,

    "currency": "EUR",

    "destinationType": destination_id
}


# =================================================
# Send Hotel Search Request
# =================================================

print()
print("Searching hotels...")

print()
print("Payload:")
print(payload)


response = requests.post(
    f"{BASE_URL}/mcp/hotel/search-hotels",
    headers=headers,
    json=payload,
    timeout=60
)


# =================================================
# Response Status
# =================================================

print()
print("Status:")
print(response.status_code)


print()
print("Raw Response:")

print(
    response.text[:10000]
)


# =================================================
# Raise HTTP Errors
# =================================================

response.raise_for_status()


# =================================================
# Parse JSON
# =================================================

data = response.json()


print()
print("=" * 60)
print("HOTEL SEARCH SUCCESSFUL")
print("=" * 60)


# =================================================
# Main Result Object
# =================================================

result = data.get(
    "result",
    {}
)


# =================================================
# Correlation ID
# =================================================

print()
print("Correlation ID:")

print(
    result.get(
        "correlationId"
    )
)


# =================================================
# Search Token
# =================================================

print()
print("Token received:")

print(
    "YES"
    if result.get("token")
    else "NO"
)


# =================================================
# Currency
# =================================================

currency = result.get(
    "currency"
)


print()
print("Currency:")

print(currency)


# =================================================
# Hotel Results
# =================================================

hotels = result.get(
    "result",
    []
)


print()
print("Hotel result type:")

print(
    type(hotels)
)


# =================================================
# Validate Hotel Results
# =================================================

if isinstance(
    hotels,
    list
):

    print()
    print(
        f"Hotels returned: {len(hotels)}"
    )


    # =================================================
    # Display Hotels
    # =================================================

    for index, hotel in enumerate(
        hotels[:5],
        start=1
    ):

        print()
        print(
            "=" * 50
        )

        print(
            f"HOTEL {index}"
        )

        print(
            "=" * 50
        )


        # ---------------------------------------------
        # Basic Information
        # ---------------------------------------------

        print()

        print(
            "Name:",
            hotel.get(
                "name"
            )
        )

        print(
            "Provider:",
            hotel.get(
                "providerName"
            )
        )

        print(
            "Hotel ID:",
            hotel.get(
                "id"
            )
        )

        print(
            "Star Rating:",
            hotel.get(
                "starRating"
            )
        )


        # ---------------------------------------------
        # Price
        # ---------------------------------------------

        print()

        print(
            "Price:",
            hotel.get(
                "ourprice"
            )
        )

        print(
            "Published Rate:",
            hotel.get(
                "publishedRate"
            )
        )

        print(
            "Saving:",
            hotel.get(
                "saving"
            )
        )

        print(
            "Saving Ratio:",
            hotel.get(
                "savingratio"
            ),
            "%"
        )


        # ---------------------------------------------
        # Distance
        # ---------------------------------------------

        print()

        print(
            "Distance:",
            hotel.get(
                "distancekm"
            ),
            "km"
        )


        # ---------------------------------------------
        # Booking Information
        # ---------------------------------------------

        options = hotel.get(
            "options",
            {}
        )


        print()

        print(
            "Rate Type:",
            hotel.get(
                "ratetype"
            )
        )

        print(
            "Pay At Hotel:",
            hotel.get(
                "payAtHotel"
            )
        )

        print(
            "Refundable:",
            options.get(
                "refundable"
            )
        )

        print(
            "Free Cancellation:",
            options.get(
                "freeCancellation"
            )
        )

        print(
            "Free Breakfast:",
            options.get(
                "freeBreakfast"
            )
        )


        # ---------------------------------------------
        # Chain
        # ---------------------------------------------

        print()

        print(
            "Chain:",
            hotel.get(
                "chain"
            )
        )


        # ---------------------------------------------
        # Address
        # ---------------------------------------------

        contact = hotel.get(
            "contact",
            {}
        )

        address = contact.get(
            "address",
            {}
        )

        city = address.get(
            "city",
            {}
        )

        print()

        print(
            "Address:",
            address.get(
                "line1"
            )
        )

        print(
            "City:",
            city.get(
                "name"
            )
        )

        print(
            "Country:",
            address.get(
                "country",
                {}
            ).get(
                "name"
            )
        )


        # ---------------------------------------------
        # Main Amenities
        # ---------------------------------------------

        print()

        print(
            "Main Amenities:",
            hotel.get(
                "mainamenity",
                []
            )
        )


        # ---------------------------------------------
        # Facilities Count
        # ---------------------------------------------

        facilities = hotel.get(
            "facilities",
            []
        )

        print()

        print(
            "Facilities:",
            len(facilities)
        )


        # ---------------------------------------------
        # Hero Image
        # ---------------------------------------------

        print()

        print(
            "Hero Image:",
            hotel.get(
                "heroImage"
            )
        )


else:

    print()

    print(
        "Unexpected hotel result structure:"
    )

    print(
        hotels
    )


# =================================================
# Completion
# =================================================

print()

print("=" * 60)

print(
    "HOTEL TEST COMPLETED"
)

print("=" * 60)