import streamlit as st
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
import requests

llm = ChatOllama(model="qwen3:4b")

def get_coordinates(city: str):
    """
    Get latitude and longitude for a city.
    Returns (lat, lon) or None.
    """

    geo_url = (
        f"https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}&count=1"
    )

    response = requests.get(geo_url, timeout=10)

    if response.status_code != 200:
        return None

    data = response.json()

    if "results" not in data:
        return None

    lat = data["results"][0]["latitude"]
    lon = data["results"][0]["longitude"]

    return lat, lon


@tool
def get_weather(city: str) -> str:
    """Get current weather information."""

    try:
        coordinates = get_coordinates(city)

        if coordinates is None:
            return f"Could not find city: {city}"

        lat, lon = coordinates

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lon}"
            f"&current_weather=true"
        )

        response = requests.get(weather_url, timeout=10)

        if response.status_code != 200:
            return "Weather service is unavailable."

        data = response.json()

        if "current_weather" not in data:
            return "Weather data not available."

        current = data["current_weather"]

        return (
            f"Current Weather in {city}\n\n"
            f"Temperature: {current['temperature']}°C\n"
            f"Wind Speed: {current['windspeed']} km/h"
        )

    except requests.exceptions.Timeout:
        return "Request timed out."

    except requests.exceptions.ConnectionError:
        return "Internet connection problem."

    except Exception as e:
        return f"Unexpected error: {str(e)}"


@tool
def get_air_quality(city: str) -> str:
    """Get current air quality information."""

    try:
        coordinates = get_coordinates(city)

        if coordinates is None:
            return f"Could not find city: {city}"

        lat, lon = coordinates

        air_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={lat}"
            f"&longitude={lon}"
            f"&current=us_aqi,pm2_5,pm10"
        )

        response = requests.get(air_url, timeout=10)

        if response.status_code != 200:
            return "Air quality service is unavailable."

        data = response.json()

        if "current" not in data:
            return "Air quality data not available."

        current = data["current"]

        aqi = current["us_aqi"]
        pm25 = current["pm2_5"]
        pm10 = current["pm10"]

        return (
            f"Air Quality in {city}\n\n"
            f"AQI: {aqi} \n"
            f"PM2.5: {pm25} µg/m³\n"
            f"PM10: {pm10} µg/m³"
        )

    except requests.exceptions.Timeout:
        return "Request timed out."

    except requests.exceptions.ConnectionError:
        return "Internet connection problem."

    except Exception as e:
        return f"Unexpected error: {str(e)}"
    

agent = create_agent(
    model=llm,
    tools=[get_weather,get_air_quality],
    system_prompt="You are a Weather Assistant. give detailed discription for the query in a friendly manner, and a one time answer"
)

st.title("Weather AI Agent")

question = st.text_input("Ask anything about weather")

if st.button("Ask"):

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
    )

    st.write(response["messages"][-1].content)
