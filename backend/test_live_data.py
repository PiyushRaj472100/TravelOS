from app.services.live_data_service import LiveDataService


service = LiveDataService()


try:

    result = service.get_currency_rate(
        base_currency="INR",
        target_currency="EUR"
    )

    print("\n==============================")
    print("LIVE DATA SERVICE")
    print("==============================")

    print(result)

finally:

    service.close()