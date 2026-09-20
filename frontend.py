import uuid
from typing import Any

import streamlit as st
from langgraph.types import Command

# --------------------------------------------------------------------------- #
# Page setup
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Wayfinder | AI Trip Planner",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)



@st.cache_resource(show_spinner=False)
def load_graph():
 
    from graph import graph  

    return graph


def initial_state(query: str) -> dict[str, Any]:
    # 2) EDIT ME if TravelState needs more initial keys.
    return {"user_query": query, "messages": [], "llm_calls": 0}


# --------------------------------------------------------------------------- #
# Pipeline definition (the "route" the request flies through)
# --------------------------------------------------------------------------- #
STOPS = [
    ("supervisor", "Supervisor", "🛂"),
    ("flight", "Flights", "✈️"),
    ("hotel", "Stays", "🏨"),
    ("weather", "Weather", "⛅"),
    ("budget", "Budget", "💰"),
    ("itinerary", "Itinerary", "🗺️"),
    ("human", "Your review", "🧑‍✈️"),
    ("final", "Final plan", "🎫"),
]
STOP_KEYS = [s[0] for s in STOPS]
OPTIONAL = {"flight", "hotel", "weather", "budget"}

EXAMPLES = [
    "5 day trip to Tokyo from Delhi in April, mid-range budget, love food and temples",
    "Romantic long weekend in Lisbon for 2, under $1500, slow travel style",
    "10 days in Vietnam, backpacker budget, beaches and street food",
    "Family trip to Dubai for 6 days with two kids, comfortable budget",
]


def classify(node_name: str) -> str | None:
    n = node_name.lower()
    for key in STOP_KEYS:
        if key in n:
            return key
    if "approval" in n:
        return "human"
    return None


# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=DM+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #0e1630;
  --ink-2: #16204a;
  --dusk: #3a2f7d;
  --apricot: #ffb36b;
  --coral: #ff7a6b;
  --lagoon: #35d0c0;
  --sand: #f4ede3;
  --mist: rgba(244,237,227,.68);
  --glass: rgba(255,255,255,.055);
  --glass-line: rgba(255,255,255,.12);
}

html, body, [class*="css"], .stMarkdown, .stTextArea textarea, .stButton button {
  font-family: 'DM Sans', system-ui, sans-serif;
}

.stApp {
  background:
    radial-gradient(1100px 520px at 88% -8%, rgba(255,122,107,.28), transparent 60%),
    radial-gradient(900px 520px at 6% 4%, rgba(58,47,125,.75), transparent 62%),
    linear-gradient(180deg, var(--ink) 0%, #0a1024 100%);
  color: var(--sand);
}

header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; max-width: 1180px; }

h1, h2, h3, h4 { font-family: 'Bricolage Grotesque', sans-serif !important; color: var(--sand); letter-spacing: -0.02em; }
p, li, label, span { color: inherit; }

/* Hero */
.hero { padding: 1.2rem 0 .4rem 0; }
.hero-title {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-weight: 800;
  font-size: clamp(2.6rem, 6vw, 4.6rem);
  line-height: .98;
  letter-spacing: -0.035em;
  margin: 0;
  background: linear-gradient(100deg, #fff 8%, var(--apricot) 52%, var(--coral) 92%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { font-size: 1.12rem; color: var(--mist); max-width: 40rem; margin-top: .9rem; }

/* Route pipeline */
.route { display: flex; align-items: flex-start; margin: 1.6rem 0 1.2rem 0; padding: 1.1rem 1rem 1rem 1rem;
  background: var(--glass); border: 1px solid var(--glass-line); border-radius: 22px; backdrop-filter: blur(6px); overflow-x: auto; }
.stop { flex: 1; min-width: 92px; text-align: center; position: relative; }
.stop::before { content: ""; position: absolute; top: 21px; left: -50%; width: 100%; height: 2px;
  background: repeating-linear-gradient(90deg, rgba(255,255,255,.22) 0 6px, transparent 6px 12px); z-index: 0; }
.stop:first-child::before { display: none; }
.stop.done::before { background: linear-gradient(90deg, var(--lagoon), var(--lagoon)); }
.stop.running::before { background: linear-gradient(90deg, var(--lagoon), var(--apricot)); }
.dot { position: relative; z-index: 1; width: 44px; height: 44px; margin: 0 auto; border-radius: 50%;
  display: grid; place-items: center; font-size: 1.15rem; background: var(--ink-2); border: 2px solid rgba(255,255,255,.18); }
.stop.done .dot { background: rgba(53,208,192,.18); border-color: var(--lagoon); }
.stop.running .dot { border-color: var(--apricot); background: rgba(255,179,107,.18); animation: pulse 1.4s ease-in-out infinite; }
.stop.skipped .dot { opacity: .35; filter: grayscale(1); }
.stop.skipped .name { opacity: .4; text-decoration: line-through; }
.name { margin-top: .5rem; font-size: .8rem; font-weight: 600; color: var(--mist); }
.stop.done .name, .stop.running .name { color: var(--sand); }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(255,179,107,.5);} 50% { box-shadow: 0 0 0 10px rgba(255,179,107,0);} }
@media (prefers-reduced-motion: reduce) { .stop.running .dot { animation: none; } }

/* Trip chips */
.chips { display: flex; flex-wrap: wrap; gap: .55rem; margin: .4rem 0 1rem 0; }
.chip { padding: .42rem .9rem; border-radius: 999px; border: 1px solid var(--glass-line); background: var(--glass); font-size: .9rem; }
.chip b { color: var(--apricot); font-weight: 600; margin-right: .35rem; }

/* Boarding-pass card */
.pass { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 1rem; padding: 1.3rem 1.6rem;
  border-radius: 24px; background: linear-gradient(120deg, rgba(58,47,125,.85), rgba(255,122,107,.55));
  border: 1px solid var(--glass-line); margin: .4rem 0 1.2rem 0; }
.pass .city { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: clamp(1.6rem, 3.6vw, 2.5rem); letter-spacing: -0.02em; }
.pass .tag { font-size: .85rem; color: var(--mist); }
.pass .mid { font-size: 1.8rem; text-align: center; }
.pass .right { text-align: right; }

/* Cards / tabs / inputs */
.card { padding: 1.2rem 1.4rem; border-radius: 20px; background: var(--glass); border: 1px solid var(--glass-line); }
.stTabs [data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid var(--glass-line); }
.stTabs [data-baseweb="tab"] { border-radius: 12px 12px 0 0; padding: .55rem 1rem; color: var(--mist); }
.stTabs [aria-selected="true"] { color: var(--apricot) !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--apricot) !important; }

.stTextArea textarea {
  background: rgba(255,255,255,.06) !important; color: var(--sand) !important;
  border: 1px solid var(--glass-line) !important; border-radius: 16px !important; font-size: 1.02rem;
}
.stTextArea textarea:focus { border-color: var(--apricot) !important; box-shadow: 0 0 0 3px rgba(255,179,107,.25) !important; }

.stButton > button, .stDownloadButton > button {
  border-radius: 14px; border: 1px solid var(--glass-line); background: var(--glass); color: var(--sand);
  padding: .6rem 1.1rem; font-weight: 600; transition: transform .12s ease, border-color .12s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--apricot); transform: translateY(-1px); color: #fff; }
.stButton > button:focus-visible { outline: 3px solid var(--apricot); }
.stButton > button[kind="primary"] {
  background: linear-gradient(100deg, var(--apricot), var(--coral)); color: #2a1208; border: none; font-weight: 700;
}
.stButton > button[kind="primary"]:hover { color: #2a1208; filter: brightness(1.06); }

[data-testid="stSidebar"] { background: rgba(10,16,36,.85); border-right: 1px solid var(--glass-line); }
[data-testid="stMetric"] { background: var(--glass); border: 1px solid var(--glass-line); border-radius: 16px; padding: .7rem .9rem; }
[data-testid="stMetricValue"] { color: var(--apricot); font-family: 'Bricolage Grotesque', sans-serif; }
[data-testid="stExpander"] { background: var(--glass); border: 1px solid var(--glass-line); border-radius: 16px; }
.stAlert { border-radius: 16px; }
hr { border-color: var(--glass-line); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
def reset_session():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.stage = "input"  # input | approval | done
    st.session_state.data = {}
    st.session_state.status = {k: "pending" for k in STOP_KEYS}
    st.session_state.query = ""
    st.session_state.llm_calls = 0
    st.session_state.error = None


if "stage" not in st.session_state:
    reset_session()

if "prefill" not in st.session_state:
    st.session_state.prefill = ""


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #
def route_html(status: dict[str, str]) -> str:
    parts = []
    for key, label, icon in STOPS:
        parts.append(
            f'<div class="stop {status[key]}"><div class="dot">{icon}</div><div class="name">{label}</div></div>'
        )
    return f'<div class="route">{"".join(parts)}</div>'


def chips_html(constraints: dict[str, Any]) -> str:
    labels = {
        "duration": "Duration",
        "budget": "Budget",
        "travel_style": "Style",
    }
    chips = []
    for k, label in labels.items():
        v = constraints.get(k)
        if v:
            chips.append(f'<span class="chip"><b>{label}</b>{v}</span>')
    prefs = constraints.get("special_preferences") or []
    for p in prefs:
        chips.append(f'<span class="chip">{p}</span>')
    return f'<div class="chips">{"".join(chips)}</div>' if chips else ""


def boarding_pass(constraints: dict[str, Any]) -> str:
    origin = constraints.get("origin") or "Home"
    dest = constraints.get("destination") or "Somewhere new"
    return f"""
    <div class="pass">
      <div><div class="tag">From</div><div class="city">{origin}</div></div>
      <div class="mid">✈️</div>
      <div class="right"><div class="tag">To</div><div class="city">{dest}</div></div>
    </div>
    """


def merge_update(update: dict[str, Any] | None):
    if not update:
        return
    for k, v in update.items():
        if k == "messages":
            continue
        if k == "llm_calls":
            st.session_state.llm_calls = max(st.session_state.llm_calls, v)
        st.session_state.data[k] = v


def advance_status(node: str, update: dict[str, Any] | None):
    status = st.session_state.status
    key = classify(node)
    if key:
        status[key] = "done"

    if key == "supervisor" and update:
        selected = [classify(a) for a in (update.get("selected_agents") or [])]
        blocked = not selected
        for opt in OPTIONAL:
            if opt not in selected:
                status[opt] = "skipped"
        if blocked:
            for k in STOP_KEYS:
                if k != "supervisor":
                    status[k] = "skipped"
            return

    # mark the next pending stop as running
    for k in STOP_KEYS:
        if status[k] == "pending":
            status[k] = "running"
            break


# --------------------------------------------------------------------------- #
# Run / resume the graph
# --------------------------------------------------------------------------- #
def stream_graph(payload, route_slot):
    graph = load_graph()
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if st.session_state.status["supervisor"] == "pending":
        st.session_state.status["supervisor"] = "running"
    route_slot.markdown(route_html(st.session_state.status), unsafe_allow_html=True)

    for chunk in graph.stream(payload, config, stream_mode="updates"):
        for node, update in chunk.items():
            if node == "__interrupt__":
                continue
            merge_update(update if isinstance(update, dict) else None)
            advance_status(node, update if isinstance(update, dict) else None)
            route_slot.markdown(route_html(st.session_state.status), unsafe_allow_html=True)

    snapshot = graph.get_state(config)
    if snapshot.next:  # paused on interrupt -> waiting for the human
        st.session_state.status["human"] = "running"
        st.session_state.stage = "approval"
    else:
        st.session_state.stage = "done"
        for k in STOP_KEYS:
            if st.session_state.status[k] in ("running", "pending"):
                st.session_state.status[k] = "done" if st.session_state.data.get("final_response") else "skipped"


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### 🧭 WayFinder AI")
    st.caption("A team of AI agents plans your trip. You approve before it's final.")
    st.divider()
    st.markdown("**Try one of these**")
    for i, ex in enumerate(EXAMPLES):
        if st.button(ex, key=f"ex{i}", use_container_width=True, disabled=st.session_state.stage != "input"):
            st.session_state.prefill = ex
            st.rerun()
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("LLM calls", st.session_state.llm_calls)
    agents_used = sum(1 for k in OPTIONAL | {"itinerary"} if st.session_state.status.get(k) == "done")
    c2.metric("Agents run", agents_used)
    if st.button("Start a new trip", use_container_width=True):
        reset_session()
        st.session_state.prefill = ""
        st.rerun()


# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
st.markdown(
    """
    <div class="hero">
      <h1 class="hero-title">Where to next?</h1>
      <p class="hero-sub">Describe your trip in a sentence. Flight, stay, weather and budget agents work on it together, then hand you a plan to approve.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

route_slot = st.empty()
route_slot.markdown(route_html(st.session_state.status), unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Stage: input
# --------------------------------------------------------------------------- #
if st.session_state.stage == "input":
    query = st.text_area(
        "Your trip",
        value=st.session_state.prefill,
        placeholder="e.g. 5 days in Tokyo from Delhi in April, mid-range budget, love food and temples",
        height=110,
        label_visibility="collapsed",
    )
    go = st.button("Plan my trip", type="primary")

    if go:
        if not query.strip():
            st.warning("Add a destination or a few details about your trip to get started.")
        else:
            st.session_state.query = query.strip()
            st.session_state.error = None
            try:
                with st.spinner("Agents are on it…"):
                    stream_graph(initial_state(st.session_state.query), route_slot)
            except Exception as e:  # noqa: BLE001
                st.session_state.error = str(e)
                st.session_state.stage = "input"
                st.session_state.status = {k: "pending" for k in STOP_KEYS}
            st.rerun()

    if st.session_state.error:
        st.error(f"Something went wrong while planning: {st.session_state.error}")

# --------------------------------------------------------------------------- #
# Results (shown during approval and after)
# --------------------------------------------------------------------------- #
data = st.session_state.data
if st.session_state.stage in ("approval", "done") and data:
    constraints = data.get("trip_constraints") or {}
    blocked = st.session_state.stage == "done" and not data.get("selected_agents") and data.get("final_response")

    if blocked:
        st.warning(data["final_response"])
        st.caption("Try a request about a trip, for example a destination, dates or budget.")
    else:
        if constraints:
            st.markdown(boarding_pass(constraints), unsafe_allow_html=True)
            st.markdown(chips_html(constraints), unsafe_allow_html=True)

        # Approval panel
        if st.session_state.stage == "approval":
            st.markdown("### Review your draft plan")
            st.info("Read through the draft below. Approve it to get the final plan, or tell the agents what to change.")
            with st.container(border=True):
                st.markdown(data.get("itinerary", "_No itinerary generated._"))

            feedback = st.text_area(
                "Feedback (optional)",
                placeholder="e.g. Add a day trip to Nikko, cut the budget by 15%, fewer museums",
                height=90,
                key="feedback_box",
            )
            b1, b2, _ = st.columns([1, 1.2, 3])
            approve = b1.button("Approve plan", type="primary", use_container_width=True)
            revise = b2.button("Request changes", use_container_width=True)

            if approve or revise:
                if revise and not feedback.strip():
                    st.warning("Tell the agents what to change, then request changes.")
                else:
                    payload = Command(resume={"approved": bool(approve), "feedback": feedback.strip()})
                    st.session_state.status["human"] = "done"
                    try:
                        with st.spinner("Polishing your final plan…"):
                            stream_graph(payload, route_slot)
                    except Exception as e:  # noqa: BLE001
                        st.session_state.error = str(e)
                    st.rerun()

        # Final plan
        if st.session_state.stage == "done" and data.get("final_response"):
            st.success("Your trip plan is ready.")
            st.markdown("### Final plan")
            with st.container(border=True):
                st.markdown(data["final_response"])
            st.download_button(
                "Download plan (.md)",
                data=data["final_response"],
                file_name="trip_plan.md",
                mime="text/markdown",
            )
            st.markdown("---")

        # Agent outputs
        st.markdown("### What each agent found")
        tabs = st.tabs(["Flights", "Stays", "Weather", "Budget", "Supervisor notes"])

        with tabs[0]:
            if data.get("flight_results"):
                st.markdown(data["flight_results"])
            else:
                st.caption("The flight agent wasn't needed for this request.")
        with tabs[1]:
            if data.get("hotel_results"):
                with st.expander("Search results", expanded=True):
                    st.markdown(data["hotel_results"])
            else:
                st.caption("The hotel agent wasn't needed for this request.")
        with tabs[2]:
            if data.get("weather_results"):
                st.markdown(data["weather_results"])
            else:
                st.caption("The weather agent wasn't needed for this request.")
        with tabs[3]:
            if data.get("budget_results"):
                st.markdown(data["budget_results"])
            else:
                st.caption("The budget agent wasn't needed for this request.")
        with tabs[4]:
            st.markdown(data.get("supervisor_reasoning") or "_No notes._")
            st.markdown("**Agents selected**")
            st.write(", ".join(data.get("selected_agents") or []) or "None")

    if st.session_state.error and st.session_state.stage != "input":
        st.error(f"Something went wrong: {st.session_state.error}")