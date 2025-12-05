import os
import httpx
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Weather Server")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# Get API key from environment
# 

@mcp.tool()
async def get_current_weather(city: str, units: str = "metric") -> str:
    """
    Get current weather/temperature for a city.
    
    Args:
        city: City name (e.g., 'London', 'New York', 'Tokyo')
        units: Temperature units - 'metric' for Celsius or 'imperial' for Fahrenheit
    
    Returns:
        Current weather information including temperature, conditions, humidity, etc.
    """
    
    if not WEATHER_API_KEY:
        return "Error: WEATHER_API_KEY environment variable not set"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.weatherapi.com/v1/current.json",
                params={
                    "q": city,
                    "key": WEATHER_API_KEY,
                    
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
                    # WeatherAPI always returns temp_c and temp_f
            temp = data["current"]["temp_c"] if units == "metric" else data["current"]["temp_f"]
            feels = data["current"]["feelslike_c"] if units == "metric" else data["current"]["feelslike_f"]

            temp_unit = "°C" if units == "metric" else "°F"
            speed_unit = "kph"  # WeatherAPI uses kph

            result = f"""Current Weather in {data['location']['name']}, {data['location']['country']}

        📍 Location: {data['location']['lat']}, {data['location']['lon']}
        🌡️  Temperature: {temp}{temp_unit}
        🤔 Feels Like: {feels}{temp_unit}
        ☁️  Condition: {data['current']['condition']['text']}
        💧 Humidity: {data['current']['humidity']}%
        🔽 Pressure: {data['current']['pressure_mb']} hPa
        💨 Wind Speed: {data['current']['wind_kph']} {speed_unit}
        ☁️  Cloudiness: {data['current']['cloud']}%
        👁️  Visibility: {data['current'].get('vis_km', 'N/A')} km
        """
            return result
            
        except httpx.HTTPStatusError as e:
            return f"HTTP Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error fetching weather: {str(e)}"


@mcp.tool()
async def get_forecast(city: str, days: int = 3, units: str = "metric") -> str:
    """Get weather forecast for multiple days (1–10)."""

    
    days = min(max(days, 1), 10)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.weatherapi.com/v1/forecast.json",
                params={"q": city, "days": days, "key": WEATHER_API_KEY},
                timeout=10.0,
            )
            data = response.json()

            available = len(data["forecast"]["forecastday"])

            result = f"🌦 Forecast for {city} (requested {days} days)\n"

            if available < days:
                result += f"\n⚠️ Only {available} days available — likely due to WeatherAPI Free Plan .\n"

            for day in data["forecast"]["forecastday"]:
                d = day["day"]
                result += f"""
            📅 {day['date']}
            🌡 Max: {d['maxtemp_c']}°C / {d['maxtemp_f']}°F
            🌡 Min: {d['mintemp_c']}°C / {d['mintemp_f']}°F
            🌤 Condition: {d['condition']['text']}
            🌧 Chance of rain: {d['daily_chance_of_rain']}%
            🌅 Sunrise: {day['astro']['sunrise']}
            🌇 Sunset: {day['astro']['sunset']}
            -------------------
        """

        return result

            
            
            
    except httpx.HTTPStatusError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error fetching forecast: {str(e)}"


@mcp.tool()
async def compare_weather(city1: str, city2: str, units: str = "metric") -> str:
    """
    Compare current weather between two cities.
    
    Args:
        city1: First city name
        city2: Second city name
        units: Temperature units - 'metric' or 'imperial'
    
    Returns:
        Side-by-side weather comparison
    """
    weather1 = await get_current_weather.fn(city1, units)
    weather2 = await get_current_weather.fn(city2, units)
    
    return f"""Weather Comparison
{'=' * 60}

{weather1}

{'=' * 60}

{weather2}
"""


if __name__ == "__main__":
    # Run the server
    mcp.run()