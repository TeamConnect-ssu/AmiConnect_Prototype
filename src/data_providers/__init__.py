"""Real data providers for weather and medication schedule."""
from src.data_providers.weather import get_weather_response
from src.data_providers.medication import get_medication_response

__all__ = ["get_weather_response", "get_medication_response"]
