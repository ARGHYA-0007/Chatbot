import csv
import os
from typing import Literal, Optional, TypedDict,Annotated
from langchain_core.messages import SystemMessage,HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END,START
from langgraph.types import interrupt, Command
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages, BaseMessage
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition


llm = ChatOllama(model='qwen2.5:7b')
memory = MemorySaver()
config = {
    "configurable": {
        "thread_id": "user1"
    }
}
import requests
from langchain_core.tools import tool



import requests

from langchain_core.tools import tool


# ============================================================
# 1. WEATHER
# ============================================================

@tool
def get_weather(city: str):
    """
    Get the current weather of a city.
    Returns temperature, humidity, wind speed and weather condition.
    """

    # Find city coordinates
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"

    geo_params = {
        "name": city,
        "count": 1,
        "language": "en"
    }

    geo_response = requests.get(
        geo_url,
        params=geo_params,
        timeout=10
    )

    geo_data = geo_response.json()

    if "results" not in geo_data:
        return f"City '{city}' was not found."

    location = geo_data["results"][0]

    latitude = location["latitude"]
    longitude = location["longitude"]

    # Get weather
    weather_url = "https://api.open-meteo.com/v1/forecast"

    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "cloud_cover,"
            "wind_speed_10m,"
            "wind_direction_10m"
        )
    }

    response = requests.get(
        weather_url,
        params=weather_params,
        timeout=10
    )

    data = response.json()
    current = data["current"]

    return {
        "city": location["name"],
        "country": location["country"],
        "temperature_c": current["temperature_2m"],
        "feels_like_c": current["apparent_temperature"],
        "humidity_percent": current["relative_humidity_2m"],
        "precipitation_mm": current["precipitation"],
        "rain_mm": current["rain"],
        "cloud_cover_percent": current["cloud_cover"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "wind_direction": current["wind_direction_10m"],
        "weather_code": current["weather_code"]
    }


# ============================================================
# 2. DICTIONARY
# ============================================================

@tool
def dictionary(word: str):
    """
    Get the definition, pronunciation and examples of an English word.
    """

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    response = requests.get(
        url,
        timeout=10
    )

    if response.status_code != 200:
        return f"Could not find the word '{word}'."

    data = response.json()

    result = data[0]

    meanings = []

    for meaning in result.get("meanings", []):

        part_of_speech = meaning.get("partOfSpeech")

        for definition in meaning.get("definitions", []):

            meanings.append({
                "part_of_speech": part_of_speech,
                "definition": definition.get("definition"),
                "example": definition.get("example")
            })

    return {
        "word": word,
        "phonetic": result.get("phonetic"),
        "meanings": meanings
    }


# ============================================================
# 3. COUNTRY INFORMATION
# ============================================================

@tool
def country_info(country: str):
    """
    Get information about a country such as capital,
    population, region, currency and languages.
    """

    url = f"https://restcountries.com/v3.1/name/{country}"

    response = requests.get(
        url,
        timeout=10
    )

    if response.status_code != 200:
        return f"Could not find country '{country}'."

    data = response.json()

    country_data = data[0]

    currencies = country_data.get("currencies", {})

    currency_names = []

    for code, currency in currencies.items():
        currency_names.append({
            "code": code,
            "name": currency.get("name"),
            "symbol": currency.get("symbol")
        })

    languages = list(
        country_data.get("languages", {}).values()
    )

    return {
        "country": country_data.get("name", {}).get("common"),
        "official_name": country_data.get("name", {}).get("official"),
        "capital": country_data.get("capital"),
        "population": country_data.get("population"),
        "region": country_data.get("region"),
        "subregion": country_data.get("subregion"),
        "languages": languages,
        "currencies": currency_names
    }


# ============================================================
# 4. CURRENCY CONVERTER
# ============================================================

@tool
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
):
    """
    Convert an amount from one currency to another.
    Example: 100 USD to INR.
    """

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    url = "https://api.frankfurter.app/latest"

    params = {
        "amount": amount,
        "from": from_currency,
        "to": to_currency
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        return "Currency conversion failed."

    data = response.json()

    return {
        "amount": amount,
        "from": from_currency,
        "to": to_currency,
        "result": data["rates"][to_currency]
    }


# ============================================================
# 5. BOOK SEARCH
# ============================================================

@tool
def search_books(query: str):
    """
    Search for books using Open Library.
    """

    url = "https://openlibrary.org/search.json"

    params = {
        "q": query,
        "limit": 5
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        return "Book search failed."

    data = response.json()

    books = []

    for book in data.get("docs", [])[:5]:

        books.append({
            "title": book.get("title"),
            "author": book.get("author_name", ["Unknown"])[0],
            "first_publish_year": book.get("first_publish_year"),
            "isbn": book.get("isbn", [None])[0]
        })

    return books


# ============================================================
# 6. NEWS
# ============================================================

@tool
def get_news(query: str):
    """
    Search for recent news about a topic.
    Requires a GNews API key stored in the GNEWS_API_KEY
    environment variable.
    """

    import os

    api_key = os.getenv("GNEWS_API_KEY")

    if not api_key:
        return "GNEWS_API_KEY is not configured."

    url = "https://gnews.io/api/v4/search"

    params = {
        "q": query,
        "lang": "en",
        "max": 5,
        "apikey": api_key
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        return "News search failed."

    data = response.json()

    articles = []

    for article in data.get("articles", []):

        articles.append({
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "published_at": article.get("publishedAt"),
            "source": article.get("source", {}).get("name")
        })

    return articles


# ============================================================
# 7. CODE EXECUTION
# ============================================================

@tool
def execute_code(
    source_code: str,
    language_id: int = 71
):
    """
    Execute code using Judge0.
    Default language_id 71 is Python 3.
    
    IMPORTANT:
    Requires a Judge0 API endpoint/key.
    """

    import os

    api_key = os.getenv("JUDGE0_API_KEY")

    if not api_key:
        return "JUDGE0_API_KEY is not configured."

    url = "https://ce.judge0.com/submissions"

    payload = {
        "source_code": source_code,
        "language_id": language_id
    }

    headers = {
        "X-RapidAPI-Key": api_key
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=10
    )

    if response.status_code not in [200, 201]:
        return "Code execution request failed."

    submission = response.json()

    return submission


# ============================================================
# 8. JOKE
# ============================================================

@tool
def get_joke():
    """
    Get a random programming or general joke.
    """

    url = "https://v2.jokeapi.dev/joke/Programming"

    params = {
        "type": "twopart"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        return "Could not get a joke."

    data = response.json()

    if data.get("type") == "twopart":

        return {
            "setup": data.get("setup"),
            "delivery": data.get("delivery")
        }

    return {
        "joke": data.get("joke")
    }


# ============================================================
# ALL TOOLS
# ============================================================

tools = [
    get_weather,
    dictionary,
    country_info,
    convert_currency,
    search_books,
    get_news,
    execute_code,
    get_joke
]
class ChatState(TypedDict):
    messages:Annotated[list[BaseMessage], add_messages]
def chat(state: ChatState):
    result = llm.invoke(state["messages"])

    return {"messages": [result]}
tool_node = ToolNode(tools)
graph = StateGraph(ChatState)
graph.add_node('chat',chat)
graph.add_node("tools", tool_node)
graph.add_edge(START,'chat')
graph.add_conditional_edges(
    "chat",
    tools_condition
)
graph.add_edge(
    "tools",
    "chat"
)

workflow = graph.compile(checkpointer=memory)
# while True:
#     query = input('USER:')
#     result = workflow.invoke({
#     "messages": [HumanMessage(content=query)]},config=config)
#     print('AI',result['messages'][-1].content)
