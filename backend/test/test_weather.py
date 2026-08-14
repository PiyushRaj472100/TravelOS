from app.services.weather_service import (
    WeatherService
)


weather_service = WeatherService()


print()
print("=" * 50)
print("Testing Weather Service")
print("=" * 50)


result = weather_service.get_current_weather(
    "Tokyo"
)


print()
print("Weather Result:")
print(result)


print()
print("=" * 50)
print("Test completed")
print("=" * 50)