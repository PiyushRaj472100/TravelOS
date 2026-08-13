from pydantic import BaseModel


class AirportLocation(BaseModel):

    name: str

    code: str

    location_type: str


class AirportService:

    AIRPORTS = {

        # =================================================
        # Australia
        # =================================================

        "sydney": {
            "name": "Sydney",
            "code": "SYD",
            "type": "city"
        },

        "melbourne": {
            "name": "Melbourne",
            "code": "MEL",
            "type": "city"
        },

        "brisbane": {
            "name": "Brisbane",
            "code": "BNE",
            "type": "city"
        },

        "perth": {
            "name": "Perth",
            "code": "PER",
            "type": "city"
        },

        # =================================================
        # Austria
        # =================================================

        "vienna": {
            "name": "Vienna",
            "code": "VIE",
            "type": "city"
        },

        "salzburg": {
            "name": "Salzburg",
            "code": "SZG",
            "type": "city"
        },

        "innsbruck": {
            "name": "Innsbruck",
            "code": "INN",
            "type": "city"
        },

        # =================================================
        # Brazil
        # =================================================

        "sao paulo": {
            "name": "São Paulo",
            "code": "SAO",
            "type": "city"
        },

        "rio de janeiro": {
            "name": "Rio de Janeiro",
            "code": "RIO",
            "type": "city"
        },

        "brasilia": {
            "name": "Brasília",
            "code": "BSB",
            "type": "city"
        },

        # =================================================
        # Canada
        # =================================================

        "toronto": {
            "name": "Toronto",
            "code": "YTO",
            "type": "city"
        },

        "vancouver": {
            "name": "Vancouver",
            "code": "YVR",
            "type": "city"
        },

        "montreal": {
            "name": "Montreal",
            "code": "YMQ",
            "type": "city"
        },

        "ottawa": {
            "name": "Ottawa",
            "code": "YOW",
            "type": "city"
        },

        # =================================================
        # China
        # =================================================

        "beijing": {
            "name": "Beijing",
            "code": "BJS",
            "type": "city"
        },

        "shanghai": {
            "name": "Shanghai",
            "code": "SHA",
            "type": "city"
        },

        "guangzhou": {
            "name": "Guangzhou",
            "code": "CAN",
            "type": "city"
        },

        "shenzhen": {
            "name": "Shenzhen",
            "code": "SZX",
            "type": "city"
        },

        # =================================================
        # Egypt
        # =================================================

        "cairo": {
            "name": "Cairo",
            "code": "CAI",
            "type": "city"
        },

        "alexandria": {
            "name": "Alexandria",
            "code": "HBE",
            "type": "city"
        },

        "luxor": {
            "name": "Luxor",
            "code": "LXR",
            "type": "city"
        },

        # =================================================
        # France
        # =================================================

        "paris": {
            "name": "Paris",
            "code": "PAR",
            "type": "city"
        },

        "nice": {
            "name": "Nice",
            "code": "NCE",
            "type": "city"
        },

        "lyon": {
            "name": "Lyon",
            "code": "LYS",
            "type": "city"
        },

        "marseille": {
            "name": "Marseille",
            "code": "MRS",
            "type": "city"
        },

        # =================================================
        # Germany
        # =================================================

        "berlin": {
            "name": "Berlin",
            "code": "BER",
            "type": "city"
        },

        "frankfurt": {
            "name": "Frankfurt",
            "code": "FRA",
            "type": "city"
        },

        "munich": {
            "name": "Munich",
            "code": "MUC",
            "type": "city"
        },

        "hamburg": {
            "name": "Hamburg",
            "code": "HAM",
            "type": "city"
        },

        # =================================================
        # Greece
        # =================================================

        "athens": {
            "name": "Athens",
            "code": "ATH",
            "type": "city"
        },

        "thessaloniki": {
            "name": "Thessaloniki",
            "code": "SKG",
            "type": "city"
        },

        "heraklion": {
            "name": "Heraklion",
            "code": "HER",
            "type": "city"
        },

        # =================================================
        # India
        # =================================================

        "delhi": {
            "name": "Delhi",
            "code": "DEL",
            "type": "city"
        },

        "new delhi": {
            "name": "New Delhi",
            "code": "DEL",
            "type": "city"
        },

        "mumbai": {
            "name": "Mumbai",
            "code": "BOM",
            "type": "city"
        },

        "bangalore": {
            "name": "Bangalore",
            "code": "BLR",
            "type": "city"
        },

        "bengaluru": {
            "name": "Bengaluru",
            "code": "BLR",
            "type": "city"
        },

        "chennai": {
            "name": "Chennai",
            "code": "MAA",
            "type": "city"
        },

        "kolkata": {
            "name": "Kolkata",
            "code": "CCU",
            "type": "city"
        },

        "hyderabad": {
            "name": "Hyderabad",
            "code": "HYD",
            "type": "city"
        },

        "ahmedabad": {
            "name": "Ahmedabad",
            "code": "AMD",
            "type": "city"
        },

        "pune": {
            "name": "Pune",
            "code": "PNQ",
            "type": "city"
        },

        "goa": {
            "name": "Goa",
            "code": "GOI",
            "type": "city"
        },

        "kochi": {
            "name": "Kochi",
            "code": "COK",
            "type": "city"
        },

        "jaipur": {
            "name": "Jaipur",
            "code": "JAI",
            "type": "city"
        },

        "lucknow": {
            "name": "Lucknow",
            "code": "LKO",
            "type": "city"
        },

        "varanasi": {
            "name": "Varanasi",
            "code": "VNS",
            "type": "city"
        },

        "amritsar": {
            "name": "Amritsar",
            "code": "ATQ",
            "type": "city"
        },

        # =================================================
        # Indonesia
        # =================================================

        "jakarta": {
            "name": "Jakarta",
            "code": "JKT",
            "type": "city"
        },

        "bali": {
            "name": "Bali",
            "code": "DPS",
            "type": "city"
        },

        "denpasar": {
            "name": "Denpasar",
            "code": "DPS",
            "type": "city"
        },

        "surabaya": {
            "name": "Surabaya",
            "code": "SUB",
            "type": "city"
        },

        "yogyakarta": {
            "name": "Yogyakarta",
            "code": "YIA",
            "type": "city"
        },

        # =================================================
        # Italy
        # =================================================

        "rome": {
            "name": "Rome",
            "code": "ROM",
            "type": "city"
        },

        "milan": {
            "name": "Milan",
            "code": "MIL",
            "type": "city"
        },

        "venice": {
            "name": "Venice",
            "code": "VCE",
            "type": "city"
        },

        "florence": {
            "name": "Florence",
            "code": "FLR",
            "type": "city"
        },

        "naples": {
            "name": "Naples",
            "code": "NAP",
            "type": "city"
        },

        # =================================================
        # Japan
        # =================================================

        "tokyo": {
            "name": "Tokyo",
            "code": "TYO",
            "type": "city"
        },

        "osaka": {
            "name": "Osaka",
            "code": "OSA",
            "type": "city"
        },

        "kyoto": {
            "name": "Kyoto",
            "code": "KIX",
            "type": "airport"
        },

        "nagoya": {
            "name": "Nagoya",
            "code": "NGO",
            "type": "city"
        },

        "sapporo": {
            "name": "Sapporo",
            "code": "CTS",
            "type": "city"
        },

        "fukuoka": {
            "name": "Fukuoka",
            "code": "FUK",
            "type": "city"
        },

        # =================================================
        # Malaysia
        # =================================================

        "kuala lumpur": {
            "name": "Kuala Lumpur",
            "code": "KUL",
            "type": "city"
        },

        "penang": {
            "name": "Penang",
            "code": "PEN",
            "type": "city"
        },

        "langkawi": {
            "name": "Langkawi",
            "code": "LGK",
            "type": "city"
        },

        "johor bahru": {
            "name": "Johor Bahru",
            "code": "JHB",
            "type": "city"
        },

        # =================================================
        # Mexico
        # =================================================

        "mexico city": {
            "name": "Mexico City",
            "code": "MEX",
            "type": "city"
        },

        "cancun": {
            "name": "Cancun",
            "code": "CUN",
            "type": "city"
        },

        "guadalajara": {
            "name": "Guadalajara",
            "code": "GDL",
            "type": "city"
        },

        "monterrey": {
            "name": "Monterrey",
            "code": "MTY",
            "type": "city"
        },

        # =================================================
        # Morocco
        # =================================================

        "casablanca": {
            "name": "Casablanca",
            "code": "CMN",
            "type": "city"
        },

        "marrakech": {
            "name": "Marrakech",
            "code": "RAK",
            "type": "city"
        },

        "rabat": {
            "name": "Rabat",
            "code": "RBA",
            "type": "city"
        },

        "fes": {
            "name": "Fes",
            "code": "FEZ",
            "type": "city"
        },

        # =================================================
        # Netherlands
        # =================================================

        "amsterdam": {
            "name": "Amsterdam",
            "code": "AMS",
            "type": "city"
        },

        "rotterdam": {
            "name": "Rotterdam",
            "code": "RTM",
            "type": "city"
        },

        "eindhoven": {
            "name": "Eindhoven",
            "code": "EIN",
            "type": "city"
        },

        # =================================================
        # New Zealand
        # =================================================

        "auckland": {
            "name": "Auckland",
            "code": "AKL",
            "type": "city"
        },

        "wellington": {
            "name": "Wellington",
            "code": "WLG",
            "type": "city"
        },

        "christchurch": {
            "name": "Christchurch",
            "code": "CHC",
            "type": "city"
        },

        "queenstown": {
            "name": "Queenstown",
            "code": "ZQN",
            "type": "city"
        },

        # =================================================
        # Portugal
        # =================================================

        "lisbon": {
            "name": "Lisbon",
            "code": "LIS",
            "type": "city"
        },

        "porto": {
            "name": "Porto",
            "code": "OPO",
            "type": "city"
        },

        "faro": {
            "name": "Faro",
            "code": "FAO",
            "type": "city"
        },

        # =================================================
        # Singapore
        # =================================================

        "singapore": {
            "name": "Singapore",
            "code": "SIN",
            "type": "city"
        },

        # =================================================
        # South Africa
        # =================================================

        "johannesburg": {
            "name": "Johannesburg",
            "code": "JNB",
            "type": "city"
        },

        "cape town": {
            "name": "Cape Town",
            "code": "CPT",
            "type": "city"
        },

        "durban": {
            "name": "Durban",
            "code": "DUR",
            "type": "city"
        },

        # =================================================
        # South Korea
        # =================================================

        "seoul": {
            "name": "Seoul",
            "code": "SEL",
            "type": "city"
        },

        "busan": {
            "name": "Busan",
            "code": "PUS",
            "type": "city"
        },

        "jeju": {
            "name": "Jeju",
            "code": "CJU",
            "type": "city"
        },

        # =================================================
        # Spain
        # =================================================

        "madrid": {
            "name": "Madrid",
            "code": "MAD",
            "type": "city"
        },

        "barcelona": {
            "name": "Barcelona",
            "code": "BCN",
            "type": "city"
        },

        "seville": {
            "name": "Seville",
            "code": "SVQ",
            "type": "city"
        },

        "valencia": {
            "name": "Valencia",
            "code": "VLC",
            "type": "city"
        },

        "malaga": {
            "name": "Malaga",
            "code": "AGP",
            "type": "city"
        },

        # =================================================
        # Switzerland
        # =================================================

        "zurich": {
            "name": "Zurich",
            "code": "ZRH",
            "type": "city"
        },

        "geneva": {
            "name": "Geneva",
            "code": "GVA",
            "type": "city"
        },

        "basel": {
            "name": "Basel",
            "code": "BSL",
            "type": "city"
        },

        # =================================================
        # Thailand
        # =================================================

        "bangkok": {
            "name": "Bangkok",
            "code": "BKK",
            "type": "city"
        },

        "phuket": {
            "name": "Phuket",
            "code": "HKT",
            "type": "city"
        },

        "chiang mai": {
            "name": "Chiang Mai",
            "code": "CNX",
            "type": "city"
        },

        "krabi": {
            "name": "Krabi",
            "code": "KBV",
            "type": "city"
        },

        # =================================================
        # Turkey
        # =================================================

        "istanbul": {
            "name": "Istanbul",
            "code": "IST",
            "type": "city"
        },

        "ankara": {
            "name": "Ankara",
            "code": "ESB",
            "type": "city"
        },

        "antalya": {
            "name": "Antalya",
            "code": "AYT",
            "type": "city"
        },

        "izmir": {
            "name": "Izmir",
            "code": "ADB",
            "type": "city"
        },

        # =================================================
        # UAE
        # =================================================

        "dubai": {
            "name": "Dubai",
            "code": "DXB",
            "type": "city"
        },

        "abu dhabi": {
            "name": "Abu Dhabi",
            "code": "AUH",
            "type": "city"
        },

        "sharjah": {
            "name": "Sharjah",
            "code": "SHJ",
            "type": "city"
        },

        # =================================================
        # United Kingdom
        # =================================================

        "london": {
            "name": "London",
            "code": "LON",
            "type": "city"
        },

        "heathrow": {
            "name": "London Heathrow",
            "code": "LHR",
            "type": "airport"
        },

        "gatwick": {
            "name": "London Gatwick",
            "code": "LGW",
            "type": "airport"
        },

        "manchester": {
            "name": "Manchester",
            "code": "MAN",
            "type": "city"
        },

        "edinburgh": {
            "name": "Edinburgh",
            "code": "EDI",
            "type": "city"
        },

        "birmingham": {
            "name": "Birmingham",
            "code": "BHX",
            "type": "city"
        },

        "glasgow": {
            "name": "Glasgow",
            "code": "GLA",
            "type": "city"
        },

        # =================================================
        # United States
        # =================================================

        "new york": {
            "name": "New York",
            "code": "NYC",
            "type": "city"
        },

        "new york city": {
            "name": "New York",
            "code": "NYC",
            "type": "city"
        },

        "los angeles": {
            "name": "Los Angeles",
            "code": "LAX",
            "type": "city"
        },

        "san francisco": {
            "name": "San Francisco",
            "code": "SFO",
            "type": "city"
        },

        "chicago": {
            "name": "Chicago",
            "code": "CHI",
            "type": "city"
        },

        "miami": {
            "name": "Miami",
            "code": "MIA",
            "type": "city"
        },

        "las vegas": {
            "name": "Las Vegas",
            "code": "LAS",
            "type": "city"
        },

        "boston": {
            "name": "Boston",
            "code": "BOS",
            "type": "city"
        },

        "seattle": {
            "name": "Seattle",
            "code": "SEA",
            "type": "city"
        },

        "houston": {
            "name": "Houston",
            "code": "HOU",
            "type": "city"
        },

        # =================================================
        # Vietnam
        # =================================================

        "hanoi": {
            "name": "Hanoi",
            "code": "HAN",
            "type": "city"
        },

        "ho chi minh city": {
            "name": "Ho Chi Minh City",
            "code": "SGN",
            "type": "city"
        },

        "saigon": {
            "name": "Ho Chi Minh City",
            "code": "SGN",
            "type": "city"
        },

        "da nang": {
            "name": "Da Nang",
            "code": "DAD",
            "type": "city"
        },

        "phu quoc": {
            "name": "Phu Quoc",
            "code": "PQC",
            "type": "city"
        }
    }


    @classmethod
    def resolve(
        cls,
        location: str
    ) -> AirportLocation:

        if not location:
            raise ValueError(
                "Airport or city is required."
            )

        normalized = (
            location
            .strip()
            .lower()
        )

        # ---------------------------------------------
        # Already an IATA code
        # ---------------------------------------------

        if (
            len(normalized) == 3
            and normalized.isalpha()
        ):

            return AirportLocation(
                name=location.upper(),
                code=location.upper(),
                location_type="airport_or_city_code"
            )

        # ---------------------------------------------
        # Known location
        # ---------------------------------------------

        data = cls.AIRPORTS.get(
            normalized
        )

        if data:

            return AirportLocation(
                name=data["name"],
                code=data["code"],
                location_type=data["type"]
            )

        # ---------------------------------------------
        # Unknown location
        # ---------------------------------------------

        raise ValueError(
            f"Could not resolve '{location}' "
            f"to a supported airport or city."
        )