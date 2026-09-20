# 🧭 Wayfinder AI

> An intelligent multi-agent AI travel planning system built with LangGraph, LangChain, MCP, Groq, and PostgreSQL.

Wayfinder AI is a multi-agent travel planning system that uses specialized AI agents to research flights, hotels, weather, budgets, and itineraries.

Instead of relying on a single LLM call, Wayfinder AI uses a **supervisor-driven multi-agent workflow** where different agents handle specific parts of the travel planning process.

The system also includes **input guardrails**, **MCP-based external tools**, **human-in-the-loop approval**, and **persistent workflow state** using PostgreSQL.

---

## 🚀 Features

- 🛡️ **Input Guardrails**
  - Validates whether a request is related to travel planning.
  - Blocks unrelated requests before they enter the travel workflow.

- 🧠 **Supervisor Agent**
  - Analyzes the user's travel request.
  - Extracts trip constraints.
  - Dynamically selects the required specialist agents.

- ✈️ **Flight Agent**
  - Retrieves airport and airline information.
  - Generates flight guidance including:
    - Departure and arrival airports
    - Airlines
    - Estimated duration
    - Fare ranges
    - Peak-season warnings
    - Booking advice

- 🏨 **Hotel Agent**
  - Searches for hotels and recommended areas using Tavily MCP.

- 🌤️ **Weather Agent**
  - Retrieves current weather and forecasts for the destination.

- 💰 **Budget Agent**
  - Analyzes trip affordability.
  - Identifies major cost categories.
  - Provides money-saving suggestions.

- 🗺️ **Itinerary Agent**
  - Combines information from the specialist agents.
  - Generates a structured draft itinerary.

- 👤 **Human-in-the-Loop**
  - Pauses the workflow for human approval.
  - Allows the user to approve or provide feedback on the generated itinerary.

- ✅ **Final Response Agent**
  - Produces the final polished travel plan after human review.

- 🔌 **Model Context Protocol (MCP)**
  - Connects AI agents to external tools and services.

- 💾 **PostgreSQL Persistence**
  - Uses LangGraph PostgreSQL checkpointing to persist workflow state.

- ⚡ **Groq LLM**
  - Uses `openai/gpt-oss-120b` through Groq for LLM inference.

---

## 🏗️ Architecture

```text
                         ┌──────────────────┐
                         │       User       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Supervisor    │
                         │ + Input Guardrail│
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              Unrelated                   Travel Request
                    │                           │
                    ▼                           ▼
                  END                  Select Specialist Agents
                                                │
                    ┌───────────────────────────┼────────────────────────┐
                    │                           │                        │
                    ▼                           ▼                        ▼
             ✈️ Flight Agent             🏨 Hotel Agent           🌤️ Weather Agent
                    │                           │                        │
              AviationStack MCP            Tavily MCP              Weather MCP
                    │                           │                        │
                    └───────────────────────────┼────────────────────────┘
                                                │
                                                ▼
                                      💰 Budget Agent
                                                │
                                                ▼
                                      🗺️ Itinerary Agent
                                                │
                                                ▼
                                      👤 Human Approval
                                                │
                                                ▼
                                      ✅ Final Response
                                                │
                                                ▼
                                               END


🧠 Multi-Agent Workflow
1. 🛡️ Input Guardrail

Every request first passes through an input validation guardrail.

"Plan a 5-day trip to Japan"
        ↓
     Allowed
        ↓
Travel Planning Workflow

"Write me a Python program to sort an array"
        ↓
     Rejected
        ↓
       END

2. 🧠 Supervisor Agent

For valid travel requests, the supervisor determines which agents are required and extracts trip constraints.

Example:

User:
"Plan a 5-day trip from Delhi to Japan under ₹1,00,000"

The supervisor may select:

flight_agent
hotel_agent
weather_agent
budget_agent
itinerary_agent

Extracted constraints include:

destination
origin
duration
budget
travel_style
special_preferences

3. 🤖 Specialist Agents

Each selected agent performs a specific task.

✈️ Flight Agent
       ↓
🏨 Hotel Agent
       ↓
🌤️ Weather Agent
       ↓
💰 Budget Agent
       ↓
🗺️ Itinerary Agent

The workflow can dynamically skip specialist agents that are not required.

4. 👤 Human Approval

The itinerary is not immediately finalized.

Draft Itinerary
      ↓
Human Review
      ↓
 ┌────┴────┐
 │         │
Approve   Feedback
 │         │
 ▼         ▼
Final     Revision
Plan      / Processing

This provides a human-in-the-loop layer before producing the final response.

🔌 MCP Integrations

Wayfinder AI uses the Model Context Protocol (MCP) to connect agents with external tools.

🔎 Tavily MCP

Used by the Hotel Agent for travel and hotel research.

🏨 Hotel Agent
       ↓
   Tavily MCP
       ↓
   Web Search

✈️ AviationStack MCP

Used by the Flight Agent for airport and airline information.

✈️ Flight Agent
       ↓
AviationStack MCP
       ↓
Airport / Airline Data

🌤️ Custom Weather MCP

Used by the Weather Agent for current weather and forecasts.

🌤️ Weather Agent
       ↓
Custom Weather MCP
       ↓
Current Weather + Forecast

🛠️ Tech Stack
Technology	                      Purpose
🐍 Python	             Core programming language
🕸️ LangGraph	          Multi-agent workflow orchestration
🔗 LangChain	         LLM and tool integration
⚡ Groq	                LLM inference
🤖 openai/gpt-oss-120b	 Language model
🔌 MCP	                 External tool integration
🔎 Tavily	             Web search
✈️ AviationStack	     Flight, airport, and airline data
🌤️ Custom Weather MCP	  Weather information
🐘 PostgreSQL	         Persistent workflow state
🐘 Psycopg	             PostgreSQL connection
🎨 Streamlit	         User interface
🔐 python-dotenv	     Environment configuration


📁 Project Structure
Wayfinder AI/
│
├── agents.py
├── graph.py
├── main.py
├── state.py
├── config.py
├── mcp_client.py
├── custom_weather_mcp_server.py
│
├── frontend
│
├── aviationstack-mcp/
│   └── ...
│
├── .env
├── requirements.txt
└── README.md

📄 Important Files

agents.py
Contains the supervisor, flight, hotel, weather, budget, itinerary, human approval, and final response agents.

graph.py
Defines the LangGraph workflow and conditional routing.

state.py
Defines the shared TravelState.

mcp_client.py
Manages MCP connections and tool calls.

config.py
Handles environment variables, API keys, database configuration, and LLM initialization.

🔄 State Management

Agents communicate through a shared TravelState.

The state contains information such as:

user_query
selected_agents
trip_constraints

flight_results
hotel_results
weather_results
budget_results

itinerary
approval_request

approved
human_feedback

final_response
llm_calls
messages

This allows information produced by one agent to be consumed by later agents.

For example:

✈️ Flight Agent
       ↓
flight_results
       ↓
🗺️ Itinerary Agent

And:

🌤️ Weather Agent
       ↓
weather_results
       ↓
💰 Budget / Itinerary Agent
🗄️ PostgreSQL Checkpointing

Wayfinder AI uses LangGraph's PostgreSQL checkpointer to persist workflow state.

This is particularly useful because the workflow contains a human approval interrupt.

The workflow can pause at:

🗺️ Itinerary Agent
       ↓
👤 Human Approval

and later resume using the persisted state.

⚙️ Installation
1. Clone the Repository

git clone <your-repository-url>
cd "Wayfinder AI"

2. Create a Virtual Environment
python -m venv venv

Activate it on Windows:

.\venv\Scripts\Activate.ps1

3. Install Dependencies

pip install -r requirements.txt

🔑 Environment Variables

Create a .env file:

GROQ_API_KEY=your_groq_api_key

TAVILY_API_KEY=your_tavily_api_key

AVIATIONSTACK_API_KEY=your_aviationstack_api_key

WEATHER_API_KEY=your_weather_api_key

DATABASE_URL=your_postgresql_connection_string

⚠️ Never commit your .env file to GitHub.

Add it to .gitignore:

.env
venv/
__pycache__/
*.pyc

▶️ Running the Application

Start the Streamlit frontend:

streamlit run frontend/app.py

The application will open in your browser.

💬 Example Queries
✈️ Complete Trip Planning
Plan a 7-day trip from Delhi to Japan with a budget of ₹1,50,000.
✈️ Flight-Focused Request
Find flight options from Delhi to Dubai.
🏨 Hotel-Focused Request
Plan a trip to Paris and suggest good areas and hotels to stay.
🌤️ Weather-Focused Request
I'm visiting Bali next month. What weather should I expect?
💰 Budget-Focused Request
Can I plan a 5-day trip to Thailand under ₹80,000?

🛡️ Guardrail Example
Write a Python program to reverse a linked list.

Expected behavior:

Request rejected by input guardrail.

The request should not proceed to the travel agents.

🛡️ Guardrails

The input guardrail validates every request before the travel workflow begins.

The guardrail returns:

{
  "allowed": true,
  "reason": ""
}

or:

{
  "allowed": false,
  "reason": "Request is unrelated to travel planning."
}

If allowed is false, the graph routes directly to END.

This prevents unrelated requests from reaching the itinerary generation stage.

👤 Human-in-the-Loop

Wayfinder AI intentionally includes human approval before the final response.

The itinerary agent creates a draft:

🤖 AI-Generated Draft
        ↓
👤 Human Review
        ↓
Approval / Feedback
        ↓
✅ Final Response

This gives the user control over the generated travel plan before the final response is produced.

📊 Why Multi-Agent Architecture?

A single LLM call could generate a travel plan, but it would have to handle every responsibility simultaneously.

Wayfinder AI separates these responsibilities:

🧠 Supervisor
      ↓
🤖 Specialized Agents
      ↓
🔌 Tool-Powered Research
      ↓
🗺️ Integrated Itinerary
      ↓
👤 Human Review
      ↓
✅ Final Response

This makes the workflow easier to extend, debug, and control.

🔮 Future Improvements
✈️ Real-time flight availability and booking
🏨 Real-time hotel availability
💰 Hotel price comparison
📅 Calendar integration
🗺️ Maps and route optimization
💱 Currency conversion
🍽️ Restaurant recommendations
🌍 Multi-city trip planning
🔄 Agent retry and error-handling policies
🛡️ More advanced guardrails
⚡ Streaming agent execution
📊 LLM cost and token monitoring
🔎 Improved search-result summarization
🧠 User preference memory
🐳 Dockerization
☁️ Cloud deployment
📌 Key Concepts Demonstrated

This project demonstrates practical implementation of:

🤖 Multi-agent AI
🕸️ LangGraph
🔗 LangChain
🧠 Agent orchestration
🎯 Supervisor architecture
🔀 Conditional routing
🛡️ Input guardrails
🔌 Model Context Protocol (MCP)
🧰 Tool calling
🌐 External API integration
🔎 Web research
🔄 Shared agent state
👤 Human-in-the-loop workflows
⏸️ LangGraph interrupts
🐘 PostgreSQL checkpointing
⚡ LLM-powered decision making
🎨 Streamlit application development
👨‍💻 Author

Ayush Tayal

Computer Science Engineer

💻 GitHub: AyushTayal777
🔗 LinkedIn: ayush685
🧭 Wayfinder AI

AI-powered multi-agent travel planning system

Built with Python, LangGraph, LangChain, MCP, Groq, PostgreSQL, and Streamlit.