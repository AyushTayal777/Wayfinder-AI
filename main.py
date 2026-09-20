import os
from typing import TypedDict, Annotated
import operator
import asyncio
import psycopg
import json
import ast
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq
from mcp_client import (
    tavily_mcp_search,
    get_airlines,
    get_airports,
    aviation_mcp_call,
    extract_destination,
    forecast_mcp_search,
    weather_mcp_search
)
from dotenv import load_dotenv
load_dotenv()
import uuid

DATABASE_URL = os.getenv("DATABASE_URL")

# LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b"
)

class TravelState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add]
    user_query:str
    flight_results:str
    hotel_results:str
    itinerary:str
    llm_calls:int
    weather_results:str

FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""


def flight_agent(state:TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query=state["user_query"]
    try:
        airports=asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines=asyncio.run(
            aviation_mcp_call(
                "list_airlines"
            )
        )

        prompt=FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000],
        )

        response=llm.invoke([
            SystemMessage(
                content='You are an expert travel flight planner.'
            ),
            HumanMessage(
                content=prompt
            )
        ])

        flight_data=response.content

    except Exception as e:
        flight_data=f"Flight info unavailable: {str(e)}"

    return {
        "flight_results":flight_data,
        "messages":[
            AIMessage(
                content="Flight recommendations generated"
            )
        ],
        "llm_calls":state.get("llm_calls",0)+1

    }

HOTEL_AGENT_PROMPT = """
You are a hotel expert. Summarize the best hotel options in {city}
from the search results below.

Search results:
{results}

Return markdown with 5-6 hotels, each as:
**Hotel Name** — area, 1-line description, approx price if available.
End with 2 lines of booking advice. No JSON, no URLs dumps.
"""

def hotel_agent(state: TravelState):
    city = extract_destination(state["user_query"])
    raw = asyncio.run(tavily_mcp_search(f"Best hotels in {city}"))

    # MCP returns [{"type": "text", "text": "<json string>"}]
    try:
        text = raw[0]["text"] if isinstance(raw, list) else str(raw)
        data = json.loads(text)
        snippets = "\n\n".join(
            f"{r.get('title','')}\n{r.get('content','')[:600]}"
            for r in data.get("results", [])[:6]
        )
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        snippets = str(raw)[:4000]

    response = llm.invoke([
        SystemMessage(content="You are an expert hotel advisor."),
        HumanMessage(content=HOTEL_AGENT_PROMPT.format(city=city, results=snippets)),
    ])

    return {
        "hotel_results": response.content,
        "messages": [AIMessage(content="Hotels fetched successfully")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }

def weather_agent(state: TravelState):

    city = extract_destination(state["user_query"])

    weather_data = asyncio.run(
        weather_mcp_search(city)
    )

    forecast_data = asyncio.run(
        forecast_mcp_search(city)
    )

    # Extract text from MCP response
    weather_text = weather_data[0]["text"]
    forecast_text = forecast_data[0]["text"]

    # Convert JSON strings into Python dictionaries
    weather_json = json.loads(weather_text)
    forecast_json = json.loads(forecast_text)

    # Format current weather
    current_weather = f"""
**City:** {weather_json["city"]}

**Temperature:** {weather_json["temperature_c"]}°C  
**Feels Like:** {weather_json["feels_like_c"]}°C  
**Humidity:** {weather_json["humidity"]}%  
**Condition:** {weather_json["condition"]}  
**Wind Speed:** {weather_json["wind_speed"]} m/s
"""

    # Format forecast
    forecast_lines = []

    for item in forecast_json["forecast"]:
        forecast_lines.append(
            f"- **{item['datetime']}** — "
            f"{item['temperature']}°C — "
            f"{item['weather']}"
        )

    forecast = "\n".join(forecast_lines)

    return {
        "weather_results": f"""
### Current Weather

{current_weather}

### Forecast

{forecast}
""",
        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ]
    }


def itinerary_agent(state:TravelState):
    prompt=f"""
    Create a travel itinerary for the following:
    User Query: {state['user_query']},
    Flight results: {state['flight_results']},
    Hotel_results:{state['hotel_results']},
    Weather_result:{state['weather_results']}
    """

    response=llm.invoke([
        SystemMessage(
            content="You are a expert travel planner"
        ),
        HumanMessage(
            content=prompt
        )
    ])

    return {
        "itinerary":response.content,
        "messages":[response],
        "llm_calls":state.get("llm_calls",0)+1
    }



graph =StateGraph(TravelState)

graph.add_node("flight_agent",flight_agent)
graph.add_node("hotel_agent",hotel_agent)
graph.add_node("weather_agent",weather_agent)
graph.add_node("itinerary_agent",itinerary_agent)


graph.add_edge(START,"flight_agent")
graph.add_edge("flight_agent","hotel_agent")
graph.add_edge("hotel_agent","weather_agent")
graph.add_edge("weather_agent","itinerary_agent")
graph.add_edge("itinerary_agent",END)

_conn=psycopg.connect(DATABASE_URL,autocommit=True)
checkpointer=PostgresSaver(_conn)
checkpointer.setup()

app=graph.compile(checkpointer=checkpointer) 


if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    user_input = input("Enter travel request: ")

    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
            "weather_results":""
        },
        config=config
    )

    print("\nFINAL RESPONSE:\n")

    for msg in result["messages"]:
        print(msg.content)