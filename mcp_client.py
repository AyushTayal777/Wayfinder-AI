import os

import asyncio

from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY= os.getenv("AVIATIONSTACK_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

client= MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
        "aviationstack":{
            "transport":"stdio",
            "command": r"C:\New folder (2)\VoyageCrew AI\aviationstack-mcp\.venv\Scripts\python.exe",
            "args": [
                "-m",
                "aviationstack_mcp",
                "mcp",
                "run"
            ],
            "env": {
                "AVIATIONSTACK_API_KEY": AVIATIONSTACK_API_KEY
            }
        
        },
        "weather": {
            "transport": "stdio",
            "command": r"C:\New folder (2)\VoyageCrew AI\venv\Scripts\python.exe",
            "args": [
                r"C:\New folder (2)\VoyageCrew AI\custom_weather_mcp_server.py"
            ],
            "env": {
                "OPENWEATHER_API_KEY": WEATHER_API_KEY
            }
        }


    }
)

# tool discovery

# async def main():
#     tools= await client.get_tools()
#     print("Available MCP Tools:")
#     for tool in tools:
#         print(tool.name)

search_tool = None

async def initialize_mcp():
    global search_tool
    global aviation_tools
    if search_tool is not None and aviation_tools:
        return

    tools= await client.get_tools()
    print("\nAvailable MCP Tools:")

    for tool in tools:
        print(tool.name)

    search_tool = next(
            tool
            for tool in tools
            if tool.name=="tavily_search"
        )

    aviation_tools = {
        tool.name:tool
        for tool in tools
        if tool.name !="tavily_search"
    }



async def tavily_mcp_search(query:str):
    await initialize_mcp()
    result = await search_tool.ainvoke(
        {
            "query":query
        }
    )
    return result

async def aviation_mcp_call(
        tool_name:str,
        tool_args:dict =None
):
    tools= await client.get_tools()

    tool=next(
        t for t in tools
        if t.name==tool_name
    )

    result=await tool.ainvoke(
        tool_args or {}
    )
    return result

async def get_airports():
    await initialize_mcp()
    tool= aviation_tools.get("list_airports")

    if not tool:
        return "Airport tool unavailable"

    result = await tool.ainvoke({})

    return result

async def get_airlines():
    await initialize_mcp()
    tool=aviation_tools.get("list_airlines")

    if not tool:
        return "Airline tool unavailable"

    result = tool.ainvoke({})
    return result

weather_tool = None
forecast_tool = None


async def initialize_weather_tools():

    global weather_tool, forecast_tool

    if weather_tool is not None:
        return

    tools = await client.get_tools()

    weather_tool = next(
        t for t in tools
        if t.name == "current_weather"
    )

    forecast_tool = next(
        t for t in tools
        if t.name == "get_forecast"
    )


async def weather_mcp_search(city: str):

    await initialize_weather_tools()

    return await weather_tool.ainvoke(
        {
            "city": city
        }
    )


async def forecast_mcp_search(city: str):

    await initialize_weather_tools()

    return await forecast_tool.ainvoke(
        {
            "city": city
        }
    )

from langchain_groq import ChatGroq

# LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b"
)

###################################
# Destination Extractor
###################################

def extract_destination(query: str):

    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    return response.content.strip()


# if __name__ == "__main__":
#     asyncio.run(main())